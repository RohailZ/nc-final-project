import pandas as pd
df = pd.read_parquet("address.parquet")
df = df.rename(columns={'address_id': 'location_id'})
print(df.to_string())