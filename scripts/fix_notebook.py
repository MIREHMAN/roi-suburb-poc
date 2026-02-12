
import json
from pathlib import Path

notebook_path = Path("combined_suburb_roi_analysis_with_g02.ipynb")

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The cell we want to modify is the one starting with "# Prepare G02 data for merging"
target_start = "# Prepare G02 data for merging"
new_source = [
    "# Prepare G02 data for merging (drop geometry for now, keep key demographic columns)\n",
    "g02_data = g02_sal.drop(columns=['geometry']).copy()\n",
    "\n",
    "# Normalize SAL_CODE by removing 'SAL' prefix if present and converting to string\n",
    "g02_data['SAL_CODE_2021_clean'] = g02_data['SAL_CODE_2021'].astype(str).str.replace('SAL', '', regex=False).str.strip()\n",
    "seifa['SAL_CODE_2021_str'] = seifa['SAL_CODE_2021'].astype(str).str.strip()\n",
    "\n",
    "# Merge SEIFA with G02 data\n",
    "print(\"Merging SEIFA and G02 data...\")\n",
    "print(\"=\" * 70)\n",
    "\n",
    "combined_data = seifa.merge(\n",
    "    g02_data,\n",
    "    left_on='SAL_CODE_2021_str',\n",
    "    right_on='SAL_CODE_2021_clean',\n",
    "    how='left',\n",
    "    suffixes=('_SEIFA', '_G02')\n",
    ")\n",
    "\n",
    "# Clean up duplicate columns\n",
    "combined_data = combined_data.drop(columns=['SAL_CODE_2021_str', 'SAL_CODE_2021_clean', 'SAL_CODE_2021_G02'], errors='ignore')\n",
    "combined_data = combined_data.rename(columns={'SAL_CODE_2021_SEIFA': 'SAL_CODE_2021'})\n",
    "\n",
    "print(f\"✓ Combined dataset created with {len(combined_data):,} suburbs\")\n",
    "print(f\"✓ Total columns: {len(combined_data.columns)}\")\n",
    "\n",
    "# Check merge success\n",
    "merge_success = combined_data['Median_age_persons'].notna().sum()\n",
    "print(f\"✓ Successfully matched {merge_success:,} suburbs with G02 data ({merge_success/len(combined_data)*100:.1f}%)\")"
]

found = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and len(cell['source']) > 0 and target_start in cell['source'][0]:
        cell['source'] = new_source
        found = True
        break

if found:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Successfully updated the notebook cell.")
else:
    print("Could not find the target cell in the notebook.")
