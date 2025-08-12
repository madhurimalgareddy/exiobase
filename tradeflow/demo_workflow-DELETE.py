#!/usr/bin/env python3
"""
Demonstration workflow showing how the config system works
"""

from config_loader import load_config, update_config, print_config_summary, get_file_path
import pandas as pd
import os

def demo_workflow():
    """
    Demonstrate the complete workflow for different trade flow types
    """
    print("=" * 80)
    print("EXIOBASE TRADE FLOW ANALYSIS - CONFIGURATION DEMO")
    print("=" * 80)
    
    # Show current configuration
    config = load_config()
    print("\nCurrent Configuration:")
    print_config_summary(config)
    
    # Demonstrate switching between different trade flow types
    tradeflow_types = ['imports', 'exports', 'domestic']
    
    for tradeflow_type in tradeflow_types:
        print(f"\n{'-' * 60}")
        print(f"DEMONSTRATING {tradeflow_type.upper()} PROCESSING")
        print(f"{'-' * 60}")
        
        # Update configuration
        update_config({'TRADEFLOW': tradeflow_type})
        config = load_config()
        print_config_summary(config)
        
        # Show where files would be created
        files_to_create = [
            'industry_tradeflow',
            'trade_factor', 
            'trade_impacts',
            'trade_resources'
        ]
        
        print(f"\nFiles that would be created for {tradeflow_type}:")
        for file_key in files_to_create:
            file_path = get_file_path(config, file_key)
            print(f"  {file_key}: {file_path}")
            
            # Check if directory exists, create if not
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"    └── Created directory: {directory}")
            else:
                print(f"    └── Directory exists: {directory}")
    
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print("Configuration system successfully demonstrated!")
    print("\nKey features:")
    print("✅ Dynamic configuration switching")
    print("✅ Automatic directory creation")
    print("✅ Separate output folders for imports/exports/domestic")
    print("✅ Shared reference files (industry.csv, factor.csv)")
    print("\nTo run analysis:")
    print("1. Set TRADEFLOW in config.yaml to 'imports', 'exports', or 'domestic'")
    print("2. Run: python industry_tradeflow.py")
    print("3. Run: python trade_impact.py")
    print("4. Run: python create_split_resources.py")
    print("Or use: python run_all_tradeflows.py (processes all types)")

if __name__ == "__main__":
    demo_workflow()