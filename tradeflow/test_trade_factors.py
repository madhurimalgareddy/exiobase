#!/usr/bin/env python3
"""
Test script to verify the trade_factors creation with fixed column mapping
"""

import pandas as pd
from config_loader import load_config, get_reference_file_path

def test_factor_mapping():
    """Test if the factor mapping works with the actual column names"""
    
    config = load_config()
    
    # Load the factors file
    factors_file = get_reference_file_path(config, 'factors')
    factors_df = pd.read_csv(factors_file)
    
    print("Factors file columns:", factors_df.columns.tolist())
    print("\nFirst 5 factors:")
    print(factors_df.head())
    
    # Test the fixed column mapping
    factors_df['name'] = factors_df['stressor'].str.split(' - ').str[0]
    factor_mapping = dict(zip(factors_df['name'], factors_df['factor_id']))
    
    print(f"\nCreated factor mapping with {len(factor_mapping)} factors")
    print("Sample mappings:")
    for i, (name, factor_id) in enumerate(list(factor_mapping.items())[:10]):
        print(f"  {name} -> {factor_id}")
    
    # Test different extensions
    extensions = ['air_emissions', 'employment', 'energy', 'land', 'material', 'water']
    for ext in extensions:
        ext_factors = factors_df[factors_df['extension'] == ext]
        print(f"\n{ext}: {len(ext_factors)} factors")
        if len(ext_factors) > 0:
            print(f"  Sample: {ext_factors['name'].iloc[0]} -> {ext_factors['factor_id'].iloc[0]}")

if __name__ == "__main__":
    test_factor_mapping()