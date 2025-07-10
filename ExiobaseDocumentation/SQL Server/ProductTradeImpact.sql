CREATE TABLE ProductTradeImpact (
    TradeImpactID INT IDENTITY(1,1) PRIMARY KEY,
    ProductCategory NVARCHAR(64),        -- e.g., 'Plastics, basic'
    ImpactCategory NVARCHAR(64),               -- e.g., 'Carbon', 'EUR', 'Land'
    ImpactValue DECIMAL(15,2),                          -- e.g., -100000.0
    Unit NVARCHAR(20),                    -- e.g., 'kg', 'EUR', 'km²'
    Year INT,                             -- e.g., 2021
    Factor VARCHAR(64),          -- air emissions

    FromCountry NVARCHAR(64),              -- Optional, if available
    ToCountry NVARCHAR(64)              -- Optional, if available
);
