#!/usr/bin/env python3
"""
Run trade flow analysis for multiple countries in sequence
Supports comma-separated country list in config.yaml
"""

import subprocess
import sys
from pathlib import Path
from config_loader import load_config, update_config

def run_script(script_name, country, tradeflow):
    """Run a single script for a specific country and trade flow type"""
    print(f"\n{'='*60}")
    print(f"Running {script_name} for {country} {tradeflow}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully for {country}")
            if result.stdout:
                # Show last few lines of output for key info
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:
                    if any(keyword in line for keyword in ['✅', 'Created', 'Summary', 'Total']):
                        print(f"   {line}")
        else:
            print(f"❌ {script_name} failed for {country}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {script_name} timed out for {country}")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name} for {country}: {e}")
        return False
        
    return True

def run_all_scripts_for_country(country, tradeflow):
    """Run all export scripts for a single country"""
    scripts = [
        'industryflow.py',
        'industryflow_finaldemand.py', 
        'industryflow_factor.py',
        'create_full_trade_factors.py',
        'create_trade_impacts.py',
        'trade_resources.py'
    ]
    
    print(f"\n🌍 Processing {country} for {tradeflow}")
    
    # Update config for this country
    update_config({
        'COUNTRY': country,
        'TRADEFLOW': tradeflow  
    })
    
    success_count = 0
    for script in scripts:
        if run_script(script, country, tradeflow):
            success_count += 1
        else:
            print(f"⚠️  Continuing despite failure in {script}")
    
    print(f"\n📊 {country} {tradeflow} complete: {success_count}/{len(scripts)} scripts succeeded")
    return success_count == len(scripts)

def main():
    """Main function to process multiple countries"""
    config = load_config()
    
    # Parse comma-separated countries
    country_string = config.get('COUNTRY', '')
    if ',' in country_string:
        countries = [c.strip() for c in country_string.split(',')]
    else:
        countries = [country_string.strip()]
    
    tradeflow = config.get('TRADEFLOW', 'exports')
    
    print(f"🚀 Starting batch processing")
    print(f"Countries: {', '.join(countries)}")
    print(f"Trade Flow: {tradeflow}")
    print(f"Total countries to process: {len(countries)}")
    
    successful_countries = []
    failed_countries = []
    
    for i, country in enumerate(countries, 1):
        print(f"\n{'='*80}")
        print(f"Processing country {i}/{len(countries)}: {country}")
        print(f"{'='*80}")
        
        if run_all_scripts_for_country(country, tradeflow):
            successful_countries.append(country)
        else:
            failed_countries.append(country)
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"🎯 BATCH PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Successful countries ({len(successful_countries)}): {', '.join(successful_countries)}")
    if failed_countries:
        print(f"❌ Failed countries ({len(failed_countries)}): {', '.join(failed_countries)}")
    
    print(f"\nTotal success rate: {len(successful_countries)}/{len(countries)} ({len(successful_countries)/len(countries)*100:.1f}%)")

if __name__ == "__main__":
    main()