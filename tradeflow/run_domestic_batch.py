#!/usr/bin/env python3
"""
Run domestic processing for both countries automatically
Allocates 20 minutes per country and reports timing
"""

import subprocess
import sys
import time
from config_loader import load_config

def run_country_domestic(country):
    """Run complete domestic processing for a single country with timing"""
    print(f"\n{'='*80}")
    print(f"🏠 STARTING DOMESTIC PROCESSING FOR {country}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    scripts = [
        'industryflow.py',
        'industryflow_finaldemand.py',
        'industryflow_factor.py',
        'create_full_trade_factors.py',
        'create_trade_impacts.py',
        'trade_resources.py'
    ]
    
    # Update country in config
    subprocess.run([sys.executable, 'update_current_country.py', country], 
                  capture_output=True, timeout=30)
    
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
                        if any(keyword in line for keyword in ['✅', 'Created', 'Total', 'completed']):
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
    print(f"🎯 {country} DOMESTIC PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"⏱️  Total time: {minutes}m {seconds}s")
    print(f"✅ Scripts completed: {success_count}/{len(scripts)}")
    
    if success_count == len(scripts):
        print(f"🎉 {country} domestic processing fully successful!")
    else:
        print(f"⚠️  {country} domestic processing partially completed")
    
    return success_count == len(scripts)

def main():
    """Process both countries automatically"""
    countries = ['IN', 'US']
    
    print(f"🚀 STARTING AUTOMATIC DOMESTIC BATCH PROCESSING")
    print(f"Countries: {', '.join(countries)}")
    print(f"Time allocation: 20 minutes per country")
    print(f"Total estimated time: {len(countries) * 20} minutes")
    
    batch_start = time.time()
    results = {}
    
    for i, country in enumerate(countries, 1):
        print(f"\n{'🔄' * 20}")
        print(f"PROCESSING COUNTRY {i}/{len(countries)}: {country}")
        print(f"{'🔄' * 20}")
        
        country_success = run_country_domestic(country)
        results[country] = country_success
    
    # Final batch summary
    batch_time = time.time() - batch_start
    batch_minutes = int(batch_time // 60)
    batch_seconds = int(batch_time % 60)
    
    successful = [c for c, success in results.items() if success]
    failed = [c for c, success in results.items() if not success]
    
    print(f"\n{'='*80}")
    print(f"🏁 DOMESTIC BATCH PROCESSING COMPLETE")
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
            result = subprocess.run(['find', f'year/2019/{country}/domestic', '-name', '*.csv', '-type', 'f'], 
                                  capture_output=True, text=True)
            file_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            status = "✅" if results[country] else "⚠️ "
            print(f"  {status} {country}: {file_count} CSV files created")
        except:
            print(f"  ❓ {country}: Unable to count files")

if __name__ == "__main__":
    main()