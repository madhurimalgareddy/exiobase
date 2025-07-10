CREATE TABLE IndustryFactor(
	IndustryFactorID int IDENTITY PRIMARY KEY NOT NULL,
	Sector nvarchar(255) NULL,
	Factor nvarchar(255) NULL,
	Country nvarchar(255) NULL,
	Year int NOT NULL,
	Value float NOT NULL

)