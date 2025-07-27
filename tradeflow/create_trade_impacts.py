#!/usr/bin/env python3
"""
Create trade_impacts.csv that shows total environmental impacts per trade transaction
"""

import pandas as pd
import numpy as np

def create_trade_impacts():
    """
    Create trade_impacts.csv by aggregating environmental impacts per trade transaction
    """
    
    print("Reading input files...")
    
    # Read the trade flows
    trade_df = pd.read_csv('industry_tradeflow.csv')
    print(f"Loaded {len(trade_df)} trade flows")
    
    # Read the trade factors (environmental coefficients and impacts)
    trade_factors_df = pd.read_csv('trade_factors.csv')
    print(f"Loaded {len(trade_factors_df)} trade-factor relationships")
    
    # Read the factors metadata for units and context
    factors_df = pd.read_csv('factors.csv')
    print(f"Loaded {len(factors_df)} factor definitions")
    
    # Merge trade_factors with factor metadata
    print("Merging trade factors with metadata...")
    enhanced_factors = trade_factors_df.merge(
        factors_df[['factor_id', 'unit', 'context', 'name']], 
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
    
    # Calculate impact by context (emission/air, natural_resource/water, etc.)
    print("Calculating impacts by environmental context...")
    
    context_impacts = enhanced_factors.groupby(['trade_id', 'context'])['impact_value'].sum().unstack(fill_value=0)
    context_impacts = context_impacts.round(3)
    
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
            enhanced_factors['name'].str.contains('|'.join(factor_names), case=False, na=False)
        ]
        
        if not matching_factors.empty:
            type_impact = matching_factors.groupby('trade_id')['impact_value'].sum()
            factor_type_impacts[factor_type] = type_impact
    
    factor_type_impacts = factor_type_impacts.fillna(0).round(3)
    
    # Merge all impact data with original trade information
    print("Merging with trade flow data...")
    
    trade_impacts = trade_df.merge(impact_summary, on='trade_id', how='left')
    
    # Add context-based impacts
    if not context_impacts.empty:
        trade_impacts = trade_impacts.merge(
            context_impacts.reset_index(), 
            on='trade_id', 
            how='left'
        )
    
    # Add factor-type impacts
    if not factor_type_impacts.empty:
        factor_type_impacts_reset = factor_type_impacts.reset_index()
        factor_type_impacts_reset = factor_type_impacts_reset.rename(columns={'index': 'trade_id'})
        trade_impacts = trade_impacts.merge(
            factor_type_impacts_reset, 
            on='trade_id', 
            how='left'
        )
    
    # Fill NaN values with 0 for impact columns
    impact_columns = [col for col in trade_impacts.columns if col not in ['trade_id', 'year', 'region1', 'region2', 'industry1', 'industry2', 'amount']]
    trade_impacts[impact_columns] = trade_impacts[impact_columns].fillna(0)
    
    # Calculate impact intensity (total impact per million USD of trade)
    trade_impacts['impact_intensity'] = (trade_impacts['total_impact_value'] / trade_impacts['amount']).round(6)
    trade_impacts['impact_intensity'] = trade_impacts['impact_intensity'].replace([np.inf, -np.inf], 0)
    
    # Sort by total impact value descending
    trade_impacts = trade_impacts.sort_values('total_impact_value', ascending=False)
    
    # Save to CSV
    trade_impacts.to_csv('trade_impacts.csv', index=False)
    
    print(f"\nCreated trade_impacts.csv with {len(trade_impacts)} trade transactions")
    
    # Display summary statistics
    print(f"\nSummary Statistics:")
    print(f"Total trade flows: {len(trade_impacts)}")
    print(f"Trade flows with environmental data: {len(trade_impacts[trade_impacts['factor_count'] > 0])}")
    print(f"Average factors per trade: {trade_impacts['factor_count'].mean():.1f}")
    print(f"Total environmental impact value: {trade_impacts['total_impact_value'].sum():,.0f}")
    
    print(f"\nTop 10 trade flows by total environmental impact:")
    top_impacts = trade_impacts.head(10)[['trade_id', 'region1', 'industry1', 'amount', 'total_impact_value', 'factor_count']]
    print(top_impacts.to_string(index=False))
    
    print(f"\nContext breakdown (sum of all impacts):")
    context_cols = [col for col in trade_impacts.columns if col.startswith(('emission/', 'natural_resource/', 'economic/'))]
    if context_cols:
        context_summary = trade_impacts[context_cols].sum().sort_values(ascending=False)
        for context, value in context_summary.head(10).items():
            print(f"  {context}: {value:,.0f}")
    
    print(f"\nMajor factor type breakdown:")
    factor_type_cols = [col for col in trade_impacts.columns if col.endswith('_total')]
    if factor_type_cols:
        factor_summary = trade_impacts[factor_type_cols].sum().sort_values(ascending=False)
        for factor_type, value in factor_summary.items():
            print(f"  {factor_type}: {value:,.0f}")
    
    # Show column information
    print(f"\nColumns in trade_impacts.csv ({len(trade_impacts.columns)} total):")
    for i, col in enumerate(trade_impacts.columns):
        print(f"  {i+1:2d}. {col}")
    
    return trade_impacts

if __name__ == "__main__":
    create_trade_impacts()