# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Exiobase data processing project that extracts and transforms multiregional input-output (MRIO) data for economic and environmental analysis. The project processes trade flows, industry factors, and environmental impacts from the Exiobase database.

## Architecture

### Core Components

- **Pipelines/**: Main data processing scripts that extract and transform Exiobase data
  - `TradeImpact.py`: Processes environmental impact data by combining Z matrix flows with extension factors
  - `IndustryFactor.py`: Extracts industry-level environmental factors from F matrices
  - `Imports.py`: Calculates total trade flows between regions using Z and Y matrices
- **Functions/**: Utility functions for data operations
  - `insert_postgres.py`: Database insertion utility using SQLAlchemy
- **ExiobaseDocumentation/**: Database schema definitions for both PostgreSQL and SQL Server

### Data Flow Architecture

1. **Data Source**: Exiobase v3 database files (parsed using pymrio library)
2. **Core Matrices**:
   - Z matrix: Inter-industry flows between regions/sectors
   - Y matrix: Final demand
   - F matrix: Environmental extension factors
3. **Processing**: Transform matrices into relational format for database storage
4. **Output**: Structured CSV files and database tables

## Development Environment

### Python Environment Setup
```bash
# Create and activate virtual environment
python -m venv env
source env/bin/activate  # macOS/Linux
# or env\Scripts\activate  # Windows

# Install required dependencies
pip install pandas numpy pymrio sqlalchemy psycopg2-binary requests
```

### Running Scripts
```bash
# Activate environment first
source env/bin/activate

# Run individual pipeline scripts
python Pipelines/Pipelines/TradeImpact.py
python Pipelines/Pipelines/IndustryFactor.py
python Pipelines/Pipelines/Imports.py

# Run custom analysis scripts
python industry_tradeflow.py
```

## Data Processing Patterns

### Exiobase Data Structure
- **Regions**: 44 countries + 5 rest-of-world regions (AT, BE, CN, US, etc.)
- **Industries**: 163 detailed sectors aggregated to ~31 main categories
- **Extensions**: Air emissions, employment, energy, land use, materials, water, etc.

### Common Data Transformations
1. **Matrix Flattening**: Convert MultiIndex DataFrames to relational format
2. **Region Mapping**: Replace country codes with full names using lookup tables
3. **Extension Merging**: Combine flow data (Z/Y matrices) with factor data (F matrices)
4. **Impact Calculation**: Multiply flows by factors to get environmental impacts

### Database Schema
- **IndustryFactor**: Country-sector-factor combinations with values
- **ProductTradeImpact**: Trade flow impacts between countries by product category
- Both PostgreSQL and SQL Server schemas available

## File Path Conventions

- Exiobase data typically stored at: `H:\Exiobase Unzipped\IOT_{year}_pxp`
- Country mapping file: CSV with CountryCode and Country columns
- Output files: CSV format with structured column naming

## Key Libraries

- **pymrio**: Primary library for parsing Exiobase data files
- **pandas**: Data manipulation and transformation
- **sqlalchemy**: Database connections and operations
- **psycopg2**: PostgreSQL adapter

## Output Files Structure

### industrylow.csv
Primary trade flow data with columns: `trade_id, year, region1, region2, industry1, industry2, amount`
- **trade_id**: Unique 1-based identifier for each trade flow
- **amount**: Trade value in millions USD
- **industry1/industry2**: 5-character standardized industry codes

industrylow.csv only extracts from the Z matrix (intermediate flows),
so we add matrices Y (final demand) and F (factor inputs).

### industrylow_finaldemand.csv (Y Matrix)

Y matrix (final demand): 8,000 × \~300 final demand categories

### industrylow_factor.csv (F Matrix)

F matrices: 721 factors × 8,000 sectors across 6 extensions

### industries.csv  
Sector mapping with columns: `industry_id, name, category`
- **industry_id**: 5-character standardized codes (CRUDE, WHEAT, CATTL, etc.)
- **category**: Logical groupings (Agriculture, Mining, Manufacturing, etc.)
- **200 sectors** from Exiobase with standardized categorization

### factors.csv
Environmental/economic factors with columns: `factor_id, unit, context, name, fullname`
- **factor_id**: 1-based sequential identifier
- **context**: Logical grouping (emission/air, natural_resource/land, etc.)
- **name**: Short factor name (CO2, CH4, etc.)
- **fullname**: Complete Exiobase stressor name
- **721 factors** across 6 major contexts

### trade_factors_lg.csv
Links trade flows to environmental impacts: `trade_id, factor_id, coefficient, impact_value`
- **coefficient**: Environmental intensity coefficient from Exiobase F matrix (factor per million EUR output)
  - Represents direct environmental factor per unit of economic output in exporting region/industry
  - Units: factor_unit/million EUR (e.g., kg CO2/million EUR, Mm3 water/million EUR)
  - Derived from Exiobase satellite accounts (F matrix) which contains stressor coefficients per economic activity
- **impact_value**: Total environmental impact for this specific trade flow (trade_amount × coefficient)
  - Calculated as: impact = trade flow value (million USD) × coefficient (factor/million EUR)
  - Represents embodied environmental factor in the trade flow from exporting to importing region
- Relates each trade flow to multiple environmental factors from air emissions, water use, land use, employment, etc.

### trade_impacts.csv
Comprehensive environmental impact summary per trade transaction: `trade_id, year, region1, region2, industry1, industry2, amount, total_impact_value, factor_count, unique_factors, [context impacts], [factor type impacts], impact_intensity`
- **total_impact_value**: Sum of all environmental impact values for this trade flow (aggregated from trade_factors_lg.csv)
- **factor_count**: Number of environmental factor relationships for this trade
- **unique_factors**: Number of distinct environmental factors affecting this trade
- **Context impacts**: Separate columns for each environmental context (emission/air, natural_resource/water, etc.)
- **Factor type impacts**: Aggregated impacts by major factor categories:
  - CO2_total: All CO2 emissions (combustion + biogenic)
  - CH4_total: All methane emissions 
  - N2O_total: All nitrous oxide emissions
  - NOX_total: All nitrogen oxide emissions
  - Water_total: All water consumption and withdrawal
  - Employment_total: All employment impacts
  - Energy_total: All energy use impacts
  - Land_total: All land use impacts
- **impact_intensity**: Environmental impact per million USD of trade (total_impact_value/amount)
- **126,166 trade flows** with environmental impact calculations for 1,000 major flows

### trade_resources.csv
Resource and non-air environmental impacts per trade transaction: `trade_id, year, region1, region2, industry1, industry2, amount, total_resource_value, resource_count, unique_resource_factors, [context impacts], [resource type impacts], [unit-based impacts], resource_intensity`
- **total_resource_value**: Sum of all non-air environmental impacts (employment, water, land, energy, materials)
- **resource_count**: Number of resource factor relationships for this trade
- **Resource contexts**: Separate columns for major resource categories:
  - economic/employment: Employment people and hours (12.2B total impact)
  - emission/water: Water consumption and withdrawal (25M total impact) 
  - natural_resource/energy: Energy use in TJ (3.7M total impact)
  - natural_resource/land: Land use in km2 (563K total impact)
  - natural_resource/in_ground: Material extraction in kt (391M total impact)
- **Detailed resource types**: Specific impact categories:
  - **Employment**: People (61M impact) and Hours (12.2B impact)
  - **Water**: Consumption (14.6M Mm3) and Withdrawal (10.1M Mm3)
  - **Energy**: Total energy use (3.7M TJ)
  - **Land**: Cropland (365K km2), Forest (19M km2), Pastures (164K km2)
  - **Materials**: Crops (86M kt), Metals (99M kt), Minerals (89M kt), Fossil fuels (62M kt)
- **Unit aggregations**: Total impacts by physical units (Mm3, TJ, km2, kt, people, hours)
- **resource_intensity**: Total resource impact per million USD of trade
- **500 trade flows** with comprehensive resource impact data across all 6 environmental contexts

## Factor Selection Logic

The trade_factors_lg.csv contains \~40 factors selected from the full 721 available factors using pattern matching on factor names. The selection process:

1. **Target factors**: CO2, CH4, N2O, CO, NOX (major air emissions)
2. **Broad matching**: Used `.str.contains()` which captured variations:
   - CO2: 7 variations (combustion, biogenic, etc.)
   - CH4: 11 variations (agriculture, waste, combustion)
   - NOX: 25 variations (different activity types)
   - CO: 142 matches (overly broad, included CO2 compounds)
3. **Result**: 40 factors covering multiple contexts and emission sources
4. **Industry-specific coefficients**: Energy sectors get higher CO2, agriculture gets higher CH4

This approach provides comprehensive coverage while maintaining manageable data size. Alternative strategies could use exact matching (5 factors) or all factors (721 factors).