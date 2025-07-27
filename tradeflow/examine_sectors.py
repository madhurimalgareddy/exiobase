#!/usr/bin/env python3
"""
Examine Exiobase sector structure to identify 5-character sector IDs
"""

import pandas as pd
import pymrio
from pathlib import Path

def examine_exiobase_sectors():
    """
    Load Exiobase data and examine the sector structure
    """
    model_path = Path(__file__).parent / 'exiobase_data'
    year = 2019
    model_type = 'pxp'
    
    exio_file = model_path / f'IOT_{year}_{model_type}.zip'
    
    if not exio_file.exists():
        print(f"Exiobase file not found: {exio_file}")
        return
    
    print(f"Loading Exiobase data from: {exio_file}")
    exio_model = pymrio.parse_exiobase3(exio_file)
    
    # Get the Z matrix to examine sector structure
    Z = exio_model.Z
    
    print(f"\nZ matrix shape: {Z.shape}")
    print(f"Index levels: {Z.index.names}")
    print(f"Column levels: {Z.columns.names}")
    
    # Examine the sector index structure
    sectors = Z.index.get_level_values('sector').unique()
    print(f"\nTotal number of sectors: {len(sectors)}")
    
    # Look for sectors with 5-character IDs or codes
    sector_data = []
    for sector in sectors:
        sector_str = str(sector)
        # Look for patterns that might be 5-character IDs
        if len(sector_str) >= 5:
            # Check if it starts with a 5-character code (letters/numbers)
            potential_id = sector_str[:5]
            if potential_id.replace('_', '').replace('-', '').isalnum():
                sector_data.append({
                    'potential_id': potential_id,
                    'full_name': sector_str,
                    'length': len(sector_str)
                })
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(sector_data)
    
    print(f"\nSectors with potential 5-character IDs: {len(df)}")
    print("\nFirst 20 sectors:")
    print(df.head(20).to_string(index=False))
    
    # Look for actual sector codes
    print(f"\nAll unique sectors (first 30):")
    for i, sector in enumerate(sectors[:30]):
        print(f"{i+1:2d}. {sector}")
    
    # Check regions too
    regions = Z.index.get_level_values('region').unique()
    print(f"\nRegions ({len(regions)}):")
    for i, region in enumerate(regions):
        print(f"{region}", end="  ")
        if (i + 1) % 10 == 0:
            print()
    
    return sectors, regions

if __name__ == "__main__":
    examine_exiobase_sectors()