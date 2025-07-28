#!/usr/bin/env python3
"""
Run trade flow analysis for all three types: imports, exports, domestic
Updates config and runs all processing scripts for each type
"""

import subprocess
import sys
from config_loader import load_config, update_config, print_config_summary

def run_script(script_name, tradeflow_type):
    """
    Run a Python script and handle any errors
    """
    print(f"\n{'='*60}")
    print(f"Running {script_name} for {tradeflow_type}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def process_tradeflow_type(tradeflow_type):
    """
    Process all scripts for a specific tradeflow type
    """
    print(f"\n{'#'*80}")
    print(f"PROCESSING {tradeflow_type.upper()} FLOWS")
    print(f"{'#'*80}")
    
    # Update configuration
    update_config({'TRADEFLOW': tradeflow_type})
    config = load_config()
    print_config_summary(config)
    
    # List of scripts to run in order
    scripts = [
        'industry_tradeflow.py',
        'create_trade_impacts.py', 
        'create_split_resources.py'
    ]
    
    success_count = 0
    for script in scripts:
        if run_script(script, tradeflow_type):
            success_count += 1
        else:
            print(f"Failed to run {script} for {tradeflow_type}")
    
    print(f"\nCompleted {success_count}/{len(scripts)} scripts for {tradeflow_type}")
    return success_count == len(scripts)

def main():
    """
    Main execution function
    """
    print("Trade Flow Analysis - All Types")
    print("This script will process imports, exports, and domestic flows")
    
    # Get initial config
    initial_config = load_config()
    print(f"\nInitial configuration:")
    print_config_summary(initial_config)
    
    # Process each tradeflow type
    tradeflow_types = ['imports', 'exports', 'domestic']
    results = {}
    
    for tradeflow_type in tradeflow_types:
        success = process_tradeflow_type(tradeflow_type)
        results[tradeflow_type] = success
    
    # Summary
    print(f"\n{'#'*80}")
    print("FINAL SUMMARY")
    print(f"{'#'*80}")
    
    for tradeflow_type, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"{tradeflow_type.upper():>10}: {status}")
    
    # Restore initial config
    update_config({'TRADEFLOW': initial_config['TRADEFLOW']})
    print(f"\nRestored configuration to: {initial_config['TRADEFLOW']}")
    
    all_success = all(results.values())
    if all_success:
        print("\n✅ All trade flow types processed successfully!")
    else:
        print("\n❌ Some trade flow types failed. Check logs above.")
    
    return all_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)