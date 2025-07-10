import pymrio
import pandas as pd


year = 2013

base_exio_path = "H:\Exiobase Unzipped\IOT_"
exio_path = base_exio_path + str(year) + "_pxp"
countries_path = r"C:\Users\garma\Downloads\exio_country_names.csv"



#exio_model.calc_all()

exio_model = pymrio.parse_exiobase3(exio_path)




regions = exio_model.get_regions()
Z = exio_model.Z
Y = exio_model.Y

# Build a list of dicts
data_list = []

for i in regions:
    Z_i = Z.loc[(i, slice(None)), :]
    Y_i = Y.loc[(i, slice(None)), :]
    for j in regions:
        Z_ij = Z_i.loc[:, (j, slice(None))].sum().sum()
        Y_ij = Y_i.loc[:, (j, slice(None))].sum().sum()
        total_exports_ij = Z_ij + Y_ij
        data_list.append({
            "region1": i,
            "region2": j,
            "value": total_exports_ij
        })

# Convert to a DataFrame in "long" (relational) format already
df_relational = pd.DataFrame(data_list)




# Load the CSV file containing country names
file_path = r"C:\Users\garma\Downloads\exio_country_names.csv"

df_country_names = pd.read_csv(file_path)

# Rename columns for clarity
df_country_names.rename(columns={"CountryCode": "region_short", "Country": "region_full"}, inplace=True)

# Load your existing df_relational (Ensure this DataFrame is created before running the script)
# Example:
# df_relational = pd.DataFrame([...])  # Your existing DataFrame

# Join with df_relational to replace `region1`
df_relational = df_relational.merge(df_country_names, left_on="region1", right_on="region_short", how="left")
df_relational.drop(columns=["region1", "region_short"], inplace=True)
df_relational.rename(columns={"region_full": "region1"}, inplace=True)

# Join with df_relational to replace `region2`
df_relational = df_relational.merge(df_country_names, left_on="region2", right_on="region_short", how="left")
df_relational.drop(columns=["region2", "region_short"], inplace=True)
df_relational.rename(columns={"region_full": "importing_country","region1":"exporting_country" }, inplace=True)

# Display updated DataFrame
print(df_relational.head())


