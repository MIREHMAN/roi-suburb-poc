
import pandas as pd
import geopandas as gpd
from pathlib import Path

SEIFA_FILE = Path("abs_data/SEIFA_2021_SAL.xlsx")
G02_GEOPACKAGE = Path(r"C:\Users\ibrah\Downloads\Geopackage_2021_G02_AUST_GDA2020\G02_AUST_GDA2020.gpkg")

print("--- Verification ---")
if SEIFA_FILE.exists() and G02_GEOPACKAGE.exists():
    # Load SEIFA
    seifa = pd.read_excel(SEIFA_FILE, sheet_name='Table 1', skiprows=5)
    seifa.columns = ['SAL_CODE_2021', 'SAL_NAME_2021', 'IRSD_Score', 'IRSD_Decile', 'IRSAD_Score', 'IRSAD_Decile', 'IER_Score', 'IER_Decile', 'IEO_Score', 'IEO_Decile', 'Usual_Resident_Population']
    seifa = seifa[pd.to_numeric(seifa['SAL_CODE_2021'], errors='coerce').notna()]
    seifa['SAL_CODE_2021'] = seifa['SAL_CODE_2021'].astype(int)
    
    # Load G02 (just a sample)
    g02_sal = gpd.read_file(G02_GEOPACKAGE, layer='G02_SAL_2021_AUST', rows=100)
    
    # Normalize and Merge
    g02_data = g02_sal.drop(columns=['geometry']).copy()
    g02_data['SAL_CODE_2021_clean'] = g02_data['SAL_CODE_2021'].astype(str).str.replace('SAL', '', regex=False).str.strip()
    seifa['SAL_CODE_2021_str'] = seifa['SAL_CODE_2021'].astype(str).str.strip()
    
    combined = seifa.merge(g02_data, left_on='SAL_CODE_2021_str', right_on='SAL_CODE_2021_clean', how='inner')
    
    print(f"Match success for sample of 100 G02 rows: {len(combined)}")
    if len(combined) > 0:
        print("✓ Merge successful with normalized codes!")
    else:
        print("✗ Merge still failed.")
else:
    print("Files not found for verification.")
