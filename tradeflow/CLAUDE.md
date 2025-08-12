# Annual trade data processing

The following provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Exiobase data processing project that extracts and transforms multiregional input-output (MRIO) data for economic and environmental analysis. The project processes trade flows, industry factors, and environmental impacts from the Exiobase database.

## Architecture

### Core Components

- **config.yaml**: Central configuration for countries, trade flows, processing parameters
- **config_loader.py**: Smart configuration handling with domestic/non-domestic file selection
- **run_smart_batch.py**: Automated batch processing with progress tracking

### Data Flow Architecture

1. **Data Source**: Exiobase v3 database files (parsed using pymrio library)
2. **Core Matrices**:
   - **Z matrix**: Inter-industry flows between regions/sectors
   - **Y matrix**: Final demand  
   - **F matrix**: Environmental extension factors
3. **Processing**: Transform matrices into relational format for database storage
4. **Output**: Structured CSV files with comprehensive environmental impact data

## Development Environment

### Python Environment Setup
```bash
# Create and activate virtual environment
python -m venv env
source env/bin/activate  # macOS/Linux

env\Scripts\activate.bat # PC

# Install required dependencies
pip install pandas numpy pymrio sqlalchemy psycopg2-binary requests pyyaml
```

### Running Scripts

#### Individual Script Execution:
```bash
# Activate environment first
source env/bin/activate

# Run scripts in order
python trade.py # Creates trade_factor.csv
# python industryflow_finaldemand.py # Renamed with -DELETE added
# python industryflow_factor.py # Renamed with -DELETE added
# python create_full_trade_factor.py # trade_factor.csv with environmental impact coefficients
python trade_impact.py
python trade_resource.py
```

#### Automated Batch Processing:
```bash
# Process multiple countries automatically
python run_smart_batch.py

# Update current country manually
python update_current_country.py CN
```

## Configuration Management

### Country List Handling
- **Explicit list**: `COUNTRY: {list: "CN,DE,JP", current: "CN"}`
- **All countries**: `COUNTRY: {list: "all"}` - Auto-discovers existing country folders
- **Default set**: `COUNTRY: {list: "default"}` - Uses predefined 12-country set
- **Auto-population**: Missing `current` field automatically populated during processing
- **Auto-cleanup**: `current` field automatically removed when batch processing completes

### Trade Flow Types
- **imports**: Flows TO the country (from other countries)
- **exports**: Flows FROM the country (to other countries)  
- **domestic**: Flows WITHIN the country (intra-country only)

### File Selection Logic
- **Domestic flows**: Automatically uses `trade_factor_lg.csv` (all 721 factors) if available
- **Import/Export flows**: Uses `trade_factor.csv` (120 selected factors) for performance
- **Smart fallback**: If `_lg` version doesn't exist, falls back to standard version

## Data Processing Patterns

### Exiobase Data Structure
- **Regions**: 44 countries + 5 rest-of-world regions (AT, BE, CN, US, etc.)
- **Industries**: 163 detailed sectors aggregated to \~200 standardized codes
- **Extensions**: Air emissions, employment, energy, land use, materials, water, etc.

### Trade Factors Strategy
- **Domestic Processing**: Uses all 721 factors (`trade_factor_lg.csv`) because:
  - Intra-country trade volumes are smaller than international flows
  - Comprehensive environmental coverage is feasible
  - Processing time remains manageable (\~1-2 minutes)
- **International Processing**: Uses 120 selected factors (`trade_factor.csv`) because:
  - International trade volumes are much larger
  - Performance optimization necessary
  - Key environmental impacts still captured

## File Path Conventions

- **Exiobase data**: `exiobase_data/IOT_{year}_pxp.zip`
- **Country outputs**: `year/{year}/{country}/{tradeflow}/`
- **Reference files**: `year/{year}/industry.csv`, `year/{year}/factor.csv`
- **Run documentation**: `runnote.md` (overwritten after each full run)

## Progress Tracking System

### Run Notes
- **runnote-inprogress.md**: Created during processing, tracks progress and timing
- **runnote.md**: Final summary created after successful completion, overwrites previous
- **Auto-cleanup**: Progress file deleted after creating final summary

### Key Information Tracked
- Trade factors file used (`trade_factor.csv` vs `trade_factor_lg.csv`)
- Processing timestamps and duration
- File generation summary
- Environmental impact coverage details

## Output Files Structure

### Core Trade Data
- **trade.csv**: `trade_id, year, region1, region2, industry1, industry2, amount`
<!--
- **industryflow_finaldemand.csv**: Final demand flows (Y matrix data)
- **industryflow_factor.csv**: Environmental coefficients (F matrix data)
-->

### Environmental Impact Data  
- **trade_factor.csv**: Selected factors for imports/exports (120 factors)
- **trade_factor_lg.csv**: All factors for domestic flows (721 factors)
- **trade_impact.csv**: Comprehensive impact summary per trade transaction
- **trade_employment.csv**: Employment impact analysis
- **trade_resource.csv**: Resource use analysis (water, energy, land)
- **trade_material.csv**: Material flow analysis

