
import json
from pathlib import Path

notebook_path = Path("combined_suburb_roi_analysis_with_g02.ipynb")

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Define the refined ROI calculation logic
refined_roi_code = [
    "# Calculating REAL ROI (Best Practice)\n",
    "print(\"Calculating Real ROI and refined financial metrics...\")\n",
    "print(\"=\" * 70)\n",
    "\n",
    "# 1. Median Property Price (Estimated via Mortgage back-calculation as Purchase Price)\n",
    "# Formula: Purchase Price = Monthly Repayment / Monthly interest factor (30yr @ 5%) / LVR (80%)\n",
    "monthly_factor = 0.005368  # 5% annual interest over 30 years\n",
    "analysis_data['Median_Property_Price'] = (analysis_data['Median_mortgage_repay_monthly'] / monthly_factor / 0.8)\n",
    "analysis_data['Median_Property_Price'] = analysis_data['Median_Property_Price'].replace(0, np.nan)\n",
    "\n",
    "# 2. Median Weekly Rent\n",
    "analysis_data['Median_Weekly_Rent'] = analysis_data['Median_rent_weekly']\n",
    "analysis_data['Annual_Rent'] = analysis_data['Median_Weekly_Rent'] * 52\n",
    "\n",
    "# 3. Rental Yield % (Gross)\n",
    "analysis_data['Rental_Yield_Pct'] = (analysis_data['Annual_Rent'] / analysis_data['Median_Property_Price'] * 100)\n",
    "\n",
    "# 4. Capital Growth % (Proxy Scale 0-10% based on Socio-Economic factors)\n",
    "analysis_data['Capital_Growth_Pct'] = (\n",
    "    analysis_data['Score_Income'] * 0.4 +\n",
    "    analysis_data['Score_Advantage'] * 0.4 +\n",
    "    normalize_score(analysis_data['Pct_Mortgaged']) * 0.2\n",
    ") / 10\n",
    "\n",
    "# 5. Socio-economic Risk Score (Inverse of Socio-economic Advantage)\n",
    "analysis_data['Socio_Economic_Risk_Score'] = 100 - analysis_data['Score_Advantage']\n",
    "\n",
    "# 6. True ROI (Best Practice Formula)\n",
    "# True_ROI = (Annual Rent - Costs) / Purchase Price\n",
    "# Costs estimate: 20% of Gross Rent for Maintenance, Rates, and Management\n",
    "analysis_data['Annual_Costs'] = analysis_data['Annual_Rent'] * 0.20\n",
    "analysis_data['True_ROI'] = ((analysis_data['Annual_Rent'] - analysis_data['Annual_Costs']) / analysis_data['Median_Property_Price'] * 100)\n",
    "\n",
    "print(\"✓ Real ROI metrics calculated successfully.\")\n"
]

# Define the refined display logic for top suburbs
refined_display_code = [
    "# Identify top investment opportunities based on Real ROI metrics\n",
    "top_n = 50\n",
    "\n",
    "top_suburbs = analysis_data.nlargest(top_n, 'Investment_Potential_Index')[[\n",
    "    'SAL_CODE_2021', 'SAL_NAME_2021_SEIFA',\n",
    "    'True_ROI',\n",
    "    'Median_Property_Price',\n",
    "    'Median_Weekly_Rent',\n",
    "    'Rental_Yield_Pct',\n",
    "    'Capital_Growth_Pct',\n",
    "    'Investment_Potential_Index',\n",
    "    'Socio_Economic_Risk_Score',\n",
    "    'Pct_Rented',\n",
    "    'Median_tot_hhd_inc_weekly',\n",
    "    'Tot_P_P'\n",
    "]].copy()\n",
    "\n",
    "print(f\"Top {top_n} Investment Opportunities (Real ROI Best Practice) - Head 20:\")\n",
    "print(\"=\" * 70)\n",
    "display(top_suburbs.head(20))\n"
]

# Update the summary statistics code
refined_summary_code = [
    "print(\"=\"*70)\n",
    "print(\"INVESTMENT ANALYSIS SUMMARY - FINANCIAL DEPTH\")\n",
    "print(\"=\"*70)\n",
    "print(f\"Total suburbs analyzed: {len(analysis_data):,}\")\n",
    "print(f\"Top opportunities identified: {top_n}\")\n",
    "print(\"-\" * 70)\n",
    "print(\"TOP 50 PERFORMANCE AVERAGES (Best Practice Metrics)\")\n",
    "print(f\"  Avg Property Price:   ${top_suburbs['Median_Property_Price'].mean():,.0f}\")\n",
    "print(f\"  Avg Weekly Rent:      ${top_suburbs['Median_Weekly_Rent'].mean():,.0f}\")\n",
    "print(f\"  Avg Gross Yield:      {top_suburbs['Rental_Yield_Pct'].mean():.2f}%\")\n",
    "print(f\"  Avg Net ROI (True):   {top_suburbs['True_ROI'].mean():.2f}%\")\n",
    "print(f\"  Avg Capital Growth:   {top_suburbs['Capital_Growth_Pct'].mean():.2f}%\")\n",
    "print(\"-\" * 70)\n",
    "print(f\"Top Suburb: {top_suburbs.iloc[0]['SAL_NAME_2021_SEIFA']}\")\n",
    "print(f\"  Index Score: {top_suburbs.iloc[0]['Investment_Potential_Index']:.2f}\")\n",
    "print(f\"  True ROI:    {top_suburbs.iloc[0]['True_ROI']:.2f}%\")\n",
    "print(\"=\"*70)\n"
]

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        content = "".join(cell['source'])
        if 'analysis_data[\'True_ROI\'] =' in content or 'Calculate REAL ROI' in content:
            cell['source'] = [
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
                "analysis_data['Score_Advantage'] = normalize_score(analysis_data['IRSAD_Score'])\n",
                "analysis_data['Score_Education'] = normalize_score(analysis_data['IEO_Score'])\n",
                "analysis_data['Score_Economic'] = normalize_score(analysis_data['IER_Score'])\n",
                "analysis_data['Score_Income'] = normalize_score(analysis_data['Median_tot_hhd_inc_weekly'])\n",
                "analysis_data['Score_Affordability'] = normalize_score(analysis_data['Median_mortgage_repay_monthly'], reverse=True)\n",
                "\n",
                "analysis_data['Investment_Potential_Index'] = (\n",
                "    analysis_data['Score_Advantage'] * 0.15 +\n",
                "    analysis_data['Score_Education'] * 0.15 +\n",
                "    analysis_data['Score_Economic'] * 0.10 +\n",
                "    analysis_data['Score_Income'] * 0.15 +\n",
                "    analysis_data['Score_Affordability'] * 0.10 +\n",
                "    normalize_score(analysis_data['Pct_Rented']) * 0.20 +\n",
                "    normalize_score(analysis_data['Pct_High_Income']) * 0.15\n",
                ")\n",
                "\n"
            ] + refined_roi_code
        elif 'top_suburbs = analysis_data.nlargest' in content:
            cell['source'] = refined_display_code
        elif 'print("INVESTMENT ANALYSIS SUMMARY - FINANCIAL DEPTH")' in content:
            cell['source'] = refined_summary_code

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook updated with Real ROI (Best Practice) metrics and summary statistics.")
