# trade, factor, industry

trade_id in trade.csv allows 5 values (year,region1,region2,industry1,industry2) to be related to multiple factors.  Trade is traditionally called flow, but flow causes confusion by failing to convey to new users that the same flowid is used for multiple factors.

At a later point the 6-char sectors can either reside in the 5-char "trade" tables, or in a new parallel structure called "commodity".
