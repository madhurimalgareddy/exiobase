#!/usr/bin/env python3
"""
Smart batch processing with enhanced country list handling
Supports: "all", "default", auto-populate current, cleanup when done
"""

import subprocess
import sys
import time
import yaml
from pathlib import Path
from config_loader import load_config

def get_existing_countries(year):
    """Get list of countries that have folders in the year directory"""
    year_path = Path(f"year/{year}")
    if not year_path.exists():
        return []
    
    countries = []
    for item in year_path.iterdir():
        if item.is_dir() and len(item.name) == 2:  # Country codes are 2 letters
            countries.append(item.name)
    
    return sorted(countries)

def get_default_countries():
    """Get the default list of 12 countries"""
    return ['CN', 'DE', 'JP', 'GB', 'FR', 'IT', 'CA', 'BR', 'AU', 'KR', 'US', 'IN']

def resolve_country_list(config):
    """Resolve country list based on 'all', 'default', or explicit list"""
    country_config = config['COUNTRY']
    
    if isinstance(country_config, dict):
        country_list = country_config.get('list', '')
    else:
        country_list = str(country_config)
    
    year = config['YEAR']
    
    if country_list.lower() == 'all':
        print("🌍 Resolving 'all' - checking existing country folders...")
        existing = get_existing_countries(year)
        if existing:
            print(f"Found {len(existing)} existing countries: {', '.join(existing)}")
            return existing
        else:
            print("No existing countries found, using default list")
            return get_default_countries()
    
    elif country_list.lower() == 'default':
        print("🎯 Using default country list")
        return get_default_countries()
    
    else:
        # Parse comma-separated list
        countries = [c.strip() for c in country_list.split(',')]
        print(f"📋 Using explicit country list: {', '.join(countries)}")
        return countries

def update_config_file(updates):
    """Update config.yaml file with new values"""
    config_path = Path(__file__).parent / 'config.yaml'
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Apply updates
    for key, value in updates.items():
        if '.' in key:
            # Handle nested keys like COUNTRY.current
            parts = key.split('.')
            current_level = config
            for part in parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            current_level[parts[-1]] = value
        else:
            config[key] = value
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def remove_config_key(key_path):
    """Remove a key from config.yaml"""
    config_path = Path(__file__).parent / 'config.yaml'
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Remove nested key
    parts = key_path.split('.')
    current_level = config
    for part in parts[:-1]:
        if part in current_level:
            current_level = current_level[part]
        else:
            return  # Key doesn't exist
    
    if parts[-1] in current_level:
        del current_level[parts[-1]]
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def run_country_processing(country, tradeflow):
    """Run complete processing for a single country with timing"""
    print(f"\n{'='*80}")
    print(f"🏠 STARTING {tradeflow.upper()} PROCESSING FOR {country}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    # Set current country in config
    update_config_file({'COUNTRY.current': country})
    
    scripts = [
        'industryflow.py',
        'industryflow_finaldemand.py',
        'industryflow_factor.py',
        'create_full_trade_factors.py',
        'create_trade_impacts.py',
        'trade_resources.py'
    ]
    
    success_count = 0
    for i, script in enumerate(scripts, 1):
        script_start = time.time()
        print(f"\n▶️  [{i}/{len(scripts)}] Running {script} for {country}...")
        
        try:
            result = subprocess.run([
                sys.executable, script
            ], capture_output=True, text=True, timeout=1200)  # 20 minutes per script
            
            script_time = time.time() - script_start
            
            if result.returncode == 0:
                print(f"✅ {script} completed in {script_time:.1f}s")
                # Show key output lines
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[-3:]:
                        if any(keyword in line for keyword in ['✅', 'Created', 'Total', 'completed', 'factors']):
                            print(f"   📊 {line}")
                success_count += 1
            else:
                print(f"❌ {script} failed after {script_time:.1f}s")
                if result.stderr:
                    error_lines = result.stderr.strip().split('\n')
                    print(f"   ⚠️  Error: {error_lines[-1] if error_lines else 'Unknown error'}")
                break
                
        except subprocess.TimeoutExpired:
            script_time = time.time() - script_start
            print(f"⏰ {script} timed out after {script_time:.1f}s (20 min limit)")
            break
        except Exception as e:
            script_time = time.time() - script_start
            print(f"❌ {script} error after {script_time:.1f}s: {e}")
            break
    
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    print(f"\n{'='*60}")
    print(f"🎯 {country} {tradeflow.upper()} PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"⏱️  Total time: {minutes}m {seconds}s")
    print(f"✅ Scripts completed: {success_count}/{len(scripts)}")
    
    if success_count == len(scripts):
        print(f"🎉 {country} {tradeflow} processing fully successful!")
    else:
        print(f"⚠️  {country} {tradeflow} processing partially completed")
    
    return success_count == len(scripts)

def main():
    """Smart batch processing with enhanced country handling"""
    config = load_config()
    tradeflow = config['TRADEFLOW']
    
    # Resolve country list (handles 'all', 'default', explicit)
    countries = resolve_country_list(config)
    
    print(f"\n🚀 STARTING SMART BATCH PROCESSING")
    print(f"Trade Flow: {tradeflow}")
    print(f"Countries: {', '.join(countries)}")
    print(f"Total countries to process: {len(countries)}")
    print(f"Time allocation: 20 minutes per country")
    print(f"Estimated total time: {len(countries) * 20} minutes")
    
    batch_start = time.time()
    results = {}
    
    for i, country in enumerate(countries, 1):
        print(f"\n{'🔄' * 20}")
        print(f"PROCESSING COUNTRY {i}/{len(countries)}: {country}")
        print(f"{'🔄' * 20}")
        
        country_success = run_country_processing(country, tradeflow)
        results[country] = country_success
    
    # Clean up - remove current from config when done
    print(f"\n🧹 Cleaning up config - removing current country setting...")
    remove_config_key('COUNTRY.current')
    
    # Final batch summary
    batch_time = time.time() - batch_start
    batch_minutes = int(batch_time // 60)
    batch_seconds = int(batch_time % 60)
    
    successful = [c for c, success in results.items() if success]
    failed = [c for c, success in results.items() if not success]
    
    print(f"\n{'='*80}")
    print(f"🏁 SMART BATCH PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"⏱️  Total batch time: {batch_minutes}m {batch_seconds}s")
    print(f"✅ Successful countries: {', '.join(successful) if successful else 'None'}")
    if failed:
        print(f"❌ Failed countries: {', '.join(failed)}")
    print(f"📊 Success rate: {len(successful)}/{len(countries)} ({len(successful)/len(countries)*100:.1f}%)")
    
    # Show final file counts
    print(f"\n📁 Final output summary:")
    for country in countries:
        try:
            result = subprocess.run(['find', f'year/2019/{country}/{tradeflow}', '-name', '*.csv', '-type', 'f'], 
                                  capture_output=True, text=True)
            file_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            status = "✅" if results[country] else "⚠️ "
            print(f"  {status} {country}: {file_count} CSV files created")
        except:
            print(f"  ❓ {country}: Unable to count files")

if __name__ == "__main__":
    main()