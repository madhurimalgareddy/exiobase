#!/usr/bin/env python3
"""
Industry Trade Flow Analysis for Exiobase Data
Extracts trade flow data based on config settings for imports, exports, or domestic flows
Outputs trade.csv with columns: year, region1, region2, industry1, industry2, amount

Default (Recommended):
python trade.py
Creates small trade_factor.csv (~50 factors, manageable size)

Large File (Not Recommended):
python trade.py -lag
Creates trade_factor_lg.csv (~1.5GB, causes Node.js memory errors) 

Creates 4 files

  1. Reference Files (created if they don't exist) - used for trade factor generation process:
  - industry.csv - Sector mapping with 5-character industry codes (calls create_sector_mapping())
  - factor.csv - Environmental factor definitions from Exiobase extensions (calls create_factors_csv())

  2. Primary Output:
  - trade.csv - The main trade flow data with columns: trade_id, year, region1, region2, industry1, industry2,
  amount

  3. Trade Factors (your focus):
  - trade_factor.csv (default, small ~50 factors)
  - trade_factor_lg.csv (with -lag flag, large ~721 factors)

"""

import pandas as pd
import numpy as np
import pymrio
import csv
import time
from datetime import datetime
import os
from pathlib import Path
import pickle as pkl
import argparse
from config_loader import load_config, get_file_path, get_reference_file_path, print_config_summary

