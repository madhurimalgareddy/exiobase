# Primary tables: trade, factor, industry

Table naming designed for 3rd graders:

**The trade_id field** in trade.csv relates 5 values (year, region1, region2, industry1, industry2) to multiple impact factors for each trade row.

**The factor_id field** represents 721 unique impacts applied to each annual trade row (for imports, exports and domestic).

Trade is traditionally called flow, but the term flow lacks clarity when relating annual trade rows to multiple factors.

Later, the 6-character "commodity" sectors can reside in the 5-character "trade" tables, or in tables starting with "commodity".

<!--
### File clean-up ran. This csv output needs to be updated in the .py scripts.

find . -type f -name "factors.csv" -execdir mv {} factor.csv \;
find . -type f -name "industries.csv" -execdir mv {} industry.csv \;
find . -type f -name "industryflow.csv" -execdir mv {} trade.csv \;
find . -type f -name "trade_factors.csv" -execdir mv {} trade_factor.csv \;
find . -type f -name "trade_impacts.csv" -execdir mv {} trade_impact.csv \;
find . -type f -name "trade_resources.csv" -execdir mv {} trade_resource.csv \;
find . -type f -name "trade_materials.csv" -execdir mv {} trade_material.csv \;

find . -type f -name "trade_factors_lite.csv" -delete
find . -type f -name "industryflow_factor.csv" -delete
find . -type f -name "industryflow_finaldemand.csv" -delete

industryflow_factor-DELETE.py, 
If we retain, activate trade_id (was flow_id) and omit the factor_name column
-->

