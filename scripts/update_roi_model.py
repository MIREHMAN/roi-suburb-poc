
import json
from pathlib import Path

notebook_path = Path("combined_suburb_roi_analysis_with_g02.ipynb")

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Define the new scoring logic
new_scoring_code = [
    "# Calculate normalized scores (0-100 scale)\n",
    "def normalize_score(series, reverse=False):\n",
    "    \"\"\"Normalize a series to 0-100 scale\"\"\"\n",
    "    min_val = series.min()\n",
    "    max_val = series.max()\n",
    "    normalized = ((series - min_val) / (max_val - min_val)) * 100\n",
    "    if reverse:\n",
    "        normalized = 100 - normalized\n",
    "    return normalized\n",
    "\n",
    "# Create scoring components\n",
    "print(\"Calculating Investment Potential Index and REAL ROI...\")\n",
    "print(\"=\" * 70)\n",
    "\n",
    "# SEIFA-based scores (higher is better)\n",
    "analysis_data['Score_Advantage'] = normalize_score(analysis_data['IRSAD_Score'])\n",
    "analysis_data['Score_Education'] = normalize_score(analysis_data['IEO_Score'])\n",
    "analysis_data['Score_Economic'] = normalize_score(analysis_data['IER_Score'])\n",
    "\n",
    "# G02-based scores\n",
    "analysis_data['Score_Income'] = normalize_score(analysis_data['Median_tot_hhd_inc_weekly'])\n",
    "analysis_data['Score_Affordability'] = normalize_score(analysis_data['Median_mortgage_repay_monthly'], reverse=True)\n",
    "\n",
    "# 1. Calculate Investment Potential Index (Old ROI_Score)\n",
    "analysis_data['Investment_Potential_Index'] = (\n",
    "    analysis_data['Score_Advantage'] * 0.15 +\n",
    "    analysis_data['Score_Education'] * 0.15 +\n",
    "    analysis_data['Score_Economic'] * 0.10 +\n",
    "    analysis_data['Score_Income'] * 0.15 +\n",
    "    analysis_data['Score_Affordability'] * 0.10 +\n",
    "    normalize_score(analysis_data['Pct_Rented']) * 0.20 +   # High rental demand is good\n",
    "    normalize_score(analysis_data['Pct_High_Income']) * 0.15 # High income area supports growth\n",
    ")\n",
    "\n",
    "# 2. Calculate REAL ROI (Financial ROI)\n",
    "# Estimate Property Price from Median mortgage repayment (Proxy)\n",
    "# Formula: Monthly Repayment / Monthly interest factor (30yr @ 5%) / LVR (80%)\n",
    "monthly_factor = 0.005368  # 5% annual interest over 30 years\n",
    "analysis_data['Estimated_Property_Price'] = (analysis_data['Median_mortgage_repay_monthly'] / monthly_factor / 0.8).replace(0, np.nan)\n",
    "\n",
    "# Calculate Annual Rent\n",
    "analysis_data['Annual_Rent'] = analysis_data['Median_rent_weekly'] * 52\n",
    "\n",
    "# Estimate Annual Costs (Management, Rates, Maintenance ~20% of gross rent)\n",
    "analysis_data['Estimated_Annual_Costs'] = analysis_data['Annual_Rent'] * 0.20\n",
    "\n",
    "# True ROI (Net Rental Yield)\n",
    "analysis_data['True_ROI'] = ((analysis_data['Annual_Rent'] - analysis_data['Estimated_Annual_Costs']) / analysis_data['Estimated_Property_Price'] * 100)\n",
    "\n",
    "# Gross Rental Yield\n",
    "analysis_data['Rental_Yield'] = (analysis_data['Annual_Rent'] / analysis_data['Estimated_Property_Price'] * 100)\n",
    "\n",
    "# Socio-economic Risk Score (Inverse of Advantage)\n",
    "analysis_data['Socio_Economic_Risk_Score'] = 100 - analysis_data['Score_Advantage']\n",
    "\n",
    "print(\"✓ Calculations complete.\")\n"
]

# Define the new display logic
new_display_code = [
    "# Identify top investment opportunities based on combined model\n",
    "top_n = 50\n",
    "\n",
    "top_suburbs = analysis_data.nlargest(top_n, 'Investment_Potential_Index')[[\n",
    "    'SAL_CODE_2021', 'SAL_NAME_2021_SEIFA',\n",
    "    'Investment_Potential_Index',\n",
    "    'True_ROI',\n",
    "    'Rental_Yield',\n",
    "    'Estimated_Property_Price',\n",
    "    'Socio_Economic_Risk_Score',\n",
    "    'Pct_Rented', 'Pct_High_Income', 'Tot_P_P',\n",
    "    'IRSAD_Score', 'IRSAD_Decile',\n",
    "    'Median_tot_hhd_inc_weekly',\n",
    "    'Median_mortgage_repay_monthly',\n",
    "    'Median_rent_weekly'\n",
    "]].copy()\n",
    "\n",
    "print(f\"Top {top_n} Investment Opportunities (by Investment Potential Index):\")\n",
    "print(\"=\" * 70)\n",
    "display(top_suburbs.head(20))\n"
]

for cell in nb['cells']:
    if cell['cell_type'] == 'code' and 'analysis_data[\'ROI_Score\'] =' in "".join(cell['source']):
        cell['source'] = new_scoring_code
    elif cell['cell_type'] == 'code' and 'top_suburbs = analysis_data.nlargest' in "".join(cell['source']):
        cell['source'] = new_display_code
    elif cell['cell_type'] == 'markdown' and 'ROI_Score' in "".join(cell['source']):
        cell['source'] = [s.replace('ROI_Score', 'Investment_Potential_Index') for s in cell['source']]
        cell['source'] = [s.replace('ROI score', 'Investment Potential Index') for s in cell['source']]

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook updated with True ROI and Investment Potential Index.")
