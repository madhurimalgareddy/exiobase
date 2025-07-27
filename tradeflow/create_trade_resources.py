#!/usr/bin/env python3
"""
Create trade_resources.csv that focuses on resource impacts (employment, land, water, energy, materials)
excluding air emissions which are covered in trade_impacts.csv
"""

import pandas as pd
import numpy as np

def create_trade_resources():
    """
    Create trade_resources.csv focusing on non-air emission environmental impacts
    """
    
    print("Reading input files...")
    
    # Read the trade flows
    trade_df = pd.read_csv('csv/industry_tradeflow.csv')
    print(f"Loaded {len(trade_df)} trade flows")
    
    # Read the trade factors (environmental coefficients and impacts)
    # Use the full trade_factors file if available, otherwise fall back to the limited one
    try:
        trade_factors_df = pd.read_csv('csv/trade_factors.csv')
        print(f"Loaded {len(trade_factors_df)} trade-factor relationships (full dataset)")
    except FileNotFoundError:
        trade_factors_df = pd.read_csv('csv/trade_factors_lite.csv')
        print(f"Loaded {len(trade_factors_df)} trade-factor relationships (limited dataset)")
    
    # Read the factors metadata for units and context
    factors_df = pd.read_csv('csv/factors.csv')
    print(f"Loaded {len(factors_df)} factor definitions")
    
    # Merge trade_factors with factor metadata
    print("Merging trade factors with metadata...")
    enhanced_factors = trade_factors_df.merge(
        factors_df[['factor_id', 'unit', 'context', 'name', 'fullname']], 
        on='factor_id', 
        how='left'
    )
    
    # Filter out air emissions - focus on resources
    print("Filtering for resource impacts (non-air emissions)...")
    resource_contexts = [
        'natural_resource/water',
        'natural_resource/land', 
        'natural_resource/energy',
        'natural_resource/in_ground',
        'economic/employment'
    ]
    
    # Also include water factors that might be classified as emission/water
    water_factors = enhanced_factors[
        (enhanced_factors['context'].isin(resource_contexts)) |
        (enhanced_factors['context'] == 'emission/water') |
        (enhanced_factors['name'].str.contains('Water', case=False, na=False))
    ]
    
    print(f"Found {len(water_factors)} resource impact relationships")
    
    if water_factors.empty:
        print("No resource factors found, creating empty trade_resources.csv")
        empty_df = trade_df.copy()
        empty_df['total_resource_value'] = 0
        empty_df['resource_count'] = 0
        empty_df.to_csv('csv/trade_resources.csv', index=False)
        return empty_df
    
    print("Calculating resource impact summaries...")
    
    # Group by trade_id and calculate summary statistics for resources
    resource_summary = water_factors.groupby('trade_id').agg({
        'impact_value': ['sum', 'count'],
        'factor_id': 'nunique'
    }).round(3)
    
    # Flatten column names
    resource_summary.columns = ['total_resource_value', 'resource_count', 'unique_resource_factors']
    resource_summary = resource_summary.reset_index()
    
    # Calculate impact by resource context
    print("Calculating impacts by resource context...")
    
    context_impacts = water_factors.groupby(['trade_id', 'context'])['impact_value'].sum().unstack(fill_value=0)
    context_impacts = context_impacts.round(3)
    
    # Calculate impact by specific resource types
    print("Calculating impacts by specific resource types...")
    
    # Define specific resource categories
    resource_categories = {
        'Water_Consumption': ['Water Consumption Blue', 'Water Consumption Green'],
        'Water_Withdrawal': ['Water Withdrawal Blue'],
        'Employment_People': ['Employment people:'],
        'Employment_Hours': ['Employment hours:'],
        'Energy_Use': ['Energy use'],
        'Land_Cropland': ['Cropland'],
        'Land_Forest': ['Forest'],
        'Land_Artificial': ['Artificial Surfaces'],
        'Land_Pastures': ['meadows & pastures', 'Permanent pastures'],
        'Materials_Crops': ['Primary Crops'],
        'Materials_Forestry': ['Forestry'],
        'Materials_Fossil': ['Fossil Fuels'],
        'Materials_Metals': ['Metal Ores'],
        'Materials_Minerals': ['Non-Metallic Minerals'],
        'Materials_Fishery': ['Fishery']
    }
    
    resource_type_impacts = pd.DataFrame(index=water_factors['trade_id'].unique())
    
    for resource_type, resource_names in resource_categories.items():
        # Find factors that contain any of the specified names
        matching_factors = water_factors[
            water_factors['fullname'].str.contains('|'.join(resource_names), case=False, na=False)
        ]
        
        if not matching_factors.empty:
            type_impact = matching_factors.groupby('trade_id')['impact_value'].sum()
            resource_type_impacts[resource_type] = type_impact
            print(f"  {resource_type}: {len(matching_factors)} factor relationships")
    
    resource_type_impacts = resource_type_impacts.fillna(0).round(3)
    
    # Calculate resource intensity by unit type
    print("Calculating resource intensities by unit type...")
    
    unit_categories = {
        'Water_Total_Mm3': ['Mm3'],
        'Employment_Total_People': ['1000 p'],
        'Employment_Total_Hours': ['M.hr'],
        'Energy_Total_TJ': ['TJ'],
        'Land_Total_km2': ['km2'],
        'Materials_Total_kt': ['kt']
    }
    
    unit_type_impacts = pd.DataFrame(index=water_factors['trade_id'].unique())
    
    for unit_type, units in unit_categories.items():
        # Find factors with specified units
        matching_factors = water_factors[
            water_factors['unit'].isin(units)
        ]
        
        if not matching_factors.empty:
            type_impact = matching_factors.groupby('trade_id')['impact_value'].sum()
            unit_type_impacts[unit_type] = type_impact
            print(f"  {unit_type}: {len(matching_factors)} factor relationships")
    
    unit_type_impacts = unit_type_impacts.fillna(0).round(3)
    
    # Merge all resource data with original trade information
    print("Merging with trade flow data...")
    
    trade_resources = trade_df.merge(resource_summary, on='trade_id', how='left')
    
    # Add context-based impacts
    if not context_impacts.empty:
        trade_resources = trade_resources.merge(
            context_impacts.reset_index(), 
            on='trade_id', 
            how='left'
        )
    
    # Add resource-type impacts
    if not resource_type_impacts.empty:
        resource_type_impacts_reset = resource_type_impacts.reset_index()
        resource_type_impacts_reset = resource_type_impacts_reset.rename(columns={'index': 'trade_id'})
        trade_resources = trade_resources.merge(
            resource_type_impacts_reset, 
            on='trade_id', 
            how='left'
        )
    
    # Add unit-type impacts
    if not unit_type_impacts.empty:
        unit_type_impacts_reset = unit_type_impacts.reset_index()
        unit_type_impacts_reset = unit_type_impacts_reset.rename(columns={'index': 'trade_id'})
        trade_resources = trade_resources.merge(
            unit_type_impacts_reset, 
            on='trade_id', 
            how='left'
        )
    
    # Fill NaN values with 0 for resource columns
    resource_columns = [col for col in trade_resources.columns if col not in ['trade_id', 'year', 'region1', 'region2', 'industry1', 'industry2', 'amount']]
    trade_resources[resource_columns] = trade_resources[resource_columns].fillna(0)
    
    # Calculate resource intensity (total resource impact per million USD of trade)
    trade_resources['resource_intensity'] = (trade_resources['total_resource_value'] / trade_resources['amount']).round(6)
    trade_resources['resource_intensity'] = trade_resources['resource_intensity'].replace([np.inf, -np.inf], 0)
    
    # Sort by total resource value descending
    trade_resources = trade_resources.sort_values('total_resource_value', ascending=False)
    
    # Save to CSV
    trade_resources.to_csv('csv/trade_resources.csv', index=False)
    
    print(f"\nCreated trade_resources.csv with {len(trade_resources)} trade transactions")
    
    # Display summary statistics
    print(f"\nSummary Statistics:")
    print(f"Total trade flows: {len(trade_resources)}")
    print(f"Trade flows with resource data: {len(trade_resources[trade_resources['resource_count'] > 0])}")
    if len(trade_resources[trade_resources['resource_count'] > 0]) > 0:
        print(f"Average resource factors per trade: {trade_resources['resource_count'].mean():.1f}")
        print(f"Total resource impact value: {trade_resources['total_resource_value'].sum():,.0f}")
        
        print(f"\nTop 10 trade flows by total resource impact:")
        top_impacts = trade_resources[trade_resources['total_resource_value'] > 0].head(10)
        top_display = top_impacts[['trade_id', 'region1', 'industry1', 'amount', 'total_resource_value', 'resource_count']]
        print(top_display.to_string(index=False))
        
        # Show context breakdown
        print(f"\nResource context breakdown:")
        context_cols = [col for col in trade_resources.columns if col.startswith(('natural_resource/', 'economic/', 'emission/water'))]
        if context_cols:
            context_summary = trade_resources[context_cols].sum().sort_values(ascending=False)
            for context, value in context_summary.items():
                if value > 0:
                    print(f"  {context}: {value:,.0f}")
        
        # Show resource type breakdown
        print(f"\nResource type breakdown:")
        resource_type_cols = [col for col in trade_resources.columns if any(col.startswith(prefix) for prefix in ['Water_', 'Employment_', 'Energy_', 'Land_', 'Materials_'])]
        if resource_type_cols:
            resource_summary = trade_resources[resource_type_cols].sum().sort_values(ascending=False)
            for resource_type, value in resource_summary.items():
                if value > 0:
                    print(f"  {resource_type}: {value:,.1f}")
        
        # Show unit breakdown
        print(f"\nResource by unit breakdown:")
        unit_type_cols = [col for col in trade_resources.columns if col.endswith(('_Mm3', '_People', '_Hours', '_TJ', '_km2', '_kt'))]
        if unit_type_cols:
            unit_summary = trade_resources[unit_type_cols].sum().sort_values(ascending=False)
            for unit_type, value in unit_summary.items():
                if value > 0:
                    print(f"  {unit_type}: {value:,.0f}")
    
    # Show column information
    print(f"\nColumns in trade_resources.csv ({len(trade_resources.columns)} total):")
    for i, col in enumerate(trade_resources.columns):
        print(f"  {i+1:2d}. {col}")
    
    return trade_resources

if __name__ == "__main__":
    create_trade_resources()