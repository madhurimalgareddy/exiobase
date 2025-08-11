# Trade flow processing

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
python industryflow.py
python industryflow_finaldemand.py  
python industryflow_factor.py
python create_full_trade_factors.py
python create_trade_impacts.py
python trade_resources.py
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
- **Domestic flows**: Automatically uses `trade_factors_lg.csv` (all 721 factors) if available
- **Import/Export flows**: Uses `trade_factors.csv` (120 selected factors) for performance
- **Smart fallback**: If `_lg` version doesn't exist, falls back to standard version

## Data Processing Patterns

### Exiobase Data Structure
- **Regions**: 44 countries + 5 rest-of-world regions (AT, BE, CN, US, etc.)
- **Industries**: 163 detailed sectors aggregated to \~200 standardized codes
- **Extensions**: Air emissions, employment, energy, land use, materials, water, etc.

### Trade Factors Strategy
- **Domestic Processing**: Uses all 721 factors (`trade_factors_lg.csv`) because:
  - Intra-country trade volumes are smaller than international flows
  - Comprehensive environmental coverage is feasible
  - Processing time remains manageable (\~1-2 minutes)
- **International Processing**: Uses 120 selected factors (`trade_factors.csv`) because:
  - International trade volumes are much larger
  - Performance optimization necessary
  - Key environmental impacts still captured

## File Path Conventions

- **Exiobase data**: `exiobase_data/IOT_{year}_pxp.zip`
- **Country outputs**: `year/{year}/{country}/{tradeflow}/`
- **Reference files**: `year/{year}/industries.csv`, `year/{year}/factors.csv`
- **Run documentation**: `runnote.md` (overwritten after each full run)

## Progress Tracking System

### Run Notes
- **runnote-inprogress.md**: Created during processing, tracks progress and timing
- **runnote.md**: Final summary created after successful completion, overwrites previous
- **Auto-cleanup**: Progress file deleted after creating final summary

### Key Information Tracked
- Trade factors file used (`trade_factors.csv` vs `trade_factors_lg.csv`)
- Processing timestamps and duration
- File generation summary
- Environmental impact coverage details

## Output Files Structure

### Core Trade Data
- **industryflow.csv**: `trade_id, year, region1, region2, industry1, industry2, amount`
- **industryflow_finaldemand.csv**: Final demand flows (Y matrix data)
- **industryflow_factor.csv**: Environmental coefficients (F matrix data)

### Environmental Impact Data  
- **trade_factors.csv**: Selected factors for imports/exports (120 factors)
- **trade_factors_lg.csv**: All factors for domestic flows (721 factors)
- **trade_impacts.csv**: Comprehensive impact summary per trade transaction
- **trade_employment.csv**: Employment impact analysis
- **trade_resources.csv**: Resource use analysis (water, energy, land)
- **trade_materials.csv**: Material flow analysis

### Reference Files
- **industries.csv**: Sector mapping with standardized 5-character codes
- **factors.csv**: Environmental factor definitions with units and contexts

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
- **Batch processing**: 20-minute timeout per country with automatic progression
- **Memory management**: Chunked processing for large datasets

## Best Practices

1. **Always run scripts in the specified order** (dependencies matter)
2. **Use batch processing** for multiple countries (run_smart_batch.py)
3. **Check runnote.md** for processing details and file usage
4. **Domestic flows**: Expect longer processing times but comprehensive coverage
5. **International flows**: Optimized for performance with key environmental impacts

## Processing Pipeline (CSV Generation Order)

The scripts are run in this specific order to ensure proper data dependencies:

create\_full_trade_factors.py

    create_full_trade_factors.py

### 1. **industryflow.py** - Core Trade Flow Extraction
- **Input**: Exiobase Z-matrix (inter-industry flows)
- **Output**: `industryflow.csv` - Main trade flow data
- **Purpose**: Extracts trade flows based on config (imports/exports/domestic)
- **Key Feature**: For domestic flows, extracts intra-country flows (country→same country)
- **Processing time**: \~2-3 minutes per country

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

### 4. **create\_full_trade_factors.py** - Environmental Impact Coefficients
- **Input**: `industryflow.csv` + `factors.csv`
- **Output**: 
  - **Domestic**: Both `trade_factors.csv` (120 factors) AND `trade_factors_lg.csv` (721 factors)
  - **Imports/Exports**: Only `trade_factors.csv` (120 factors)
- **Purpose**: Links trade flows to environmental impacts
- **Key Innovation**: Domestic flows use `_lg` version since intra-country volumes are smaller
- **Processing time**: \~1-2 minutes per country

### 5. **create_trade_impacts.py** - Aggregated Environmental Impacts
- **Input**: `industryflow.csv` + `trade_factors_lg.csv` (domestic) or `trade_factors.csv` (others)
- **Output**: `trade_impacts.csv`
- **Purpose**: Comprehensive environmental impact summary per trade transaction
- **Processing time**: \~10-15 seconds per country

### 6. **trade_resources.py** - Resource Analysis
- **Input**: `trade_factors_lg.csv` or `trade_factors.csv`
- **Output**: `trade_employment.csv`, `trade_resources.csv`, `trade_materials.csv`
- **Purpose**: Specialized analysis of employment, resources, and materials
- **Processing time**: \~5-15 seconds per country

## Troubleshooting

- **Empty domestic flows**: Check country codes match Exiobase regions exactly
- **Missing trade_factors**: Ensure previous scripts completed successfully  
- **Performance issues**: International flows use optimized factor selection
- **Configuration errors**: Verify COUNTRY structure and current field population