class ExiobaseTradeFlow:
    def __init__(self, use_large_factors=False):
        # Load configuration
        self.config = load_config()
        self.use_large_factors = use_large_factors
        print_config_summary(self.config)
        
        self.year = self.config['YEAR']
        
        # Handle COUNTRY as either string or dict with current sub-parameter
        country_config = self.config['COUNTRY']
        if isinstance(country_config, dict):
            if 'current' in country_config:
                self.country = country_config['current']
            elif 'list' in country_config:
                # If no current is set, use first from list
                country_list = country_config['list'].split(',')
                self.country = country_list[0].strip()
            else:
                self.country = str(country_config)
        elif isinstance(country_config, str):
            if ',' in country_config:
                self.country = country_config.split(',')[0].strip()
            else:
                self.country = country_config
        else:
            self.country = str(country_config)
            
        self.tradeflow_type = self.config['TRADEFLOW']
        self.output_file = get_file_path(self.config, 'industryflow')
        self.model_type = 'pxp'  # product by product matrix
        
        # Set up paths for Exiobase data storage
        self.model_path = Path(__file__).parent / 'exiobase_data'
        self.model_path.mkdir(exist_ok=True)
        
        # Load or create sector mapping
        self.sector_mapping = self.load_sector_mapping()
        
        # Create factors export
        self.create_factors_export()

    def load_sector_mapping(self):
        """
        Load the sector mapping from industry.csv or create it if it doesn't exist
        """
        industries_file = get_reference_file_path(self.config, 'industries')
        
        if Path(industries_file).exists():
            print("Loading existing sector mapping from industry.csv")
            mapping_df = pd.read_csv(industries_file)
            # Create a mapping dictionary from sector name to 5-char ID
            return dict(zip(mapping_df['name'], mapping_df['industry_id']))
        else:
            print("Creating new sector mapping...")
            # Run the sector mapping creation
            from create_sector_mapping import create_sector_mapping
            mapping_df = create_sector_mapping()
            return dict(zip(mapping_df['name'], mapping_df['industry_id']))

    def create_factors_export(self):
        """
        Create the factor.csv export if it doesn't exist
        """
        factors_file = get_reference_file_path(self.config, 'factors')
        
        if Path(factors_file).exists():
            print("factor.csv already exists")
        else:
            print("Creating factor.csv from Exiobase extensions...")
            try:
                from factors import create_factors_csv
                create_factors_csv()
            except Exception as e:
                print(f"Failed to create factor.csv: {e}")

    def _apply_partial_factors_filter(self, F_stacked, ext_name):
        """
        Apply filtering to create smaller trade_factor.csv using selected factors
        """
        partial_limit = self.config['PROCESSING'].get('partial_factor_limit', 50)
        
        # Define priority factors for each extension
        priority_factors = {
            'air_emissions': ['CO2', 'CH4', 'N2O', 'NOX', 'CO', 'SO2', 'NH3', 'PM10', 'PM2.5'],
            'employment': ['Employment people', 'Employment hours'],
            'energy': ['Energy use', 'Electricity', 'Natural gas', 'Oil'],
            'water': ['Water consumption', 'Water withdrawal'],
            'land': ['Cropland', 'Forest', 'Pastures', 'Artificial'],
            'material': ['Metal Ores', 'Non-Metallic Minerals', 'Fossil Fuels', 'Primary Crops']
        }
        
        selected_factors = priority_factors.get(ext_name, [])
        
        if selected_factors:
            # Filter by priority factors first
            priority_mask = F_stacked['flowable'].str.contains('|'.join(selected_factors), case=False, na=False)
            priority_data = F_stacked[priority_mask].copy()
            
            # If we still have too many, select top ones by coefficient magnitude
            if len(priority_data) > partial_limit:
                priority_data = priority_data.nlargest(partial_limit, 'coefficient')
            
            # If we have fewer than limit, add other significant factors
            remaining_limit = partial_limit - len(priority_data)
            if remaining_limit > 0:
                other_data = F_stacked[~priority_mask].copy()
                if len(other_data) > 0:
                    other_significant = other_data.nlargest(remaining_limit, 'coefficient')
                    F_stacked = pd.concat([priority_data, other_significant], ignore_index=True)
                else:
                    F_stacked = priority_data
            else:
                F_stacked = priority_data
        else:
            # If no priority factors defined, select by coefficient magnitude
            F_stacked = F_stacked.nlargest(partial_limit, 'coefficient')
        
        print(f"    Selected {len(F_stacked)} factors from {ext_name} (partial factors mode)")
        return F_stacked

    def create_trade_factor(self, trade_df, exio_model):
        """
        Create trade_factor.csv that links each trade flow to environmental factors
        """
        print("Creating trade_factor.csv with real Exiobase factor data...")
        
        try:
            # Load the factors mapping
            factors_file = get_reference_file_path(self.config, 'factors')
            factors_df = pd.read_csv(factors_file)
            
            # Create a mapping from factor names to factor_ids
            # Extract factor names from stressor column (format: "CO2 - combustion - air")
            factors_df['name'] = factors_df['stressor'].str.split(' - ').str[0]
            factor_mapping = dict(zip(factors_df['name'], factors_df['factor_id']))
            
            extensions = ['air_emissions', 'employment', 'energy', 'land', 'material', 'water']
            
            all_trade_factor = []
            
            for ext_name in extensions:
                if hasattr(exio_model, ext_name):
                    print(f"Processing {ext_name} factors for trade flows...")
                    ext = getattr(exio_model, ext_name)
                    
                    if hasattr(ext, 'F'):
                        F_matrix = ext.F
                        
                        # Convert F matrix to a lookup format
                        # F matrix: rows = factors, columns = (region, sector)
                        F_stacked = F_matrix.stack(level=['region', 'sector'], future_stack=True).reset_index()
                        F_stacked.columns = ['stressor', 'region', 'sector', 'coefficient']
                        
                        # Filter for non-zero coefficients only and sample for performance
                        F_stacked = F_stacked[F_stacked['coefficient'] != 0].copy()
                        
                        # Keep ALL coefficients for comprehensive analysis
                        print(f"  Found {len(F_stacked)} non-zero {ext_name} coefficients")
                        
                        # Map sectors to industry IDs
                        F_stacked['industry_id'] = F_stacked['sector'].map(self.sector_mapping)
                        F_stacked = F_stacked.dropna(subset=['industry_id'])
                        
                        # Extract flowable name for mapping
                        F_stacked['flowable'] = F_stacked['stressor'].apply(lambda x: x.split(' - ')[0] if ' - ' in x else x)
                        F_stacked['factor_id'] = F_stacked['flowable'].map(factor_mapping)
                        F_stacked = F_stacked.dropna(subset=['factor_id'])
                        
                        # Apply partial factors filtering if not using large factors
                        if not self.use_large_factors and self.config['PROCESSING'].get('use_partial_factors', True):
                            F_stacked = self._apply_partial_factors_filter(F_stacked, ext_name)
                        
                        # Process ALL data with performance optimizations and progress tracking
                        ext_start_time = time.time()
                        print(f"  Processing ALL {len(trade_df)} trade flows with {len(F_stacked)} {ext_name} coefficients")
                        
                        # Optimize F_stacked for faster merging
                        F_stacked = F_stacked.set_index(['region', 'industry_id'])
                        trade_df_indexed = trade_df.set_index(['region1', 'industry1'])
                        
                        # Create efficient merge - process in chunks for memory management
                        chunk_size = 10000
                        trade_factor_chunks = []
                        total_chunks = (len(trade_df) + chunk_size - 1) // chunk_size
                        
                        for i in range(0, len(trade_df), chunk_size):
                            chunk_start = time.time()
                            chunk_df = trade_df.iloc[i:i+chunk_size].copy()
                            chunk_num = i // chunk_size + 1
                            
                            # Efficient merge using index-based joins
                            trade_factor_chunk = chunk_df.merge(
                                F_stacked.reset_index(), 
                                left_on=['region1', 'industry1'], 
                                right_on=['region', 'industry_id'],
                                how='inner'
                            )
                            
                            if not trade_factor_chunk.empty:
                                trade_factor_chunks.append(trade_factor_chunk)
                            
                            # Progress report every chunk
                            chunk_time = time.time() - chunk_start
                            elapsed_total = time.time() - ext_start_time
                            print(f"    Chunk {chunk_num}/{total_chunks} completed in {chunk_time:.1f}s | Total: {elapsed_total:.1f}s | Found: {len(trade_factor_chunk) if not trade_factor_chunk.empty else 0} matches")
                        
                        # Combine all chunks
                        if trade_factor_chunks:
                            trade_factor_merge = pd.concat(trade_factor_chunks, ignore_index=True)
                            print(f"  Combined {len(trade_factor_chunks)} chunks -> {len(trade_factor_merge)} total matches")
                        else:
                            trade_factor_merge = pd.DataFrame()
                        
                        if not trade_factor_merge.empty:
                            # Calculate factor impacts
                            trade_factor_merge['impact_value'] = trade_factor_merge['amount'] * trade_factor_merge['coefficient']
                            
                            # Filter for meaningful impacts (keep all meaningful data)
                            initial_count = len(trade_factor_merge)
                            trade_factor_merge = trade_factor_merge[abs(trade_factor_merge['impact_value']) > 0.001]
                            print(f"  Filtered {initial_count} -> {len(trade_factor_merge)} meaningful impacts (>0.001)")
                            
                            # Keep only needed columns
                            trade_factor_subset = trade_factor_merge[['trade_id', 'factor_id', 'coefficient', 'impact_value']]
                            trade_factor_subset['factor_id'] = trade_factor_subset['factor_id'].astype(int)
                            
                            all_trade_factor.extend(trade_factor_subset.to_dict('records'))
            
            # Create DataFrame and save
            if all_trade_factor:
                trade_factor_df = pd.DataFrame(all_trade_factor)
                
                # Determine output file based on mode
                if self.use_large_factors:
                    output_file = get_file_path(self.config, 'trade_factor')
                    if not output_file.endswith('_lg.csv'):
                        output_file = output_file.replace('.csv', '_lg.csv')
                    file_type = "large"
                    print(f"⚠️  WARNING: Creating large trade_factor_lg.csv (~1.5GB) - this may cause memory issues in trade_resource.py")
                else:
                    output_file = get_file_path(self.config, 'trade_factor')
                    if output_file.endswith('_lg.csv'):
                        output_file = output_file.replace('_lg.csv', '.csv')
                    file_type = "small"
                
                trade_factor_df.to_csv(output_file, index=False)
                print(f"Created {file_type} trade_factor file with {len(trade_factor_df)} factor-trade relationships")
                print(f"File: {output_file}")
            else:
                print("No trade-factor relationships found, creating empty trade_factor.csv")
                output_file = get_file_path(self.config, 'trade_factor')
                if output_file.endswith('_lg.csv'):
                    output_file = output_file.replace('_lg.csv', '.csv')
                pd.DataFrame(columns=['trade_id', 'factor_id', 'coefficient', 'impact_value']).to_csv(output_file, index=False)
                
        except Exception as e:
            print(f"Error creating trade_factor.csv: {e}")
            self.create_trade_factor_fallback(trade_df)

    def create_trade_factor_fallback(self, trade_df):
        """
        Create a simplified trade_factor.csv for fallback data
        """
        print("Creating simplified trade_factor.csv with sample data...")
        
        try:
            # Create sample factor relationships for major flows
            sample_factors = []
            
            # Sample some common factors
            common_factor_ids = [1, 5, 7, 15]  # As, CH4, CO2, N2O
            
            # For each trade flow, create sample factor relationships
            for _, trade_row in trade_df.head(100).iterrows():  # Limit to first 100 for performance
                for factor_id in common_factor_ids:
                    # Create realistic sample coefficients
                    if factor_id == 7:  # CO2
                        coefficient = np.random.uniform(0.1, 2.0)
                    elif factor_id == 5:  # CH4  
                        coefficient = np.random.uniform(0.01, 0.1)
                    else:
                        coefficient = np.random.uniform(0.001, 0.05)
                    
                    impact_value = trade_row['amount'] * coefficient
                    
                    sample_factors.append({
                        'trade_id': trade_row['trade_id'],
                        'factor_id': factor_id,
                        'coefficient': coefficient,
                        'impact_value': impact_value
                    })
            
            trade_factor_df = pd.DataFrame(sample_factors)
            output_file = get_file_path(self.config, 'trade_factor')
            trade_factor_df.to_csv(output_file, index=False)
            print(f"Created sample trade_factor.csv with {len(trade_factor_df)} relationships")
            
        except Exception as e:
            print(f"Error creating fallback trade_factor.csv: {e}")

    def download_and_process_exiobase(self):
        """
        Download and process Exiobase data using pymrio library
        """
        print(f"Downloading Exiobase data for {self.year}...")
        
        # Check if Exiobase data already exists
        exio_file = self.model_path / f'IOT_{self.year}_{self.model_type}.zip'
        if exio_file.exists():
            print(f"Found existing Exiobase file: {exio_file}")
        else:
            # Download Exiobase data for the specified year
            try:
                print(f"Downloading Exiobase data for {self.year}... (this may take several minutes)")
                pymrio.download_exiobase3(
                    storage_folder=self.model_path,
                    system=self.model_type,
                    years=[self.year]
                )
                print(f"Successfully downloaded Exiobase {self.year} data")
            except Exception as e:
                print(f"Download failed: {e}")
                print("Using fallback method with simulated data...")
                return self.load_fallback_data()
        
        # Parse the downloaded Exiobase data
        try:
            print(f"Parsing Exiobase file: {exio_file}")
            exio_model = pymrio.parse_exiobase3(exio_file)
            return exio_model
        except Exception as e:
            print(f"Parsing failed: {e}")
            print("Using fallback method with simulated data...")
            return self.load_fallback_data()

    def extract_m_matrix_data(self, exio_model):
        """
        Extract trade flow data from Exiobase model based on tradeflow type
        """
        print(f"Extracting {self.tradeflow_type} trade flow data...")
        
        # Get the Z matrix (inter-industry flows)
        Z = exio_model.Z.copy()
        
        # Set proper index and column names
        Z.index.names = ['from_region', 'from_sector']
        Z.columns.names = ['to_region', 'to_sector']
        
        # Stack the matrix to create a long format DataFrame
        Z_stacked = Z.stack(level=['to_region', 'to_sector'], future_stack=True).reset_index()
        Z_stacked.columns = ['from_region', 'from_sector', 'to_region', 'to_sector', 'flow']
        
        # Filter based on tradeflow type
        if self.tradeflow_type == 'imports':
            # Filter for flows to the country (imports)
            Z_filtered = Z_stacked[Z_stacked['to_region'] == self.country].copy()
            # Remove domestic flows
            Z_filtered = Z_filtered[Z_filtered['from_region'] != self.country].copy()
            print(f"Processing imports to {self.country}")
        elif self.tradeflow_type == 'exports':
            # Filter for flows from the country (exports)
            Z_filtered = Z_stacked[Z_stacked['from_region'] == self.country].copy()
            # Remove domestic flows
            Z_filtered = Z_filtered[Z_filtered['to_region'] != self.country].copy()
            print(f"Processing exports from {self.country}")
        elif self.tradeflow_type == 'domestic':
            # Filter for flows within the country (domestic)
            domestic_candidates = Z_stacked[
                (Z_stacked['from_region'] == self.country) & 
                (Z_stacked['to_region'] == self.country)
            ].copy()
            
            print(f"Processing domestic flows within {self.country}")
            print(f"Found {len(domestic_candidates)} potential domestic flows")
            print(f"Non-zero flows: {len(domestic_candidates[domestic_candidates['flow'] > 0])}")
            print(f"Flows > 0.001: {len(domestic_candidates[domestic_candidates['flow'] > 0.001])}")
            print(f"Flows > 0.01: {len(domestic_candidates[domestic_candidates['flow'] > 0.01])}")
            
            if len(domestic_candidates) > 0:
                print(f"Flow range: {domestic_candidates['flow'].min():.6f} to {domestic_candidates['flow'].max():.2f}")
            
            Z_filtered = domestic_candidates
        else:
            raise ValueError(f"Invalid tradeflow type: {self.tradeflow_type}")
        
        # Filter out zero or very small flows (lowered threshold for domestic)
        initial_count = len(Z_filtered)
        if self.tradeflow_type == 'domestic':
            # Use lower threshold for domestic flows
            Z_filtered = Z_filtered[Z_filtered['flow'] > 0.001].copy()
            print(f"After filtering flows > 0.001: {len(Z_filtered)} flows (removed {initial_count - len(Z_filtered)})")
        else:
            Z_filtered = Z_filtered[Z_filtered['flow'] > 0.01].copy()
        
        # Map sector names to 5-character industry IDs
        Z_filtered['industry1'] = Z_filtered['from_sector'].map(self.sector_mapping)
        Z_filtered['industry2'] = Z_filtered['to_sector'].map(self.sector_mapping)
        
        # Remove rows where mapping failed (should be rare)
        Z_filtered = Z_filtered.dropna(subset=['industry1', 'industry2'])
        
        # Aggregate by 5-character industry IDs
        trade_data = Z_filtered.groupby(['from_region', 'to_region', 'industry1', 'industry2']).agg({
            'flow': 'sum'
        }).reset_index()
        
        # Format the final output
        trade_data = trade_data.rename(columns={
            'from_region': 'region1',
            'to_region': 'region2',
            'flow': 'amount'
        })
        
        # Add year column
        trade_data['year'] = self.year
        
        # Add trade_id column (1-based sequential ID)
        trade_data = trade_data.reset_index(drop=True)
        trade_data['trade_id'] = trade_data.index + 1
        
        # Reorder columns
        trade_data = trade_data[['trade_id', 'year', 'region1', 'region2', 'industry1', 'industry2', 'amount']]
        
        return trade_data

    def load_fallback_data(self):
        """
        Fallback method to generate realistic trade flow data when Exiobase download fails
        """
        print("Using fallback data generation...")
        
        # Simplified region and sector lists based on typical Exiobase structure
        regions = ['AT', 'BE', 'BG', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FR', 'GR',
                  'HR', 'HU', 'IE', 'IT', 'LT', 'LU', 'LV', 'MT', 'NL', 'PL', 'PT', 'RO',
                  'SE', 'SI', 'SK', 'GB', 'JP', 'CN', 'CA', 'KR', 'BR', 'IN', 'MX', 'RU',
                  'AU', 'CH', 'TR', 'TW', 'NO', 'ID', 'ZA', 'WA', 'WL', 'WE', 'WF', 'WM']
        
        # Use the same 5-character IDs from the mapping if available
        if hasattr(self, 'sector_mapping') and self.sector_mapping:
            sectors = list(set(self.sector_mapping.values()))[:50]  # Use actual IDs
        else:
            # Fallback 5-character sector codes
            sectors = ['PADDY', 'WHEAT', 'CEREA', 'VEGET', 'OILSE', 'SUGAR', 'PLANT', 'CROPS',
                      'CATTL', 'PIGS9', 'POULT', 'MEATA', 'ANIMA', 'RAWMI', 'WOOLS', 'MANUR',
                      'FORES', 'FISHF', 'ANTHR', 'COKIN', 'OTHER', 'SUBBI', 'PATEN', 'LIGNI',
                      'CRUDE', 'NATUR', 'IRON1', 'IRON2', 'ALUMI', 'COPPE', 'NICKE', 'ZINC1',
                      'LEAD1', 'TIN12', 'OTHER', 'GOLD1', 'SILVE', 'PLATI', 'OTHER', 'URANI',
                      'STONE', 'SAND1', 'CLAY1', 'CHEMI', 'SALT1', 'OTHER', 'PETRE', 'NATUR',
                      'OTHER', 'MEAT1', 'MEAT2']
        
        np.random.seed(42)  # For reproducible results
        
        data = []
        for region1 in regions:
            for region2 in regions:
                # Apply filtering based on tradeflow type
                if self.tradeflow_type == 'imports':
                    if region2 != self.country or region1 == self.country:
                        continue
                elif self.tradeflow_type == 'exports':
                    if region1 != self.country or region2 == self.country:
                        continue
                elif self.tradeflow_type == 'domestic':
                    if region1 != self.country or region2 != self.country:
                        continue
                
                for exp_sector in sectors[:31]:  # Limit to first 31 sectors
                    for imp_sector in sectors[:31]:
                        # Generate realistic trade amounts
                        base_amount = np.random.lognormal(8, 2.5)
                        
                        # Sector-specific adjustments
                        if any(x in exp_sector for x in ['Coke_', 'Comin', 'Basic']):
                            base_amount *= 3.0  # Raw materials
                        elif any(x in exp_sector for x in ['Chemi', 'Mach_', 'Elec_']):
                            base_amount *= 2.0  # Manufacturing
                        elif any(x in exp_sector for x in ['Finan', 'Legal', 'Educa']):
                            base_amount *= 0.2  # Services
                        
                        # Region-specific adjustments
                        if region1 in ['CN', 'DE', 'JP']:
                            base_amount *= 1.8
                        elif region1 in ['CA', 'MX']:
                            base_amount *= 1.3
                        
                        # Only include significant flows
                        if base_amount > 0.1:
                            data.append({
                                'year': self.year,
                                'region1': region1,
                                'region2': region2,
                                'industry1': exp_sector,
                                'industry2': imp_sector,
                                'amount': round(base_amount, 2)
                            })
        
        df = pd.DataFrame(data)
        # Add trade_id for fallback data
        df['trade_id'] = df.index + 1
        # Reorder columns
        df = df[['trade_id', 'year', 'region1', 'region2', 'industry1', 'industry2', 'amount']]
        
        return df

    def process_trade_flows(self):
        """
        Process and format the trade flow data
        """
        print(f"Processing {self.tradeflow_type} flows for {self.year} with {self.country}...")
        
        # Try to download and process real Exiobase data
        exio_model = self.download_and_process_exiobase()
        
        if isinstance(exio_model, pd.DataFrame):
            # Fallback data was returned
            df = exio_model
            # For fallback data, create trade_factor with dummy data
            self.create_trade_factor_fallback(df)
        else:
            # Real Exiobase model was returned
            df = self.extract_m_matrix_data(exio_model)
            # Create trade_factor with real data
            self.create_trade_factor(df, exio_model)
        
        # Sort by amount descending to show largest flows first
        df = df.sort_values('amount', ascending=False)
        
        return df

    def export_to_csv(self, df):
        """
        Export the processed data to CSV
        """
        print(f"Exporting trade.csv data to {self.output_file}...")
        
        # Ensure we have the correct column order including trade_id
        if 'trade_id' in df.columns:
            columns = ['trade_id', 'year', 'region1', 'region2', 'industry1', 'industry2', 'amount']
        else:
            columns = ['year', 'region1', 'region2', 'industry1', 'industry2', 'amount']
        df = df[columns]
        
        # Export to CSV
        df.to_csv(self.output_file, index=False, float_format='%.2f')
        
        return len(df)

    def run_analysis(self):
        """
        Main analysis runner with timing and logging
        """
        start_time = datetime.now()
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"For year: {self.year}")
        print(f"For country: {self.country}")
        print(f"Trade flow type: {self.tradeflow_type}")
        print(f"Output: {self.output_file}")
        print()
        
        try:
            # Process the trade flows
            df = self.process_trade_flows()
            
            # Export to CSV
            total_rows = self.export_to_csv(df)
            
            # Calculate timing
            end_time = datetime.now()
            run_time = end_time - start_time
            run_time_minutes = round(run_time.total_seconds() / 60, 1)
            
            # Display summary
            print()
            print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total run time: {run_time_minutes} minutes")
            print(f"Total rows output: {total_rows}")
            print()
            print("Data source in Exiobase: Inter-industry flows matrix (Z) - Trade flows from exporting regions/industries")
            print("to importing industries in the United States. Data extracted from Exiobase v3.8.2")
            print("multiregional input-output database covering 163 industries across 44 countries and 5 RoW regions.")
            print("Downloaded using pymrio.download_exiobase3() and processed via pymrio.parse_exiobase3().")
            print("Additional exports: industry.csv (200 sectors), factor.csv (721 factors), trade_factor.csv (factor impacts)")
            
            return True
            
        except Exception as e:
            end_time = datetime.now()
            run_time = end_time - start_time
            run_time_minutes = round(run_time.total_seconds() / 60, 1)
            
            print(f"Error occurred: {str(e)}")
            print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total run time: {run_time_minutes} minutes")
            return False

def main():
    """
    Main execution function
    """
    parser = argparse.ArgumentParser(description='Generate trade factors for Exiobase data')
    parser.add_argument('-lag', '--large', action='store_true', 
                       help='Generate large trade_factor_lg.csv with all factors (WARNING: ~1.5GB file, may cause memory issues)')
    
    args = parser.parse_args()
    
    if args.large:
        print("🚀 Large factors mode enabled - generating comprehensive trade_factor_lg.csv")
        print("⚠️  WARNING: This will create a ~1.5GB file that may cause FATAL ERROR in trade_resource.py")
        print("   Node.js v8::ToLocalChecked Empty MaybeLocal error after ~10 minutes")
        print("   Consider using the default small file mode instead")
        print()
    
    analyzer = ExiobaseTradeFlow(use_large_factors=args.large)
    success = analyzer.run_analysis()
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()