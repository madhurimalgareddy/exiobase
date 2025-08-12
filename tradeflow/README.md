# Primary tables: trade, factor, industry

Table naming designed for 3rd graders:

**The trade_id field** in trade.csv relates 5 values (year, region1, region2, industry1, industry2) to multiple impact factors for each trade row.

**The factor_id field** represents 721 unique impacts applied to each annual trade row (for imports, exports and domestic).

Trade is traditionally called flow, but the term flow lacks clarity when relating annual trade rows to multiple factors.

Later, the 6-character "commodity" sectors can reside in the 5-character "trade" tables, or in tables starting with "commodity".

## Processing Command

To process the 9 CSV files listed in config.yaml, run the automated batch processing:

```bash
python main.py
```

## Processing Times

| Configuration | trade.py | trade_impact.py | trade_resource.py |
|--------------|----------|----------------|-------------------|
| **2019/US/exports** | **133.7s (2m 14s)**<br>**188,735 trade flows**<br/>125,148 trade factors | **5.3s**<br>**188,735 trade impacts** | **9.0s**<br>**38,935 total rows**<br/>(3,469 employment<br/>28,844 resources<br/>6,622 materials) |

- trade.py: Includes Exiobase download, trade flow extraction, and trade_factor.csv generation
- trade_impact.py: Creates aggregated environmental impact summary (22 columns)
- trade_resource.py: Creates 3 specialized files (employment, resource, material analysis)
- Total processing time: ~2m 30s for 188,735 trade flows
- Well within timeout limits (20 min/script, 60 min/country, 5 hours/batch)

The main.py command generates the following CSV files for each country/tradeflow combination:
- `factor.csv` - Environmental factor definitions (721 factors)
- `industry.csv` - Industry sector mapping  
- `trade.csv` - Core trade flows (trade_id, year, region1, region2, industry1, industry2, amount)
- `trade_factor.csv` - Environmental coefficients (120 selected factors for imports/exports)
- `trade_factor_lg.csv` - All environmental coefficients (721 factors for domestic flows)
- `trade_impact.csv` - Aggregated environmental impacts
- `trade_resource.csv` - Resource use analysis
- `trade_material.csv` - Material flow analysis  
- `trade_employment.csv` - Employment impact analysis

