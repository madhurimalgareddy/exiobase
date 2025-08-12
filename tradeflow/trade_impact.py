#!/usr/bin/env python3
"""
Create trade_impact.csv that shows total environmental impacts per trade transaction
"""

import pandas as pd
import numpy as np
from config_loader import load_config, get_file_path, get_reference_file_path, print_config_summary

def create_trade_impact():
    """
    Create trade_impact.csv by aggregating environmental impacts per trade transaction
    """
    # Load configuration
    config = load_config()
    print_config_summary(config)
    
    print("Reading input files...")
    
    # Read the trade flows
    trade_file = get_file_path(config, 'industryflow')
    trade_df = pd.read_csv(trade_file)
    print(f"Loaded {len(trade_df)} trade flows")
    
    # Read the trade factors (environmental coefficients and impacts)
    trade_factor_file = get_file_path(config, 'trade_factor')
    trade_factor_df = pd.read_csv(trade_factor_file)
    print(f"Loaded {len(trade_factor_df)} trade-factor relationships")
    
    # Read the factors metadata for units and extension
    factors_file = get_reference_file_path(config, 'factors')
    factors_df = pd.read_csv(factors_file)
    print(f"Loaded {len(factors_df)} factor definitions")
    
    # Merge trade_factor with factor metadata
    print("Merging trade factors with metadata...")
    enhanced_factors = trade_factor_df.merge(
        factors_df[['factor_id', 'unit', 'extension', 'stressor']], 
        on='factor_id', 
        how='left'
    )
    
    print("Calculating impact summaries by trade transaction...")
    
    # Group by trade_id and calculate summary statistics
    impact_summary = enhanced_factors.groupby('trade_id').agg({
        'impact_value': ['sum', 'count'],
        'factor_id': 'nunique'
    }).round(3)
    
    # Flatten column names
    impact_summary.columns = ['total_impact_value', 'factor_count', 'unique_factors']
    impact_summary = impact_summary.reset_index()
    
    # Calculate impact by extension (air_emissions, water, etc.)
    print("Calculating impacts by environmental extension...")
    
    extension_impacts = enhanced_factors.groupby(['trade_id', 'extension'])['impact_value'].sum().unstack(fill_value=0)
    extension_impacts = extension_impacts.round(3)
    
    # Calculate impact by major factor types
    print("Calculating impacts by major factor types...")
    
    # Define major factor categories
    major_factors = {
        'CO2_total': ['CO2', 'CO2_bio'],
        'CH4_total': ['CH4'],
        'N2O_total': ['N2O'],
        'NOX_total': ['NOX', 'NOx'],
        'Water_total': ['Water Consumption Blue', 'Water Withdrawal Blue'],
        'Employment_total': ['Employment people:', 'Employment hours:'],
        'Energy_total': ['Energy use'],
        'Land_total': ['Cropland', 'Forest', 'Artificial Surfaces']
    }
    
    factor_type_impacts = pd.DataFrame(index=enhanced_factors['trade_id'].unique())
    
    for factor_type, factor_names in major_factors.items():
        # Find factors that contain any of the specified names
        matching_factors = enhanced_factors[
            enhanced_factors['stressor'].str.contains('|'.join(factor_names), case=False, na=False)
        ]
        
        if not matching_factors.empty:
            type_impact = matching_factors.groupby('trade_id')['impact_value'].sum()
            factor_type_impacts[factor_type] = type_impact
    
    factor_type_impacts = factor_type_impacts.fillna(0).round(3)
    
    # Merge all impact data with original trade information
    print("Merging with trade flow data...")
    
    trade_impact = trade_df.merge(impact_summary, on='trade_id', how='left')
    
    # Add extension-based impacts
    if not extension_impacts.empty:
        trade_impact = trade_impact.merge(
            extension_impacts.reset_index(), 
            on='trade_id', 
            how='left'
        )
    
    # Add factor-type impacts
    if not factor_type_impacts.empty:
        factor_type_impacts_reset = factor_type_impacts.reset_index()
        factor_type_impacts_reset = factor_type_impacts_reset.rename(columns={'index': 'trade_id'})
        trade_impact = trade_impact.merge(
            factor_type_impacts_reset, 
            on='trade_id', 
            how='left'
        )
    
    # Fill NaN values with 0 for impact columns
    impact_columns = [col for col in trade_impact.columns if col not in ['trade_id', 'year', 'region1', 'region2', 'industry1', 'industry2', 'amount']]
    trade_impact[impact_columns] = trade_impact[impact_columns].fillna(0)
    
    # Calculate impact intensity (total impact per million USD of trade)
    trade_impact['impact_intensity'] = (trade_impact['total_impact_value'] / trade_impact['amount']).round(6)
    trade_impact['impact_intensity'] = trade_impact['impact_intensity'].replace([np.inf, -np.inf], 0)
    
    # Sort by total impact value descending
    trade_impact = trade_impact.sort_values('total_impact_value', ascending=False)
    
    # Save to CSV
    output_file = get_file_path(config, 'trade_impact')
    trade_impact.to_csv(output_file, index=False)
    
    print(f"\nCreated trade_impact.csv with {len(trade_impact)} trade transactions")
    
    # Display summary statistics
    print(f"\nSummary Statistics:")
    print(f"Total trade flows: {len(trade_impact)}")
    print(f"Trade flows with environmental data: {len(trade_impact[trade_impact['factor_count'] > 0])}")
    print(f"Average factors per trade: {trade_impact['factor_count'].mean():.1f}")
    print(f"Total environmental impact value: {trade_impact['total_impact_value'].sum():,.0f}")
    
    print(f"\nTop 10 trade flows by total environmental impact:")
    top_impacts = trade_impact.head(10)[['trade_id', 'region1', 'industry1', 'amount', 'total_impact_value', 'factor_count']]
    print(top_impacts.to_string(index=False))
    
    print(f"\nContext breakdown (sum of all impacts):")
    extension_cols = [col for col in trade_impact.columns if col in ['air_emissions', 'water', 'land', 'material', 'energy', 'employment']]
    if extension_cols:
        extension_summary = trade_impact[extension_cols].sum().sort_values(ascending=False)
        for extension, value in extension_summary.head(10).items():
            print(f"  {extension}: {value:,.0f}")
    
    print(f"\nMajor factor type breakdown:")
    factor_type_cols = [col for col in trade_impact.columns if col.endswith('_total')]
    if factor_type_cols:
        factor_summary = trade_impact[factor_type_cols].sum().sort_values(ascending=False)
        for factor_type, value in factor_summary.items():
            print(f"  {factor_type}: {value:,.0f}")
    
    # Show column information
    print(f"\nColumns in trade_impact.csv ({len(trade_impact.columns)} total):")
    for i, col in enumerate(trade_impact.columns):
        print(f"  {i+1:2d}. {col}")
    
    return trade_impact

if __name__ == "__main__":
    create_trade_impact()