### Reference Files
- **industry.csv**: Sector mapping with standardized 5-character codes
- **factor.csv**: Environmental factor definitions with units and contexts

## Key Libraries

- **pymrio**: Primary library for parsing Exiobase data files
- **pandas**: Data manipulation and transformation
- **numpy**: Numerical computations and coefficient generation
- **pathlib**: Modern file path handling
- **yaml**: Configuration file management

## Performance Optimizations

- **Domestic flows**: All 721 factors (comprehensive analysis feasible)
- **International flows**: 120 selected factors (performance-optimized)
- **Smart file selection**: Automatic `_lg` vs standard file detection
- **Batch processing**: Multi-level timeout protection with automatic progression
- **Memory management**: Chunked processing for large datasets
- **Resume functionality**: Automatically skips already completed countries

## Timeout Configuration

The system implements a three-tier timeout hierarchy for robust processing management:

1. **Script timeout**: 20 minutes per individual script
   - Prevents any single script from hanging indefinitely
   - Applies to each of the 6 processing scripts per country
   - Most granular level of timeout protection

2. **Country timeout**: 60 minutes per country total
   - Limits total processing time for all scripts in a single country
   - Provides real-time countdown: "Country time remaining: X.X minutes"
   - Prevents any country from consuming excessive batch time

3. **Batch timeout**: 5 hours for entire batch
   - Overall time limit for processing all countries in the list
   - Shows remaining batch time: "Batch time remaining: X.X hours"
   - Most restrictive timeout - will stop processing when reached

**Timeout Priority**: The most restrictive timeout wins. If any timeout is exceeded, processing stops gracefully with clear status reporting.

## Best Practices

1. **Always run scripts in the specified order** (dependencies matter)
2. **Use batch processing** for multiple countries (run_smart_batch.py)
3. **Check runnote.md** for processing details and file usage
4. **Domestic flows**: Expect longer processing times but comprehensive coverage
5. **International flows**: Optimized for performance with key environmental impacts

## Processing Pipeline (CSV Generation Order)

The scripts are run in this specific order to ensure proper data dependencies:

create\_full_trade_factor.py

    create_full_trade_factor.py

### 1. **trade.py** - Core Trade Flow Extraction
- **Input**: Exiobase Z-matrix (inter-industry flows)
- **Output**: `industry.csv`,`factor.csv`, trade_factor.csv`, `trade_factor_lg.csv` - Main trade flow data
- **Purpose**: Extracts trade flows based on config (imports/exports/domestic)
- **Key Feature**: For domestic flows, extracts intra-country flows (country→same country)
- **Processing time**: \~2-3 minutes per country

<!--
### 2. **industryflow_finaldemand.py** - Final Demand Flows  
- **Input**: Exiobase Y-matrix (final demand)
- **Output**: `industryflow_finaldemand.csv`
- **Purpose**: Captures final consumption, government spending, investment
- **Processing time**: \~1-2 minutes per country

### 3. **industryflow_factor.py** - Environmental Factor Coefficients
- **Input**: Exiobase F-matrices (environmental extensions)
- **Output**: `industryflow_factor.csv` 
- **Purpose**: Extracts environmental intensity coefficients per industry
- **Processing time**: \~1-2 minutes per country

### 4. **create\_full_trade_factor.py** - Environmental Impact Coefficients
- **Input**: `trade.csv` + `factor.csv`
- **Output**: 
  - **Domestic**: Both `trade_factor.csv` (120 factors) AND `trade_factor_lg.csv` (721 factors)
  - **Imports/Exports**: Only `trade_factor.csv` (120 factors)
- **Purpose**: Links trade flows to environmental impacts
- **Key Innovation**: Domestic flows use `_lg` version since intra-country volumes are smaller
- **Processing time**: \~1-2 minutes per country
-->

### 5. **trade_impact.py** - Aggregated Environmental Impacts
- **Input**: `trade_factor_lg.csv` (domestic) or `trade_factor.csv` (others)
- **Output**: `trade_impact.csv`
- **Purpose**: Comprehensive environmental impact summary per trade transaction
- **Processing time**: \~10-15 seconds per country

### 6. **trade_resource.py** - Resource Analysis with 3 factor table outputs (for optimal sizes and processing time)
- **Input**: `trade_factor_lg.csv` or `trade_factor.csv`
- **Output**: `trade_employment.csv`, `trade_resource.csv`, `trade_material.csv`
- **Purpose**: Specialized analysis of employment, resources, and materials
- **Processing time**: \~5-15 seconds per country

## Troubleshooting

- **Empty domestic flows**: Check country codes match Exiobase regions exactly
- **Missing trade_factor**: Ensure previous scripts completed successfully  
- **Performance issues**: International flows use optimized factor selection
- **Configuration errors**: Verify COUNTRY structure and current field population