#!/usr/bin/env python3
"""
Configuration loader for Exiobase Trade Flow Analysis
"""

import yaml
import os
from pathlib import Path

def load_config():
    """
    Load configuration from config.yaml
    """
    config_path = Path(__file__).parent / 'config.yaml'
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def update_config(updates):
    """
    Update configuration file with new values
    """
    config_path = Path(__file__).parent / 'config.yaml'
    
    # Load current config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update with new values
    config.update(updates)
    
    # Write back to file
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    return config

def get_output_folder(config, tradeflow_type=None):
    """
    Get the appropriate output folder based on trade flow type
    """
    if tradeflow_type is None:
        tradeflow_type = config['TRADEFLOW']
    
    folder_path = config['FOLDERS'][tradeflow_type]
    # Substitute year placeholder
    return folder_path.format(year=config['YEAR'])

def get_file_path(config, file_key, tradeflow_type=None):
    """
    Get full file path for a given file key
    """
    folder = get_output_folder(config, tradeflow_type)
    filename = config['FILES'][file_key]
    
    # Ensure folder exists
    Path(folder).mkdir(parents=True, exist_ok=True)
    
    return f"{folder}/{filename}"

def get_reference_file_path(config, file_key):
    """
    Get path for reference files (always in base folder)
    """
    base_folder = config['FOLDERS']['base']
    # Substitute year placeholder
    base_folder = base_folder.format(year=config['YEAR'])
    filename = config['FILES'][file_key]
    
    # Ensure folder exists
    Path(base_folder).mkdir(parents=True, exist_ok=True)
    
    return f"{base_folder}/{filename}"

def print_config_summary(config):
    """
    Print current configuration summary
    """
    print(f"Configuration Summary:")
    print(f"  Trade Flow: {config['TRADEFLOW']}")
    print(f"  Year: {config['YEAR']}")
    print(f"  Country: {config['COUNTRY']}")
    print(f"  Output Folder: {get_output_folder(config)}")
    print()

if __name__ == "__main__":
    # Test the configuration loader
    config = load_config()
    print_config_summary(config)
    
    # Test file path generation
    print("Sample file paths:")
    print(f"  Industry trade flow: {get_file_path(config, 'industry_tradeflow')}")
    print(f"  Trade employment: {get_file_path(config, 'trade_employment')}")
    print(f"  Industries (ref): {get_reference_file_path(config, 'industries')}")