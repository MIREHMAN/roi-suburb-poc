import json
import os

notebook_path = r'c:\Users\ibrah\OneDrive\Documents\Malik Inam\Quantec Team\subrub_roi_poc\combined_suburb_roi_analysis_with_g02.ipynb'

def fix_roi_nan():
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    modified = False

    for cell in cells:
        if cell['cell_type'] == 'code':
            source = cell['source']
            source_text = "".join(source)
            
            # Identify the cell calculating Real ROI (Cell 51 based on context)
            if "analysis_data['True_ROI'] =" in source_text and "Real ROI metrics calculated successfully" in source_text:
                print("Found ROI calculation cell.")
                
                # Logic to add
                filter_code = [
                    "\n",
                    "# Filter out suburbs with invalid financial data (NaN Price or 0 Rent) preventing NaN ROI\n",
                    "print(\"Filtering out suburbs with missing financial data...\")\n",
                    "initial_count = len(analysis_data)\n",
                    "analysis_data = analysis_data.dropna(subset=['Median_Property_Price'])\n",
                    "analysis_data = analysis_data[analysis_data['Median_Weekly_Rent'] > 0]\n",
                    "analysis_data = analysis_data[analysis_data['Median_Property_Price'] > 0]\n",
                    "print(f\"Removed {initial_count - len(analysis_data)} suburbs with invalid Price or Rent.\")\n",
                    "\n"
                ]
                
                # Insert before the final print
                new_source = []
                inserted = False
                for line in source:
                    if "Real ROI metrics calculated successfully" in line and not inserted:
                        new_source.extend(filter_code)
                        new_source.append(line)
                        inserted = True
                    else:
                        new_source.append(line)
                
                cell['source'] = new_source
                modified = True
                print("Injected filtering logic.")
                break

    if modified:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print(f"Notebook updated: {notebook_path}")
    else:
        print("Could not find the target cell to modify.")

if __name__ == "__main__":
    fix_roi_nan()
