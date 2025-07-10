CREATE TABLE IndustryFactor (
    IndustryFactorID SERIAL PRIMARY KEY,
    Sector VARCHAR(255),
    Factor VARCHAR(255),
    Country VARCHAR(255),
    Year INTEGER,
    Value DECIMAL(18,4)  
);
