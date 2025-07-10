import pandas as pd

import pymrio


year = 2013

base_exio_path = "H:\Exiobase Unzipped\IOT_"
exio_path = base_exio_path + str(year) + "_pxp"
countries_path = r"C:\Users\garma\Downloads\exio_country_names.csv"



#exio_model.calc_all()

exio_model = pymrio.parse_exiobase3(exio_path)




# Step 1: Load the F matrix (e.g., employment)
df = exio_model.air_emissions.F.copy()

# Step 2: Preserve 'stressor' and flatten the rest of the MultiIndex columns
df = df.reset_index()
df.columns = ["stressor"] + [f"{col[0]}|{col[1]}" for col in df.columns[1:]]
# Step 3: Melt the DataFrame to long format
df_melted = df.melt(id_vars="stressor", var_name="region_sector", value_name="value")

# Step 4: Filter out any rows where 'region_sector' doesn't contain a pipe (|)
df_melted = df_melted[df_melted["region_sector"].str.count("\|") == 1]

# Step 5: Split 'region_sector' into 'region' and 'sector'
df_melted[["region", "sector"]] = df_melted["region_sector"].str.split("|", expand=True)

# Step 6: Drop the combined column
df_melted.drop(columns="region_sector", inplace=True)

# Step 7: Reorder columns if needed


df_melted.rename(columns={"stressor": "factor"}, inplace=True)


df_melted['year'] = year

df_melted = df_melted[["region", "sector", "factor", "year", "value"]]


country_names = pd.read_csv(countries_path)


merged_df = country_names.merge(df_melted, left_on='CountryCode', right_on='region', how='inner')
merged_df.drop(columns=["CountryCode","region"], inplace=True)
merged_df.rename(columns={"Country": "country"}, inplace=True)

industry_factor = merged_df

industry_factor
