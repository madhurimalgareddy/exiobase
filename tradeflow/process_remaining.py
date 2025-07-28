#!/usr/bin/env python3
"""
Process remaining countries for imports and then all for domestic
"""

import subprocess
import sys

def process_country(country, tradeflow):
    print(f"\n🌍 Processing {country} {tradeflow}...")
    try:
        result = subprocess.run([
            sys.executable, 'run_single_country.py', country, tradeflow
        ], timeout=600, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {country} {tradeflow} completed")
            return True
        else:
            print(f"❌ {country} {tradeflow} failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Remaining imports
remaining_imports = ['GB', 'FR', 'IT', 'CA', 'BR', 'AU', 'KR', 'US', 'IN']
print(f"Processing {len(remaining_imports)} remaining imports...")

for country in remaining_imports:
    process_country(country, 'imports')

# All domestic flows
all_countries = ['CN', 'DE', 'JP', 'GB', 'FR', 'IT', 'CA', 'BR', 'AU', 'KR', 'US', 'IN']
print(f"\nProcessing domestic flows for all {len(all_countries)} countries...")

for country in all_countries:
    process_country(country, 'domestic')

print("\n🎯 All processing complete!")