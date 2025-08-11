#!/usr/bin/env python3
"""
Extract factor input flows from Exiobase F matrices for industryflow_factor.csv
Based on the same pattern as industryflow.py and industryflow_finaldemand.py but processes F matrices.

The F matrices contain environmental and socioeconomic coefficients:
- 721 factors across 6 extensions (air_emissions, employment, energy, land, material, water)
- 8,000 sectors (49 regions × 163 sectors)

Outputs industryflow_factor.csv with columns: 
flow_id, year, region, sector, industry, factor_name, coefficient, flow_type, extension_type
"""

import pandas as pd
import pymrio
from pathlib import Path
import time
from config_loader import load_config, get_file_path, get_reference_file_path

class FactorInputExtractor:
    def __init__(self):
        """Initialize the factor input extractor"""
        self.config = load_config()
        self.year = self.config['YEAR']
        self.country = self.config['COUNTRY']
        self.tradeflow_type = 'imports'  # Focus on US sectors
        self.model_path = Path(__file__).parent / 'exiobase_data'
        self.model_type = 'pxp'
        self.output_file = get_file_path(self.config, 'industryflow_factor', self.tradeflow_type)
        
        # Load sector mapping
        self.sector_mapping = self.load_sector_mapping()
        
    def load_sector_mapping(self):
        """Load the sector mapping from industries.csv"""
        try:
            industries_file = get_reference_file_path(self.config, 'industries')
            if Path(industries_file).exists():
                print("Loading existing sector mapping from industries.csv")
                mapping_df = pd.read_csv(industries_file)
                return dict(zip(mapping_df['name'], mapping_df['industry_id']))
            else:
                print("Industries file not found, creating minimal mapping")
                return {}
        except Exception as e:
            print(f"Error loading sector mapping: {e}")
            return {}

    def load_exiobase_data(self):
        """Load Exiobase data following the same pattern as other scripts"""
        print(f"Loading Exiobase data for {self.year}...")
        
        exio_file = self.model_path / f'IOT_{self.year}_{self.model_type}.zip'
        
        if not exio_file.exists():
            print(f"Exiobase file not found: {exio_file}")
            return None
            
        try:
            print(f"Parsing Exiobase file: {exio_file}")
            exio_model = pymrio.parse_exiobase3(exio_file)
            return exio_model
        except Exception as e:
            print(f"Parsing failed: {e}")
            return None

    def extract_f_matrix_data(self, exio_model):
        """
        Extract factor input flow data from Exiobase F matrices (based on working patterns)
        """
        print(f"Extracting factor input flows for {self.country} sectors...")
        
        # Extensions to process (same as factors.py)
        extensions = ['air_emissions', 'employment', 'energy', 'land', 'material', 'water']
        all_factor_flows = []
        
        for ext_name in extensions:
            if hasattr(exio_model, ext_name):
                print(f"Processing {ext_name} extension...")
                ext = getattr(exio_model, ext_name)
                
                if hasattr(ext, 'F'):
                    # Get the F matrix (factor coefficients) - following same pattern as Z/Y matrices
                    F = ext.F.copy()
                    
                    # Set proper index and column names
                    F.index.names = ['factor_name']
                    F.columns.names = ['region', 'sector']
                    
                    # Stack the matrix to create long format (same as Z/Y matrix approach)
                    F_stacked = F.stack(level=['region', 'sector'], future_stack=True).reset_index()
                    F_stacked.columns = ['factor_name', 'region', 'sector', 'coefficient']
                    
                    # Filter for US sectors (same logic as imports filtering in other scripts)
                    F_filtered = F_stacked[F_stacked['region'] == self.country].copy()
                    print(f"Processing {ext_name} factors for {self.country} sectors")
                    
                    # Filter out zero or very small coefficients (adapted threshold for factors)
                    F_filtered = F_filtered[F_filtered['coefficient'] > 0.0001].copy()
                    
                    # Sample to improve performance (take largest coefficients)
                    sample_size = self.config['PROCESSING']['sample_size']
                    if len(F_filtered) > sample_size:
                        F_filtered = F_filtered.nlargest(sample_size, 'coefficient')
                        print(f"Sampled top {sample_size} {ext_name} factor coefficients")
                    
                    # Map sector names to 5-character industry IDs (same as other scripts)
                    F_filtered['industry'] = F_filtered['sector'].map(self.sector_mapping)
                    
                    # Remove rows where mapping failed
                    F_filtered = F_filtered.dropna(subset=['industry'])
                    
                    # Add extension type
                    F_filtered['extension_type'] = ext_name
                    
                    all_factor_flows.append(F_filtered)
                    print(f"Found {len(F_filtered)} {ext_name} factor flows")
        
        if not all_factor_flows:
            print("No factor flows found")
            return pd.DataFrame()
        
        # Combine all extensions
        combined_flows = pd.concat(all_factor_flows, ignore_index=True)
        
        # Aggregate by industry and factor (adapted from other scripts' aggregation)
        factor_data = combined_flows.groupby(['region', 'industry', 'factor_name', 'extension_type']).agg({
            'coefficient': 'sum',
            'sector': 'first'  # Keep original sector name for reference
        }).reset_index()
        
        # Add year column
        factor_data['year'] = self.year
        
        # Add flow_id column (1-based sequential ID) - same as other scripts
        ## factor_data = factor_data.reset_index(drop=True)
        ## factor_data['flow_id'] = factor_data.index + 1
        
        # Add flow type indicator
        factor_data['flow_type'] = 'factor_input'
        
        # Reorder columns (adapted from other scripts' column order)
        factor_data = factor_data[['factor_id', 'year', 'region', 'sector', 'industry', 'factor_name', 'coefficient', 'flow_type', 'extension_type']]
        
        return factor_data

    def export_to_csv(self, df):
        """Export to CSV (same pattern as other scripts)"""
        print(f"Exporting factor input data to: {self.output_file}")
        
        # Ensure output directory exists
        Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Export to CSV
        df.to_csv(self.output_file, index=False, float_format='%.6f')
        
        print(f"✅ Created {self.output_file} with {len(df)} factor input flow records")
        
        # Display summary (same as other scripts)
        print(f"\nFactor Input Summary:")
        print(f"Total flows: {len(df)}")
        print(f"Average coefficient: {df['coefficient'].mean():.6f}")
        print(f"Industries: {df['industry'].nunique()} unique")
        print(f"Factors: {df['factor_name'].nunique()} unique")
        print(f"Extensions: {df['extension_type'].nunique()} unique")
        
        print(f"\nExtension type breakdown:")
        print(df['extension_type'].value_counts())
        
        print(f"\nTop 10 factor coefficients:")
        print(df.nlargest(10, 'coefficient')[['industry', 'factor_name', 'extension_type', 'coefficient']].to_string(index=False))
        
        return len(df)

    def run(self):
        """Main execution method (same pattern as other scripts)"""
        start_time = time.time()
        
        print(f"=== Factor Input Flow Extraction ===")
        print(f"Year: {self.year}")
        print(f"Country: {self.country}")
        print(f"Flow type: Factor inputs to US sectors")
        print(f"Output: {self.output_file}")
        print()
        
        # Load Exiobase data
        exio_model = self.load_exiobase_data()
        if exio_model is None:
            print("Failed to load Exiobase data")
            return
        
        # Extract F matrix data
        try:
            df = self.extract_f_matrix_data(exio_model)
            
            if df.empty:
                print("No factor input flow data extracted")
                return
            
            # Export to CSV
            total_rows = self.export_to_csv(df)
            
        except Exception as e:
            print(f"Error during extraction: {e}")
            return
        
        # Performance summary
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n=== Extraction Complete ===")
        print(f"Processing time: {duration:.2f} seconds")
        print(f"Records processed: {total_rows}")
        print(f"Output file: {self.output_file}")

def main():
    """Main function to run the factor input extraction"""
    extractor = FactorInputExtractor()
    extractor.run()

if __name__ == "__main__":
    main()