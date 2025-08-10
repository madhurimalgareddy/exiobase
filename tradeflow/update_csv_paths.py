#!/usr/bin/env python3
"""
Update all Python scripts to output CSV files to csv/ subfolder
"""

import os
import re
from pathlib import Path

def update_csv_paths():
    """
    Update all Python scripts to read/write CSV files from/to csv/ subfolder
    """
    
    # Create csv directory if it doesn't exist
    csv_dir = Path("csv")
    csv_dir.mkdir(exist_ok=True)
    print(f"Created/verified csv/ directory")
    
    # List of Python files to update
    py_files = [
        'create_factors.py',
        'create_full_trade_factors.py', 
        'create_sector_mapping.py',
        'create_trade_impacts.py',
        'industry_tradeflow.py',
        'regenerate_factors.py',
        'update_trade_files.py'
    ]
    
    # Patterns to find and replace
    replacements = [
        # Direct CSV file references that should go to csv/
        (r"'([a-zA-Z_][a-zA-Z0-9_]*\.csv)'", r"'csv/\1'"),
        (r'"([a-zA-Z_][a-zA-Z0-9_]*\.csv)"', r'"csv/\1"'),
        
        # Path object CSV references
        (r"/ '([a-zA-Z_][a-zA-Z0-9_]*\.csv)'", r"/ 'csv/\1'"),
        (r'/ "([a-zA-Z_][a-zA-Z0-9_]*\.csv)"', r'/ "csv/\1"'),
        
        # to_csv calls with direct filenames
        (r"\.to_csv\('([a-zA-Z_][a-zA-Z0-9_]*\.csv)'", r".to_csv('csv/\1'"),
        (r'\.to_csv\("([a-zA-Z_][a-zA-Z0-9_]*\.csv)"', r'.to_csv("csv/\1"'),
        
        # Variable assignments
        (r"output_file = '([a-zA-Z_][a-zA-Z0-9_]*\.csv)'", r"output_file = 'csv/\1'"),
        (r'output_file = "([a-zA-Z_][a-zA-Z0-9_]*\.csv)"', r'output_file = "csv/\1"'),
        (r"detailed_file = '([a-zA-Z_][a-zA-Z0-9_]*\.csv)'", r"detailed_file = 'csv/\1'"),
        
        # os.path.exists calls
        (r"os\.path\.exists\('([a-zA-Z_][a-zA-Z0-9_]*\.csv)'\)", r"os.path.exists('csv/\1')"),
        (r"os\.remove\('([a-zA-Z_][a-zA-Z0-9_]*\.csv)'\)", r"os.remove('csv/\1')"),
    ]
    
    for py_file in py_files:
        if not os.path.exists(py_file):
            print(f"Skipping {py_file} - file not found")
            continue
            
        print(f"Updating {py_file}...")
        
        # Read the file
        with open(py_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Apply replacements
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Special handling for Path objects in industry_tradeflow.py
        if py_file == 'industry_tradeflow.py':
            content = re.sub(
                r"Path\(__file__\)\.parent / '([a-zA-Z_][a-zA-Z0-9_]*\.csv)'",
                r"Path(__file__).parent / 'csv/\1'",
                content
            )
        
        # Write back if changed
        if content != original_content:
            with open(py_file, 'w') as f:
                f.write(content)
            print(f"  ✓ Updated {py_file}")
        else:
            print(f"  - No changes needed for {py_file}")
    
    print(f"\nAll Python scripts updated to use csv/ subfolder")
    print(f"CSV files should be placed in: {csv_dir.absolute()}")

if __name__ == "__main__":
    update_csv_paths()