#!/usr/bin/env python3
"""
Run imports for all 12 countries in sequence
"""

import subprocess
import sys

countries = ['CN', 'DE', 'JP', 'GB', 'FR', 'IT', 'CA', 'BR', 'AU', 'KR', 'US', 'IN']

print(f"🚀 Starting imports batch processing for {len(countries)} countries")

for i, country in enumerate(countries, 1):
    print(f"\n{'='*60}")
    print(f"Processing imports {i}/{len(countries)}: {country}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, 'run_single_country.py', country, 'imports'
        ], timeout=600)
        
        if result.returncode == 0:
            print(f"✅ {country} imports completed successfully")
        else:
            print(f"❌ {country} imports failed")
    except subprocess.TimeoutExpired:
        print(f"⏰ {country} imports timed out")
    except Exception as e:
        print(f"❌ Error processing {country}: {e}")

print(f"\n🎯 Imports batch processing complete!")