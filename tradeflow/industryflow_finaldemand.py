#!/usr/bin/env python3
"""
Extract final demand flows from Exiobase Y matrix for industryflow_finaldemand.csv
Based on the same pattern as industry_tradeflow.py but processes Y matrix instead of Z matrix.

Outputs industryflow_finaldemand.csv with columns: 
flow_id, year, region1, region2, industry1, demand_category, amount, flow_type
"""

import pandas as pd
import pymrio
from pathlib import Path
import time
from config_loader import load_config, get_file_path, get_reference_file_path

class FinalDemandExtractor:
    def __init__(self):
        """Initialize the final demand extractor"""
        self.config = load_config()
        self.year = self.config['YEAR']
        self.country = self.config['COUNTRY']
        self.tradeflow_type = 'imports'  # Focus on imports as requested
        self.model_path = Path(__file__).parent / 'exiobase_data'
        self.model_type = 'pxp'
        self.output_file = get_file_path(self.config, 'industryflow_finaldemand', self.tradeflow_type)
        
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
        """Load Exiobase data following the same pattern as industry_tradeflow.py"""
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

    def extract_y_matrix_data(self, exio_model):
        """
        Extract final demand flow data from Exiobase Y matrix (based on extract_m_matrix_data pattern)
        """
        print(f"Extracting final demand flows for {self.country} imports...")
        
        # Get the Y matrix (final demand flows) - following same pattern as Z matrix
        Y = exio_model.Y.copy()
        
        # Set proper index and column names
        Y.index.names = ['from_region', 'from_sector']
        Y.columns.names = ['to_region', 'demand_category']
        
        # Stack the matrix to create a long format DataFrame (same as Z matrix approach)
        Y_stacked = Y.stack(level=['to_region', 'demand_category'], future_stack=True).reset_index()
        Y_stacked.columns = ['from_region', 'from_sector', 'to_region', 'demand_category', 'flow']
        
        # Filter for imports (flows TO the country from other regions) - same logic as Z matrix
        Y_filtered = Y_stacked[Y_stacked['to_region'] == self.country].copy()
        # Remove domestic flows
        Y_filtered = Y_filtered[Y_filtered['from_region'] != self.country].copy()
        print(f"Processing final demand imports to {self.country}")
        
        # Filter out zero or very small flows (same threshold as Z matrix)
        Y_filtered = Y_filtered[Y_filtered['flow'] > 0.01].copy()
        
        # Map sector names to 5-character industry IDs (same as Z matrix)
        Y_filtered['industry1'] = Y_filtered['from_sector'].map(self.sector_mapping)
        
        # Remove rows where mapping failed
        Y_filtered = Y_filtered.dropna(subset=['industry1'])
        
        # Aggregate by industry and demand category (adapted from Z matrix aggregation)
        final_demand_data = Y_filtered.groupby(['from_region', 'to_region', 'industry1', 'demand_category']).agg({
            'flow': 'sum'
        }).reset_index()
        
        # Format the final output (adapted from Z matrix format)
        final_demand_data = final_demand_data.rename(columns={
            'from_region': 'region1',
            'to_region': 'region2',
            'flow': 'amount'
        })
        
        # Add year column
        final_demand_data['year'] = self.year
        
        # Add flow_id column (1-based sequential ID) - same as trade_id in Z matrix
        final_demand_data = final_demand_data.reset_index(drop=True)
        final_demand_data['flow_id'] = final_demand_data.index + 1
        
        # Add flow type indicator
        final_demand_data['flow_type'] = 'final_demand'
        
        # Reorder columns (adapted from Z matrix column order)
        final_demand_data = final_demand_data[['flow_id', 'year', 'region1', 'region2', 'industry1', 'demand_category', 'amount', 'flow_type']]
        
        return final_demand_data

    def export_to_csv(self, df):
        """Export to CSV (same pattern as industry_tradeflow.py)"""
        print(f"Exporting final demand data to: {self.output_file}")
        
        # Ensure output directory exists
        Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Export to CSV
        df.to_csv(self.output_file, index=False, float_format='%.2f')
        
        print(f"✅ Created {self.output_file} with {len(df)} final demand flow records")
        
        # Display summary (same as industry_tradeflow.py)
        print(f"\nFinal Demand Summary:")
        print(f"Total flows: {len(df)}")
        print(f"Total amount: {df['amount'].sum():.2f} million EUR")
        print(f"Regions: {df['region1'].nunique()} unique")
        print(f"Industries: {df['industry1'].nunique()} unique")
        print(f"Demand categories: {df['demand_category'].nunique()} unique")
        
        print(f"\nDemand category breakdown:")
        print(df['demand_category'].value_counts().head(10))
        
        print(f"\nTop 10 flows:")
        print(df.nlargest(10, 'amount')[['region1', 'industry1', 'demand_category', 'amount']].to_string(index=False))
        
        return len(df)

    def run(self):
        """Main execution method (same pattern as industry_tradeflow.py)"""
        start_time = time.time()
        
        print(f"=== Final Demand Flow Extraction ===")
        print(f"Year: {self.year}")
        print(f"Country: {self.country}")
        print(f"Flow type: Final demand imports")
        print(f"Output: {self.output_file}")
        print()
        
        # Load Exiobase data
        exio_model = self.load_exiobase_data()
        if exio_model is None:
            print("Failed to load Exiobase data")
            return
        
        # Extract Y matrix data
        try:
            df = self.extract_y_matrix_data(exio_model)
            
            if df.empty:
                print("No final demand flow data extracted")
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
    """Main function to run the final demand extraction"""
    extractor = FinalDemandExtractor()
    extractor.run()

if __name__ == "__main__":
    main()