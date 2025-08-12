#!/usr/bin/env python3
"""
Process countries sequentially from comma-separated COUNTRY field
Uses COUNTRY.current to track progress and resume if interrupted
"""

import subprocess
import sys
from config_loader import load_config, update_config

def get_countries_to_process():
    """Get list of countries that still need processing"""
    config = load_config()
    
    # Parse comma-separated countries
    all_countries = [c.strip() for c in config['COUNTRY'].split(',')]
    current_country = config.get('COUNTRY.current', '')
    
    if current_country and current_country in all_countries:
        # Start from current country
        start_idx = all_countries.index(current_country)
        return all_countries[start_idx:]
    else:
        # Start from beginning
        return all_countries

def run_single_country_scripts(country, tradeflow):
    """Run all scripts for a single country"""
    print(f"🌍 Processing {country} for {tradeflow}")
    
    # Update current country in config
    update_config({'COUNTRY.current': country})
    
    scripts = [
        'trade.py',
        'industryflow_finaldemand.py',
        'industryflow_factor.py',
        'create_full_trade_factor.py',
        'trade_impact.py',
        'trade_resource.py'
    ]
    
    success_count = 0
    for script in scripts:
        print(f"▶️  Running {script}...")
        try:
            result = subprocess.run([
                sys.executable, script
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print(f"✅ {script} completed")
                success_count += 1
            else:
                print(f"❌ {script} failed: {result.stderr}")
                print("Stopping processing for this country")
                break
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {script} timed out")
            break
        except Exception as e:
            print(f"❌ Error running {script}: {e}")
            break
    
    return success_count == len(scripts)

def main():
    """Main processing function"""
    config = load_config()
    tradeflow = config['TRADEFLOW']
    
    countries_to_process = get_countries_to_process()
    
    print(f"🚀 Starting sequential processing for {tradeflow}")
    print(f"Countries to process: {', '.join(countries_to_process)}")
    
    successful = []
    failed = []
    
    for i, country in enumerate(countries_to_process, 1):
        print(f"\n{'='*60}")
        print(f"Processing {i}/{len(countries_to_process)}: {country}")
        print(f"{'='*60}")
        
        if run_single_country_scripts(country, tradeflow):
            successful.append(country)
            print(f"✅ {country} completed successfully")
        else:
            failed.append(country)
            print(f"❌ {country} failed")
    
    # Clean up - remove COUNTRY.current when all done
    if not failed:
        print(f"\n🎯 All countries processed successfully!")
        print("Removing COUNTRY.current from config...")
        
        # Read current config and remove COUNTRY.current
        config = load_config()
        if 'COUNTRY.current' in config:
            del config['COUNTRY.current']
            
            # Write back without COUNTRY.current
            import yaml
            from pathlib import Path
            config_path = Path(__file__).parent / 'config.yaml'
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successful: {', '.join(successful)}")
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")
        print(f"Next run will resume from: {failed[0] if failed else 'N/A'}")

if __name__ == "__main__":
    main()