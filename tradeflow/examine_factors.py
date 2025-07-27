#!/usr/bin/env python3
"""
Examine Exiobase extension/factor data to understand factor structure
"""

import pandas as pd
import pymrio
from pathlib import Path

def examine_exiobase_factors():
    """
    Load Exiobase data and examine the extension/factor structure
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
    
    print(f"\nExiobase model structure:")
    print(f"Available extensions: {list(exio_model.__dict__.keys())}")
    
    # Check for satellite/extension data
    for attr_name in ['satellite', 'impacts', 'air_emissions', 'employment', 'energy', 'land', 'material', 'water']:
        if hasattr(exio_model, attr_name):
            ext = getattr(exio_model, attr_name)
            print(f"\n{attr_name.upper()} extension found:")
            if hasattr(ext, 'F'):
                F_matrix = ext.F
                print(f"  F matrix shape: {F_matrix.shape}")
                print(f"  F matrix index (factors): {len(F_matrix.index)} factors")
                print(f"  Factor names (first 10):")
                for i, factor in enumerate(F_matrix.index[:10]):
                    print(f"    {i+1}. {factor}")
                
                # Try to find units or metadata
                if hasattr(ext, 'unit'):
                    print(f"  Units available: {ext.unit}")
                
                # Look for stressor information (factor details)
                if hasattr(F_matrix, 'index'):
                    stressors = F_matrix.index.tolist()
                    print(f"  Total stressors/factors: {len(stressors)}")
    
    return exio_model

if __name__ == "__main__":
    examine_exiobase_factors()