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

def is_country_completed(country, tradeflow, year):
    """Check if a country has already completed processing"""
    runnote_path = Path(f"year/{year}/{country}/{tradeflow}/runnote.md")
    return runnote_path.exists()

def filter_incomplete_countries(countries, tradeflow, year):
    """Filter out countries that have already completed processing"""
    incomplete = []
    completed = []
    
    for country in countries:
        if is_country_completed(country, tradeflow, year):
            completed.append(country)
        else:
            incomplete.append(country)
    
    if completed:
        print(f"🔄 Resume mode: Found {len(completed)} already completed countries: {', '.join(completed)}")
        print(f"📋 Processing {len(incomplete)} remaining countries: {', '.join(incomplete) if incomplete else 'None'}")
    
    return incomplete, completed

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

def run_country_processing(country, tradeflow, batch_start_time, batch_timeout=18000):
    """Run complete processing for a single country with timing and batch timeout check"""
    # Check if batch timeout exceeded before starting country
    elapsed_batch_time = time.time() - batch_start_time
    if elapsed_batch_time >= batch_timeout:
        print(f"⏰ BATCH TIMEOUT: {elapsed_batch_time/3600:.1f} hours elapsed, stopping before {country}")
        return False
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
        # Check batch timeout before each script
        elapsed_batch_time = time.time() - batch_start_time
        if elapsed_batch_time >= batch_timeout:
            print(f"⏰ BATCH TIMEOUT: {elapsed_batch_time/3600:.1f} hours elapsed, stopping at {script}")
            break
            
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
    all_countries = resolve_country_list(config)
    
    # Filter out already completed countries for resume functionality
    countries, completed_countries = filter_incomplete_countries(all_countries, tradeflow, config['YEAR'])
    
    print(f"\n🚀 STARTING SMART BATCH PROCESSING")
    print(f"Trade Flow: {tradeflow}")
    print(f"All countries: {', '.join(all_countries)}")
    print(f"Countries to process: {', '.join(countries) if countries else 'None - All completed!'}")
    print(f"Total countries to process: {len(countries)}")
    print(f"Time allocation: 5 hours total for entire batch")
    print(f"Estimated time per country: ~{300/len(countries) if countries else 0:.0f} minutes")
    
    # If all countries are completed, show summary and exit
    if not countries:
        print(f"\n🎉 ALL COUNTRIES ALREADY COMPLETED!")
        print(f"✅ Completed countries: {', '.join(completed_countries)}")
        print(f"🧹 Cleaning up config - removing current country setting...")
        remove_config_key('COUNTRY.current')
        return
    
    batch_start = time.time()
    batch_timeout = 18000  # 5 hours in seconds
    results = {}
    
    # Initialize results for completed countries as successful
    for country in completed_countries:
        results[country] = True
    
    for i, country in enumerate(countries, 1):
        # Check batch timeout before starting each country
        elapsed_batch_time = time.time() - batch_start
        if elapsed_batch_time >= batch_timeout:
            print(f"\n⏰ BATCH TIMEOUT REACHED: {elapsed_batch_time/3600:.1f} hours elapsed")
            print(f"🛑 Stopping processing. Remaining countries: {', '.join(countries[i-1:])}")
            # Mark remaining countries as not processed
            for remaining_country in countries[i-1:]:
                results[remaining_country] = False
            break
            
        remaining_time = (batch_timeout - elapsed_batch_time) / 3600
        print(f"\n{'🔄' * 20}")
        print(f"PROCESSING COUNTRY {i}/{len(countries)}: {country}")
        print(f"⏰ Batch time remaining: {remaining_time:.1f} hours")
        print(f"{'🔄' * 20}")
        
        country_success = run_country_processing(country, tradeflow, batch_start, batch_timeout)
        results[country] = country_success
        
        # If country processing was stopped due to batch timeout, break
        if not country_success and elapsed_batch_time >= batch_timeout:
            break
    
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
    print(f"⏱️  Total batch time: {batch_minutes}m {batch_seconds}s (of 5 hour limit)")
    if batch_time >= batch_timeout * 0.9:  # If we used 90%+ of time limit
        print(f"⚠️  Close to time limit: {batch_time/3600:.1f}/5.0 hours used")
    print(f"✅ All successful countries: {', '.join(successful) if successful else 'None'}")
    if failed:
        print(f"❌ Failed countries: {', '.join(failed)}")
    if completed_countries:
        print(f"🔄 Previously completed: {', '.join(completed_countries)}")
        print(f"🆕 Newly processed: {', '.join([c for c in countries if c in successful])}")
    total_countries = len(all_countries)
    print(f"📊 Overall success rate: {len(successful)}/{total_countries} ({len(successful)/total_countries*100:.1f}%)")
    
    # Show final file counts
    print(f"\n📁 Final output summary:")
    for country in all_countries:
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