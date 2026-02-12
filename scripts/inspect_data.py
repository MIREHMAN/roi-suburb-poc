
import pandas as pd
import geopandas as gpd
from pathlib import Path

SEIFA_FILE = Path("abs_data/SEIFA_2021_SAL.xlsx")
G02_GEOPACKAGE = Path(r"C:\Users\ibrah\Downloads\Geopackage_2021_G02_AUST_GDA2020\G02_AUST_GDA2020.gpkg")

results = []

results.append("--- SEIFA Inspection ---")
if SEIFA_FILE.exists():
    df_seifa = pd.read_excel(SEIFA_FILE, sheet_name='Table 1', skiprows=5)
    sal_codes_seifa = df_seifa.iloc[:, 0].dropna().head(10).tolist()
    results.append(f"SEIFA SAL Codes (Raw): {sal_codes_seifa}")
    results.append(f"SEIFA SAL Codes (Types): {[type(x) for x in sal_codes_seifa]}")
else:
    results.append("SEIFA file not found")

results.append("\n--- G02 Inspection ---")
if G02_GEOPACKAGE.exists():
    g02_sal = gpd.read_file(G02_GEOPACKAGE, layer='G02_SAL_2021_AUST', rows=10)
    # Check column names in case they are different
    results.append(f"G02 Columns: {g02_sal.columns.tolist()}")
    if 'SAL_CODE_2021' in g02_sal.columns:
        sal_codes_g02 = g02_sal['SAL_CODE_2021'].head(10).tolist()
        results.append(f"G02 SAL Codes (Raw): {sal_codes_g02}")
        results.append(f"G02 SAL Codes (Types): {[type(x) for x in sal_codes_g02]}")
    else:
        results.append("SAL_CODE_2021 not found in G02")
else:
    results.append("G02 geopackage not found")

with open("scripts/inspection_results.txt", "w") as f:
    f.write("\n".join(results))
