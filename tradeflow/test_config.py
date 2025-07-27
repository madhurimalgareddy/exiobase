#!/usr/bin/env python3
"""
Test configuration switching
"""

from config_loader import load_config, update_config, print_config_summary

def test_config_switching():
    """
    Test switching between different tradeflow configurations
    """
    print("Testing Configuration Switching")
    print("=" * 50)
    
    # Test each tradeflow type
    for tradeflow_type in ['imports', 'exports', 'domestic']:
        print(f"\nSwitching to {tradeflow_type}...")
        update_config({'TRADEFLOW': tradeflow_type})
        config = load_config()
        print_config_summary(config)
        
        # Test path generation
        from config_loader import get_file_path, get_reference_file_path
        print(f"Sample paths:")
        print(f"  Industry trade: {get_file_path(config, 'industry_tradeflow')}")
        print(f"  Trade impacts: {get_file_path(config, 'trade_impacts')}")
        print(f"  Factors (ref): {get_reference_file_path(config, 'factors')}")
    
    print("\n" + "=" * 50)
    print("Configuration switching test completed!")

if __name__ == "__main__":
    test_config_switching()