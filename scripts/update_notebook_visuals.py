
import json
from pathlib import Path

notebook_path = Path("combined_suburb_roi_analysis_with_g02.ipynb")

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Update Section 10 (Display Columns)
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and 'top_suburbs = analysis_data.nlargest' in "".join(cell['source']):
        source = cell['source']
        # Find where the list of columns starts
        found_cols = False
        for j, line in enumerate(source):
            if "'SAL_NAME_2021_SEIFA'" in line:
                # Insert new columns after this
                source.insert(j+1, "    'ROI_Score',\n")
                source.insert(j+2, "    'Pct_Rented', 'Pct_High_Income', 'Tot_P_P',\n")
                found_cols = True
                break
        if found_cols:
            break

# 2. Update Section 11 (Visualizations)
visual_cell_idx = -1
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and 'fig, axes = plt.subplots(2, 2' in "".join(cell['source']):
        visual_cell_idx = i
        break

if visual_cell_idx != -1:
    new_visual_source = [
        "# ROI Analysis - Comprehensive Visualizations\n",
        "fig, axes = plt.subplots(3, 2, figsize=(18, 18))\n",
        "\n",
        "# 1. ROI Score Distribution\n",
        "axes[0, 0].hist(analysis_data['ROI_Score'], bins=50, edgecolor='black', alpha=0.7, color='steelblue')\n",
        "axes[0, 0].set_title('Distribution of ROI Scores', fontsize=16, fontweight='bold')\n",
        "axes[0, 0].set_xlabel('ROI Score')\n",
        "axes[0, 0].set_ylabel('Number of Suburbs')\n",
        "axes[0, 0].axvline(analysis_data['ROI_Score'].median(), color='red', linestyle='--', label=f'Median: {analysis_data[\"ROI_Score\"].median():.1f}')\n",
        "axes[0, 0].legend()\n",
        "\n",
        "# 2. Rental Density vs ROI Score\n",
        "sns.regplot(data=analysis_data, x='Pct_Rented', y='ROI_Score', ax=axes[0, 1], \n",
        "            scatter_kws={'alpha':0.4, 's':10}, line_kws={'color':'red'})\n",
        "axes[0, 1].set_title('Rental Density (%) vs ROI Score', fontsize=16, fontweight='bold')\n",
        "axes[0, 1].set_xlabel('Percentage of Rented Dwellings')\n",
        "axes[0, 1].set_ylabel('ROI Score')\n",
        "\n",
        "# 3. High Income vs ROI Score\n",
        "sns.regplot(data=analysis_data, x='Pct_High_Income', y='ROI_Score', ax=axes[1, 0], \n",
        "            color='green', scatter_kws={'alpha':0.4, 's':10}, line_kws={'color':'red'})\n",
        "axes[1, 0].set_title('High Income Households (%) vs ROI Score', fontsize=16, fontweight='bold')\n",
        "axes[1, 0].set_xlabel('Percentage of High Income Households (>$3k/wk)')\n",
        "axes[1, 0].set_ylabel('ROI Score')\n",
        "\n",
        "# 4. Mortgage Stress/Repayment vs ROI Score\n",
        "axes[1, 1].scatter(analysis_data['Median_mortgage_repay_monthly'], \n",
        "                   analysis_data['ROI_Score'], alpha=0.4, s=10, color='orange')\n",
        "axes[1, 1].set_title('Monthly Mortgage vs ROI Score', fontsize=16, fontweight='bold')\n",
        "axes[1, 1].set_xlabel('Median Monthly Mortgage Repayment ($)')\n",
        "axes[1, 1].set_ylabel('ROI Score')\n",
        "\n",
        "# 5. Population vs ROI Score\n",
        "axes[2, 0].scatter(analysis_data['Tot_P_P'], \n",
        "                   analysis_data['ROI_Score'], alpha=0.3, s=10, color='purple')\n",
        "axes[2, 0].set_xscale('log')\n",
        "axes[2, 0].set_title('Population (Log Scale) vs ROI Score', fontsize=16, fontweight='bold')\n",
        "axes[2, 0].set_xlabel('Total Population')\n",
        "axes[2, 0].set_ylabel('ROI Score')\n",
        "\n",
        "# 6. Household Income vs ROI Score\n",
        "axes[2, 1].scatter(analysis_data['Median_tot_hhd_inc_weekly'], \n",
        "                   analysis_data['ROI_Score'], alpha=0.4, s=10, color='brown')\n",
        "axes[2, 1].set_title('Household Income vs ROI Score', fontsize=16, fontweight='bold')\n",
        "axes[2, 1].set_xlabel('Median Weekly Household Income ($)')\n",
        "axes[2, 1].set_ylabel('ROI Score')\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()"
    ]
    nb['cells'][visual_cell_idx]['source'] = new_visual_source

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook visualisations and table columns updated.")
