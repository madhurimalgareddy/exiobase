#!/usr/bin/env python3
"""
Update the current country in config.yaml
"""

import sys
import yaml
from pathlib import Path

def update_current_country(new_country):
    """Update the current country in config.yaml"""
    config_path = Path(__file__).parent / 'config.yaml'
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if isinstance(config['COUNTRY'], dict):
        config['COUNTRY']['current'] = new_country
    else:
        # Convert to new structure
        country_list = config['COUNTRY'] if isinstance(config['COUNTRY'], str) else str(config['COUNTRY'])
        config['COUNTRY'] = {
            'list': country_list,
            'current': new_country
        }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Updated current country to: {new_country}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_current_country.py <country_code>")
        print("Example: python update_current_country.py US")
        sys.exit(1)
    
    update_current_country(sys.argv[1])