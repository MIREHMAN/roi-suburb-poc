import json
import os

notebook_path = r'c:\Users\ibrah\OneDrive\Documents\Malik Inam\Quantec Team\subrub_roi_poc\combined_suburb_roi_analysis_with_g02.ipynb'

def fix_realistic_roi():
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    modified = False

    for cell in cells:
        if cell['cell_type'] == 'code':
            source = cell['source']
            source_text = "".join(source)
            
            # Find the filtering cell we added earlier
            if "Filter out suburbs with invalid financial data" in source_text and "dropna(subset=['Median_Property_Price'])" in source_text:
                print("Found filtering cell - adding realistic price filters.")
                
                new_source = []
                for line in source:
                    new_source.append(line)
                    # Add realistic filters after the existing filters
                    if "analysis_data[analysis_data['Median_Property_Price'] > 0]" in line:
                        realistic_filters = [
                            "\n",
                            "# Apply realistic property price filters (minimum $200k to avoid outliers)\n",
                            "analysis_data = analysis_data[analysis_data['Median_Property_Price'] >= 200000]\n",
                            "# Filter out suburbs with unrealistic rent-to-price ratios (max 15% gross yield)\n",
                            "analysis_data = analysis_data[analysis_data['Rental_Yield_Pct'] <= 15]\n",
                            "print(f\"After realistic filters: {len(analysis_data)} suburbs remaining.\")\n"
                        ]
                        new_source.extend(realistic_filters)
                
                cell['source'] = new_source
                modified = True
                print("Added realistic property price filters.")
                break

    # Now restore Investment_Potential_Index ranking
    if modified:
        for cell in cells:
            if cell['cell_type'] == 'code':
                source = cell['source']
                source_text = "".join(source)
                
                if "top_suburbs = analysis_data.nlargest(top_n, 'True_ROI')" in source_text:
                    print("Found ranking cell - restoring Investment_Potential_Index.")
                    new_source = []
                    for line in source:
                        if "nlargest(top_n, 'True_ROI')" in line:
                            new_line = line.replace("'True_ROI'", "'Investment_Potential_Index'")
                            new_source.append(new_line)
                        else:
                            new_source.append(line)
                    
                    cell['source'] = new_source
                    print("Restored Investment_Potential_Index ranking.")
                    break

    if modified:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print(f"Notebook updated: {notebook_path}")
    else:
        print("Could not find the target cells to modify.")

if __name__ == "__main__":
    fix_realistic_roi()
