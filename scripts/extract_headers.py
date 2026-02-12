
import pandas as pd
import json

files = ['G01', 'G32', 'G33', 'G37', 'G40']
base_path = r'abs_data\census_2021_datapack_sal\Australia\2021 Census GCP Suburbs and Localities for AUS\2021Census_{}_AUST_SAL.csv'

results = {}

for f in files:
    path = base_path.format(f)
    try:
        df = pd.read_csv(path, nrows=0)
        results[f] = df.columns.tolist()
    except Exception as e:
        results[f] = f"Error: {str(e)}"

with open('scripts/datapack_columns.json', 'w') as f:
    json.dump(results, f, indent=4)

print("Column extraction complete. Results saved to scripts/datapack_columns.json")
