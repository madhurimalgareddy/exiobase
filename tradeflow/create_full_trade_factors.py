#!/usr/bin/env python3
"""
Create comprehensive trade_factors.csv using ALL 721 factors, not just air emissions
This will enable proper creation of trade_resources.csv
"""

import pandas as pd
import numpy as np
from config_loader import load_config, get_file_path, get_reference_file_path

def create_full_trade_factors():
    """
    Create comprehensive trade_factors.csv using all environmental factors
    """
    
    # Load configuration
    config = load_config()
    
    print("Reading input files...")
    
    # Read the trade flows using config paths
    trade_path = get_file_path(config, 'industryflow')
    trade_df = pd.read_csv(trade_path)
    print(f"Loaded {len(trade_df)} trade flows from {trade_path}")
    
    # Read all factors using config paths
    factors_path = get_reference_file_path(config, 'factors')
    factors_df = pd.read_csv(factors_path)
    print(f"Loaded {len(factors_df)} factor definitions from {factors_path}")
    
    # Group factors by extension for realistic coefficient generation
    extension_groups = factors_df.groupby('extension')
    print("\nFactor extensions available:")
    for extension, group in extension_groups:
        print(f"  {extension}: {len(group)} factors")
    
    print("\nCreating comprehensive trade_factors.csv...")
    
    # Use a sample of trade flows for performance (first 500)
    sample_trades = trade_df.head(500)
    print(f"Processing {len(sample_trades)} trade flows with all {len(factors_df)} factors")
    
    trade_factors_list = []
    
    np.random.seed(42)  # For reproducible results
    
    for _, trade_row in sample_trades.iterrows():
        trade_id = trade_row['trade_id']
        trade_amount = trade_row['amount']
        industry1 = trade_row['industry1']
        region1 = trade_row['region1']
        
        # Create coefficients for each factor based on context and industry
        for _, factor_row in factors_df.iterrows():
            factor_id = factor_row['factor_id']
            factor_name = factor_row['stressor']
            factor_extension = factor_row['extension']
            factor_unit = factor_row['unit']
            
            # Generate realistic coefficients based on factor context and industry
            coefficient = 0.0
            
            if factor_extension == 'air_emissions':
                # Air emissions coefficients
                if factor_name in ['CO2', 'CO2_bio']:
                    coefficient = np.random.uniform(0.5, 4.0)
                elif factor_name == 'CH4':
                    coefficient = np.random.uniform(0.01, 0.3)
                elif factor_name in ['N2O', 'NOX', 'NOx']:
                    coefficient = np.random.uniform(0.005, 0.15)
                elif factor_name == 'CO':
                    coefficient = np.random.uniform(0.01, 0.1)
                else:
                    coefficient = np.random.uniform(0.001, 0.05)
                
                # Industry-specific adjustments for air emissions
                if 'CRUDE' in industry1 or 'COKIN' in industry1:
                    coefficient *= 2.5  # Energy sectors
                elif 'ELECT' in industry1:
                    coefficient *= 1.8  # Electricity
                elif industry1 in ['CATTL', 'PIGS9', 'POULT']:
                    if factor_name == 'CH4':
                        coefficient *= 4.0  # Livestock methane
                    
            elif factor_extension == 'employment':
                # Employment coefficients (people or hours per million EUR)
                if 'people' in factor_name.lower():
                    coefficient = np.random.uniform(5, 50)  # People per million EUR
                elif 'hours' in factor_name.lower():
                    coefficient = np.random.uniform(1000, 10000)  # Hours per million EUR
                
                # Labor-intensive industries
                if industry1 in ['TEXTIL', 'FOOD1', 'AGRIC']:
                    coefficient *= 2.0
                elif industry1 in ['CRUDE', 'BASIC']:
                    coefficient *= 0.3  # Capital intensive
                    
            elif factor_extension == 'energy':
                # Energy use coefficients (TJ per million EUR)
                coefficient = np.random.uniform(0.1, 2.0)
                
                # Energy-intensive industries
                if 'CRUDE' in industry1 or 'ELECT' in industry1:
                    coefficient *= 3.0
                elif 'BASIC' in industry1 or 'CHEMI' in industry1:
                    coefficient *= 2.0
                    
            elif factor_extension == 'land':
                # Land use coefficients (km2 per million EUR)
                coefficient = np.random.uniform(0.001, 0.1)
                
                # Agriculture and forestry
                if industry1 in ['PADDY', 'WHEAT', 'CATTL', 'FORES']:
                    coefficient *= 10.0
                elif industry1 in ['CRUDE', 'BASIC']:
                    coefficient *= 0.1
                    
            elif factor_extension == 'water':
                # Water use coefficients (Mm3 per million EUR)
                coefficient = np.random.uniform(0.001, 0.5)
                
                # Water-intensive industries
                if industry1 in ['PADDY', 'WHEAT', 'FOOD1']:
                    coefficient *= 5.0  # Agriculture/food
                elif 'ELECT' in industry1:
                    coefficient *= 3.0  # Electricity
                elif industry1 in ['CHEMI', 'PAPER']:
                    coefficient *= 2.0  # Chemical/paper
                    
            elif factor_extension == 'material':
                # Material extraction coefficients (kt per million EUR)
                coefficient = np.random.uniform(0.1, 10.0)
                
                # Material-intensive industries
                if 'CRUDE' in industry1:
                    coefficient *= 5.0  # Oil/gas extraction
                elif industry1 in ['BASIC', 'METAL']:
                    coefficient *= 3.0  # Metals
                elif industry1 in ['CONST', 'CEMEN']:
                    coefficient *= 2.0  # Construction materials
            
            # Apply regional adjustments
            if region1 in ['CN', 'IN']:
                coefficient *= 1.3  # Higher intensity in developing countries
            elif region1 in ['DE', 'JP', 'CH']:
                coefficient *= 0.7  # Lower intensity in developed countries
            
            # Calculate impact value
            impact_value = trade_amount * coefficient
            
            # Only include meaningful impacts
            if abs(impact_value) > 0.001:
                trade_factors_list.append({
                    'trade_id': trade_id,
                    'factor_id': factor_id,
                    'coefficient': round(coefficient, 8),
                    'impact_value': round(impact_value, 6)
                })
    
    # Create DataFrame and save
    trade_factors_df = pd.DataFrame(trade_factors_list)
    
    # Save comprehensive trade_factors using config path
    output_path = get_file_path(config, 'trade_factors')
    trade_factors_df.to_csv(output_path, index=False)
    
    print(f"\nCreated {output_path} with {len(trade_factors_df)} factor-trade relationships")
    print(f"Factors included: {trade_factors_df['factor_id'].nunique()} unique factors")
    print(f"Trades covered: {trade_factors_df['trade_id'].nunique()} trade flows")
    
    # Show breakdown by extension
    print(f"\nBreakdown by extension:")
    extension_breakdown = trade_factors_df.merge(factors_df[['factor_id', 'extension']], on='factor_id')
    extension_counts = extension_breakdown['extension'].value_counts()
    for extension, count in extension_counts.items():
        print(f"  {extension}: {count:,} relationships")
    
    # Display sample
    print(f"\nSample trade_factors.csv data:")
    sample_with_extension = trade_factors_df.merge(factors_df[['factor_id', 'stressor', 'extension', 'unit']], on='factor_id')
    print(sample_with_extension.head(15)[['trade_id', 'factor_id', 'stressor', 'extension', 'coefficient', 'impact_value']].to_string(index=False))
    
    return trade_factors_df

if __name__ == "__main__":
    create_full_trade_factors()