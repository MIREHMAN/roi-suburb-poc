
import json

nb_path = r"c:\Users\ibrah\OneDrive\Documents\Malik Inam\Quantec Team\subrub_roi_poc\combined_suburb_roi_analysis_with_g02.ipynb"

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

updated = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "top_suburbs = analysis_data.nlargest" in source:
            # Check for missing columns
            missing = []
            if "'IRSAD_Score'" not in source: missing.append("'IRSAD_Score'")
            if "'Median_mortgage_repay_monthly'" not in source: missing.append("'Median_mortgage_repay_monthly'")
            
            if missing:
                # Insert missing columns after 'SAL_NAME_2021_SEIFA',
                new_cols = ", ".join(missing) + ","
                new_source = source.replace("'SAL_NAME_2021_SEIFA',", f"'SAL_NAME_2021_SEIFA', {new_cols}")
                cell['source'] = [line + '\n' for line in new_source.split('\n')]
                # Fix trailing \n
                if cell['source'][-1].strip() == "":
                    cell['source'] = cell['source'][:-1]
                print(f"Added {new_cols} to top_suburbs column selection.")
                updated = True

if updated:
    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Notebook updated successfully.")
else:
    print("No updates needed or pattern not found.")
