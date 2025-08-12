#!/usr/bin/env python3
"""
Run trade flow analysis for a single country
"""

import sys
import subprocess
from config_loader import load_config, update_config

def main():
    if len(sys.argv) != 3:
        print("Usage: python run_single_country.py <country> <tradeflow>")
        print("Example: python run_single_country.py CN exports")
        sys.exit(1)
    
    country = sys.argv[1]
    tradeflow = sys.argv[2]
    
    print(f"🌍 Processing {country} for {tradeflow}")
    
    # Update config
    update_config({
        'COUNTRY': country,
        'TRADEFLOW': tradeflow
    })
    
    scripts = [
        'trade.py',
        'industryflow_finaldemand.py',
        'industryflow_factor.py', 
        'create_full_trade_factor.py',
        'trade_impact.py',
        'trade_resource.py'
    ]
    
    for script in scripts:
        print(f"\n▶️  Running {script}...")
        try:
            result = subprocess.run([sys.executable, script], 
                                  capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                print(f"✅ {script} completed")
            else:
                print(f"❌ {script} failed: {result.stderr}")
                break
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    print(f"🎯 {country} {tradeflow} processing complete")

if __name__ == "__main__":
    main()