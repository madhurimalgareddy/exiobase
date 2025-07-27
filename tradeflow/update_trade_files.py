#!/usr/bin/env python3
"""
Update existing industry_tradeflow.csv to add trade_id and create trade_factors_lite.csv
"""

import pandas as pd
import numpy as np

def update_trade_files():
    """
    Add trade_id to existing industry_tradeflow.csv and create trade_factors_lite.csv
    """
    
    # Read existing industry_tradeflow.csv
    print("Reading existing industry_tradeflow.csv...")
    trade_df = pd.read_csv('csv/industry_tradeflow.csv')
    
    # Add trade_id column if it doesn't exist
    if 'trade_id' not in trade_df.columns:
        print("Adding trade_id column...")
        trade_df['trade_id'] = trade_df.index + 1
        
        # Reorder columns to put trade_id first
        cols = ['trade_id'] + [col for col in trade_df.columns if col != 'trade_id']
        trade_df = trade_df[cols]
        
        # Save updated file
        trade_df.to_csv('csv/industry_tradeflow.csv', index=False)
        print(f"Updated industry_tradeflow.csv with trade_id column ({len(trade_df)} rows)")
    
    # Read factors.csv
    print("Reading factors.csv...")
    factors_df = pd.read_csv('csv/factors.csv')
    
    # Create trade_factors_lite.csv with realistic sample data
    print("Creating trade_factors_lite.csv...")
    
    # Focus on major factors for demonstration
    major_factors = factors_df[factors_df['name'].isin(['CO2', 'CH4', 'N2O', 'CO', 'NOX'])]['factor_id'].tolist()
    if not major_factors:
        # If specific factors not found, use first few
        major_factors = factors_df['factor_id'].head(5).tolist()
    
    trade_factors_list = []
    
    # Sample trade flows (limit to first 1000 for performance)
    sample_trades = trade_df.head(1000)
    
    np.random.seed(42)  # For reproducible results
    
    for _, trade_row in sample_trades.iterrows():
        trade_id = trade_row['trade_id']
        trade_amount = trade_row['amount']
        
        # For each trade, assign factors based on industry type
        industry1 = trade_row['industry1']
        
        for factor_id in major_factors:
            # Create realistic coefficients based on factor type
            factor_name = factors_df[factors_df['factor_id'] == factor_id]['name'].iloc[0]
            
            if factor_name == 'CO2':
                # CO2 coefficients typically higher
                coefficient = np.random.uniform(0.5, 3.0)
            elif factor_name == 'CH4':
                # Methane coefficients typically lower
                coefficient = np.random.uniform(0.01, 0.2)
            elif factor_name in ['N2O', 'NOX']:
                # Other air emissions
                coefficient = np.random.uniform(0.005, 0.1)
            else:
                # Default coefficient
                coefficient = np.random.uniform(0.001, 0.05)
            
            # Adjust based on industry type
            if 'CRUDE' in industry1 or 'COKIN' in industry1:
                coefficient *= 2.0  # Energy sectors have higher emissions
            elif 'AGRIC' in industry1 or 'CATTLE' in industry1:
                if factor_name == 'CH4':
                    coefficient *= 3.0  # Agriculture has high methane
            elif 'ELECT' in industry1:
                if factor_name == 'CO2':
                    coefficient *= 1.5  # Electricity has high CO2
            
            # Calculate impact value
            impact_value = trade_amount * coefficient
            
            # Only include meaningful impacts
            if abs(impact_value) > 0.01:
                trade_factors_list.append({
                    'trade_id': trade_id,
                    'factor_id': factor_id,
                    'coefficient': round(coefficient, 6),
                    'impact_value': round(impact_value, 3)
                })
    
    # Create DataFrame and save
    trade_factors_df = pd.DataFrame(trade_factors_list)
    trade_factors_df.to_csv('csv/trade_factors_lite.csv', index=False)
    
    print(f"Created trade_factors_lite.csv with {len(trade_factors_df)} factor-trade relationships")
    print(f"Factors included: {trade_factors_df['factor_id'].nunique()} unique factors")
    print(f"Trades covered: {trade_factors_df['trade_id'].nunique()} trade flows")
    
    # Display sample
    print("\nSample trade_factors_lite.csv data:")
    print(trade_factors_df.head(10).to_string(index=False))
    
    return trade_factors_df

if __name__ == "__main__":
    update_trade_files()