# Removed from main.py output process

### 2. **industryflow_finaldemand.py** - Final Demand Flows - Removed from main.py  
- **Input**: Exiobase Y-matrix (final demand)
- **Output**: `industryflow_finaldemand.csv`
- **Purpose**: Captures final consumption, government spending, investment
- **Processing time**: \~1-2 minutes per country

### 3. **industryflow_factor.py** - Environmental Factor Coefficients
- **Input**: Exiobase F-matrices (environmental extensions)
- **Output**: `industryflow_factor.csv`  Environmental coefficients (F matrix data)
- **Purpose**: Extracts environmental intensity coefficients per industry
- **Processing time**: \~1-2 minutes per country

### 4. **create_full_trade_factor.py** - Environmental Impact Coefficients
- **Input**: `trade.csv` + `factor.csv`
- **Output**: 
  - **Domestic**: Both `trade_factor.csv` (120 factors) AND `trade_factor_lg.csv` (721 factors)
  - **Imports/Exports**: Only `trade_factor.csv` (120 factors)
- **Purpose**: Links trade flows to environmental impacts
- **Key Innovation**: Domestic flows use `_lg` version since intra-country volumes are smaller
- **Processing time**: \~1-2 minutes per country

