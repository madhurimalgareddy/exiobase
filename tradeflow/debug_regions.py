#!/usr/bin/env python3
"""
Debug script to check available regions in Exiobase data
"""

import pandas as pd
import pymrio
from config_loader import load_config

def check_exiobase_regions():
    """Check what regions are available in Exiobase"""
    print("Loading Exiobase data to check available regions...")
    
    # Load Exiobase data
    exio_data_path = "exiobase_data/IOT_2019_pxp.zip"
    exio_model = pymrio.parse_exiobase3(exio_data_path)
    
    # Get Z matrix regions
    Z = exio_model.Z
    print(f"Z matrix shape: {Z.shape}")
    
    # Check available regions
    regions_from_index = Z.index.get_level_values('region').unique()
    regions_from_columns = Z.columns.get_level_values('region').unique() 
    
    print(f"\nRegions available in Z matrix index: {len(regions_from_index)}")
    print("First 20 regions:", list(regions_from_index[:20]))
    
    print(f"\nRegions available in Z matrix columns: {len(regions_from_columns)}")
    print("First 20 regions:", list(regions_from_columns[:20]))
    
    # Check for India and US specifically
    india_variations = ['IN', 'IND', 'India', 'INDIA']
    us_variations = ['US', 'USA', 'United States', 'US_']
    
    print("\n=== Checking for India ===")
    for variant in india_variations:
        if variant in regions_from_index:
            print(f"✅ Found India as: '{variant}'")
            
            # Check domestic flows for this region
            domestic_flows = Z.loc[(variant,), (variant,)]
            non_zero_domestic = (domestic_flows > 0).sum().sum()
            print(f"   Non-zero domestic flows: {non_zero_domestic}")
            if non_zero_domestic > 0:
                print(f"   Domestic flow range: {domestic_flows[domestic_flows > 0].min().min():.6f} to {domestic_flows.max().max():.2f}")
        else:
            print(f"❌ Not found as: '{variant}'")
    
    print("\n=== Checking for United States ===")
    for variant in us_variations:
        if variant in regions_from_index:
            print(f"✅ Found US as: '{variant}'")
            
            # Check domestic flows for this region
            domestic_flows = Z.loc[(variant,), (variant,)]
            non_zero_domestic = (domestic_flows > 0).sum().sum()
            print(f"   Non-zero domestic flows: {non_zero_domestic}")
            if non_zero_domestic > 0:
                print(f"   Domestic flow range: {domestic_flows[domestic_flows > 0].min().min():.6f} to {domestic_flows.max().max():.2f}")
        else:
            print(f"❌ Not found as: '{variant}'")
    
    # Show all regions containing 'IN' or 'US'
    print(f"\n=== All regions containing 'IN' or 'US' ===")
    for region in regions_from_index:
        if 'IN' in str(region).upper() or 'US' in str(region).upper():
            print(f"  {region}")

if __name__ == "__main__":
    check_exiobase_regions()