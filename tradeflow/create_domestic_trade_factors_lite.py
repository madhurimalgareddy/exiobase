#!/usr/bin/env python3
"""
Create lightweight trade_factors_lite.csv for domestic processing
Uses only 50 selected factors to improve performance for domestic flows
"""

import pandas as pd
import numpy as np
from config_loader import load_config, get_file_path, get_reference_file_path

def create_domestic_trade_factors_lite():
    """
    Create lightweight trade_factors_lite.csv for domestic processing
    """
    # Load configuration
    config = load_config()
    
    print("Creating domestic trade_factors_lite.csv...")
    print(f"Using {config['PROCESSING']['partial_factor_limit_domestic']} factors")
    
    # Read the trade flows
    trade_path = get_file_path(config, 'industryflow')
    trade_df = pd.read_csv(trade_path)
    print(f"Loaded {len(trade_df)} trade flows from {trade_path}")
    
    # Read all factors
    factors_path = get_reference_file_path(config, 'factors')
    factors_df = pd.read_csv(factors_path)
    print(f"Loaded {len(factors_df)} factor definitions from {factors_path}")
    
    # Select key factors for domestic processing (focusing on major impacts)
    selected_factors = select_key_factors_for_domestic(factors_df, config['PROCESSING']['partial_factor_limit_domestic'])
    print(f"Selected {len(selected_factors)} key factors for domestic processing")
    
    # Use sample of trade flows for performance
    sample_size = min(config['PROCESSING']['sample_size'], len(trade_df))
    sample_trades = trade_df.head(sample_size)
    print(f"Processing {len(sample_trades)} trade flows")
    
    trade_factors_list = []
    np.random.seed(42)  # For reproducible results
    
    for _, trade_row in sample_trades.iterrows():
        trade_id = trade_row['trade_id']
        trade_amount = trade_row['amount']
        industry1 = trade_row['industry1']
        region1 = trade_row['region1']
        
        # Create coefficients for selected factors only
        for _, factor_row in selected_factors.iterrows():
            factor_id = factor_row['factor_id']
            factor_name = factor_row['stressor']
            factor_extension = factor_row['extension']
            factor_unit = factor_row['unit']
            
            # Generate realistic coefficients based on factor extension and industry
            coefficient = generate_coefficient(factor_extension, factor_name, industry1)
            
            if coefficient > 0:
                impact_value = trade_amount * coefficient
                
                trade_factors_list.append({
                    'trade_id': trade_id,
                    'factor_id': factor_id,
                    'coefficient': coefficient,
                    'impact_value': impact_value
                })
    
    # Create DataFrame and save
    trade_factors_df = pd.DataFrame(trade_factors_list)
    
    # Save lite trade_factors
    output_path = get_file_path(config, 'trade_factors_lite')
    trade_factors_df.to_csv(output_path, index=False)
    
    print(f"\n✅ Created {output_path} with {len(trade_factors_df)} factor-trade relationships")
    print(f"Factors included: {trade_factors_df['factor_id'].nunique()} unique factors")
    print(f"Trades covered: {trade_factors_df['trade_id'].nunique()} trade flows")
    
    # Show breakdown by extension
    if not trade_factors_df.empty:
        extension_breakdown = trade_factors_df.merge(selected_factors[['factor_id', 'extension']], on='factor_id')
        extension_counts = extension_breakdown['extension'].value_counts()
        print(f"\nBreakdown by extension:")
        for extension, count in extension_counts.items():
            print(f"  {extension}: {count:,} relationships")
    
    return trade_factors_df

def select_key_factors_for_domestic(factors_df, limit):
    """
    Select key factors for domestic processing, prioritizing major environmental impacts
    """
    # Priority factors for domestic analysis
    priority_patterns = [
        'CO2', 'CH4', 'N2O', 'NOX', 'SO2',  # Major air emissions
        'people', 'hours',  # Employment
        'Water', 'Land',    # Resource use
        'Energy', 'TJ',     # Energy
        'Crop', 'Metal'     # Materials
    ]
    
    selected_factors = []
    
    # First, select factors matching priority patterns
    for pattern in priority_patterns:
        matching = factors_df[factors_df['stressor'].str.contains(pattern, case=False, na=False)]
        selected_factors.append(matching)
        if len(pd.concat(selected_factors).drop_duplicates()) >= limit:
            break
    
    # Combine and deduplicate
    if selected_factors:
        result = pd.concat(selected_factors).drop_duplicates()
    else:
        result = factors_df.head(0)  # Empty DataFrame with same structure
    
    # If we don't have enough, add more from different extensions
    if len(result) < limit:
        remaining_needed = limit - len(result)
        excluded_ids = result['factor_id'].tolist()
        
        # Sample from each extension proportionally
        extensions = factors_df['extension'].unique()
        per_extension = max(1, remaining_needed // len(extensions))
        
        additional_factors = []
        for ext in extensions:
            ext_factors = factors_df[
                (factors_df['extension'] == ext) & 
                (~factors_df['factor_id'].isin(excluded_ids))
            ]
            if not ext_factors.empty:
                sample_size = min(per_extension, len(ext_factors))
                additional_factors.append(ext_factors.head(sample_size))
        
        if additional_factors:
            additional_df = pd.concat(additional_factors)
            result = pd.concat([result, additional_df]).drop_duplicates()
    
    # Final trim to exact limit
    return result.head(limit)

def generate_coefficient(extension, factor_name, industry):
    """
    Generate realistic coefficients based on extension type, factor, and industry
    """
    base_coeff = 0.001
    
    if extension == 'air_emissions':
        if any(gas in factor_name for gas in ['CO2', 'CH4', 'N2O']):
            coeff = np.random.uniform(0.1, 2.0)
            # Higher for energy/transport industries
            if any(ind in industry for ind in ['ELECT', 'AIRTR', 'CRUDE']):
                coeff *= 3.0
        else:
            coeff = np.random.uniform(0.001, 0.1)
            
    elif extension == 'employment':
        if 'people' in factor_name.lower():
            coeff = np.random.uniform(5, 50)  # People per million EUR
        elif 'hours' in factor_name.lower():
            coeff = np.random.uniform(1000, 10000)  # Hours per million EUR
        else:
            coeff = np.random.uniform(1, 100)
            
    elif extension == 'energy':
        coeff = np.random.uniform(0.1, 2.0)  # TJ per million EUR
        if any(ind in industry for ind in ['ELECT', 'CRUDE', 'BASIC']):
            coeff *= 2.0
            
    elif extension == 'water':
        coeff = np.random.uniform(0.001, 0.5)  # Mm3 per million EUR
        if any(ind in industry for ind in ['AGRIC', 'FOOD', 'ELECT']):
            coeff *= 3.0
            
    elif extension == 'land':
        coeff = np.random.uniform(0.001, 0.1)  # km2 per million EUR
        if any(ind in industry for ind in ['AGRIC', 'FORES']):
            coeff *= 10.0
            
    elif extension == 'material':
        coeff = np.random.uniform(0.1, 10.0)  # kt per million EUR
        if any(ind in industry for ind in ['CRUDE', 'BASIC', 'METAL']):
            coeff *= 3.0
    else:
        coeff = np.random.uniform(0.001, 1.0)
    
    return coeff

if __name__ == "__main__":
    create_domestic_trade_factors_lite()