
import pandas as pd
from pathlib import Path

# Paths
SEIFA_FILE = Path("abs_data/SEIFA_2021_SAL.xlsx")
DATAPACK_DIR = Path(r"abs_data/census_2021_datapack_sal/Australia/2021 Census GCP Suburbs and Localities for AUS")

print("--- Verification of DataPacks Integration ---")

def test_load():
    # Load SEIFA Sample
    seifa = pd.read_excel(SEIFA_FILE, sheet_name='Table 1', skiprows=5)
    seifa.columns = ['SAL_CODE_2021', 'SAL_NAME_2021', 'IRSD_Score', 'IRSD_Decile', 'IRSAD_Score', 'IRSAD_Decile', 'IER_Score', 'IER_Decile', 'IEO_Score', 'IEO_Decile', 'Usual_Resident_Population']
    seifa = seifa[pd.to_numeric(seifa['SAL_CODE_2021'], errors='coerce').notna()]
    seifa['SAL_CODE_2021_str'] = seifa['SAL_CODE_2021'].astype(int).astype(str)

    # Load G37 (Tenure) Sample
    g37_path = DATAPACK_DIR / "2021Census_G37_AUST_SAL.csv"
    if not g37_path.exists():
        print(f"✗ G37 not found at {g37_path}")
        return
    
    g37 = pd.read_csv(g37_path, nrows=100)
    g37['SAL_CODE_2021_clean'] = g37['SAL_CODE_2021'].astype(str).str.replace('SAL', '', regex=False).str.strip()
    
    # Merge
    merged = seifa.merge(g37, left_on='SAL_CODE_2021_str', right_on='SAL_CODE_2021_clean', how='inner')
    
    print(f"Merge Match Success (Sample 100): {len(merged)}")
    if len(merged) > 0:
        print("✓ DataPack merge normalization works!")
        # Test calculation
        merged['Pct_Rented'] = (merged['R_Tot_Total'] / merged['Total_Total'] * 100).fillna(0)
        print(f"Sample Pct_Rented range: {merged['Pct_Rented'].min():.2f}% - {merged['Pct_Rented'].max():.2f}%")
        print("✓ Derived calculations work!")
    else:
        print("✗ Merge failed.")

test_load()
