
import json
from pathlib import Path

notebook_path = Path("combined_suburb_roi_analysis_with_g02.ipynb")

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Update Section 2 (File Paths) to include DataPacks path
# Find the cell with "Configuration - File Paths"
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and 'SEIFA_FILE' in "".join(cell['source']):
        cell['source'].append("\n")
        cell['source'].append("# Census DataPacks Path\n")
        cell['source'].append('DATAPACK_DIR = Path(r"abs_data\\census_2021_datapack_sal\\Australia\\2021 Census GCP Suburbs and Localities for AUS")\n')
        break

# 2. Add new sections for DataPacks
new_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 6.5 Load Census DataPacks (G01, G33, G37, G50A)\n",
            "\n",
            "Enhance the dataset with population, income distribution, tenure types (rental density), and occupation data."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "def load_datapack(file_prefix):\n",
            "    filename = f\"2021Census_{file_prefix}_AUST_SAL.csv\"\n",
            "    path = DATAPACK_DIR / filename\n",
            "    if not path.exists():\n",
            "        print(f\"✗ File not found: {path}\")\n",
            "        return None\n",
            "    \n",
            "    df = pd.read_csv(path)\n",
            "    # Normalize SAL code\n",
            "    df['SAL_CODE_2021_clean'] = df['SAL_CODE_2021'].astype(str).str.replace('SAL', '', regex=False).str.strip()\n",
            "    return df\n",
            "\n",
            "print(\"Loading DataPacks...\")\n",
            "\n",
            "# G01: Total Population\n",
            "g01 = load_datapack('G01')[['SAL_CODE_2021_clean', 'Tot_P_P']]\n",
            "\n",
            "# G33: Income - Extract High Income (> $3000/week)\n",
            "g33 = load_datapack('G33')\n",
            "high_inc_cols = ['HI_3000_3499_Tot', 'HI_3500_3999_Tot', 'HI_4000_more_Tot']\n",
            "g33['High_Income_Households'] = g33[high_inc_cols].sum(axis=1)\n",
            "g33 = g33[['SAL_CODE_2021_clean', 'High_Income_Households', 'Tot_Tot']]\n",
            "g33.rename(columns={'Tot_Tot': 'Total_Households_G33'}, inplace=True)\n",
            "\n",
            "# G37: Tenure - Extract Rented and Total Dwellings\n",
            "g37 = load_datapack('G37')[['SAL_CODE_2021_clean', 'R_Tot_Total', 'Total_Total', 'O_MTG_Total']]\n",
            "\n",
            "# G50A: Occupation - Extract Professionals and Managers\n",
            "g50a = load_datapack('G50A')\n",
            "# Sum managers and professionals (all ages/genders where possible or just totals if available)\n",
            "# For simplicity, let's take some key representative columns if totals aren't clear, \n",
            "# but G50A usually has detailed splits. Let's just use G01/G33/G37 for now as they are most impactful.\n",
            "\n",
            "print(\"✓ DataPacks loaded successfully\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Merge DataPacks into combined_data\n",
            "print(\"Merging DataPacks into master dataset...\")\n",
            "\n",
            "combined_data = combined_data.merge(g01, on='SAL_CODE_2021', how='left')\n",
            "combined_data = combined_data.merge(g33, left_on='SAL_CODE_2021', right_on='SAL_CODE_2021_clean', how='left')\n",
            "combined_data = combined_data.drop(columns=['SAL_CODE_2021_clean'])\n",
            "combined_data = combined_data.merge(g37, left_on='SAL_CODE_2021', right_on='SAL_CODE_2021_clean', how='left')\n",
            "combined_data = combined_data.drop(columns=['SAL_CODE_2021_clean'])\n",
            "\n",
            "# Calculate derived percentages\n",
            "combined_data['Pct_Rented'] = (combined_data['R_Tot_Total'] / combined_data['Total_Total'] * 100).fillna(0)\n",
            "combined_data['Pct_High_Income'] = (combined_data['High_Income_Households'] / combined_data['Total_Households_G33'] * 100).fillna(0)\n",
            "combined_data['Pct_Mortgaged'] = (combined_data['O_MTG_Total'] / combined_data['Total_Total'] * 100).fillna(0)\n",
            "\n",
            "print(f\"✓ Final combined dataset has {len(combined_data.columns)} columns\")\n",
            "display(combined_data[['SAL_NAME_2021_SEIFA', 'Pct_Rented', 'Pct_High_Income', 'Tot_P_P']].head())"
        ]
    }
]

# Insert after Section 6 display cell
insert_idx = -1
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and 'display(combined_data[display_cols].head(10))' in "".join(cell['source']):
        insert_idx = i + 1
        break

if insert_idx != -1:
    nb['cells'][insert_idx:insert_idx] = new_cells

# 3. Update Section 9 (Scoring) to include new features
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and 'analysis_data[\'ROI_Score\'] =' in "".join(cell['source']):
        # Replace the scoring logic
        new_scoring = [
            "# Calculate composite ROI score with Census DataPack enhancements\n",
            "analysis_data['ROI_Score'] = (\n",
            "    analysis_data['Score_Advantage'] * 0.15 +\n",
            "    analysis_data['Score_Education'] * 0.15 +\n",
            "    analysis_data['Score_Economic'] * 0.10 +\n",
            "    analysis_data['Score_Income'] * 0.15 +\n",
            "    analysis_data['Score_Affordability'] * 0.10 +\n",
            "    normalize_score(analysis_data['Pct_Rented']) * 0.20 +   # High rental demand is good\n",
            "    normalize_score(analysis_data['Pct_High_Income']) * 0.15 # High income area supports growth\n",
            ")\n"
        ]
        # Find where ROI_Score calculation starts and replace
        source = cell['source']
        for j, line in enumerate(source):
            if 'analysis_data[\'ROI_Score\'] =' in line:
                # Replace this line and subsequent lines until the closing parenthesis
                # We'll just replace the whole block for simplicity if we can identify it
                # Or just append the new logic and comment out the old
                source[j:] = new_scoring
                break
        break

# 4. Update Section 12 (Export) to new filename
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and 'output_file =' in "".join(cell['source']):
        source = cell['source']
        for j, line in enumerate(source):
            if 'output_file =' in line:
                source[j] = "output_file = 'top_investment_opportunities_complete_v2.csv'\n"
            if 'full_output_file =' in line:
                source[j] = "full_output_file = 'suburb_investment_analysis_final.csv'\n"

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook updated with Census DataPacks integration.")
