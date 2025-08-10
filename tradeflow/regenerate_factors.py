#!/usr/bin/env python3
"""
Regenerate factors.csv with new column structure: factor_id,unit,context,name,fullname
"""

import pandas as pd
from config_loader import load_config, get_reference_file_path

def regenerate_factors():
    """
    Regenerate factors.csv with the new column order and remove flow column
    """
    
    # Load configuration
    config = load_config()
    
    # Read the detailed factors file which has all the data we need
    print("Reading factors_detailed.csv...")
    detailed_file = get_reference_file_path(config, 'factors').replace('.csv', '_detailed.csv')
    detailed_df = pd.read_csv(detailed_file)
    
    # Create the new factors.csv with required columns in correct order
    factors_new = detailed_df[['factor_id', 'unit', 'context', 'name', 'full_stressor_name']].copy()
    
    # Rename the full_stressor_name column to fullname
    factors_new = factors_new.rename(columns={'full_stressor_name': 'fullname'})
    
    # Save the new factors.csv
    output_file = get_reference_file_path(config, 'factors')
    factors_new.to_csv(output_file, index=False)
    
    print(f"Regenerated factors.csv with {len(factors_new)} factors")
    print("New column structure: factor_id, unit, context, name, fullname")
    
    # Display sample
    print("\nFirst 10 factors:")
    print(factors_new.head(10).to_string(index=False))
    
    print("\nLast 10 factors:")
    print(factors_new.tail(10).to_string(index=False))
    
    # Show summary
    print(f"\nSummary:")
    print(f"Total factors: {len(factors_new)}")
    print(f"Contexts: {factors_new['context'].nunique()}")
    print("\nContext breakdown:")
    print(factors_new['context'].value_counts())
    
    # Clean up - remove the detailed file since we don't need it anymore
    import os
    if os.path.exists(detailed_file):
        os.remove(detailed_file)
        print("\nRemoved factors_detailed.csv (no longer needed)")
    
    return factors_new

if __name__ == "__main__":
    regenerate_factors()