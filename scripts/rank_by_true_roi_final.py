import json
import os

notebook_path = r'c:\Users\ibrah\OneDrive\Documents\Malik Inam\Quantec Team\subrub_roi_poc\combined_suburb_roi_analysis_with_g02.ipynb'

def rank_by_true_roi_final():
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    modified = False

    for cell in cells:
        if cell['cell_type'] == 'code':
            source = cell['source']
            source_text = "".join(source)
            
            # Find the cell that selects top suburbs
            if "top_suburbs = analysis_data.nlargest(top_n, 'Investment_Potential_Index')" in source_text:
                print("Found ranking cell - changing to True_ROI ranking.")
                
                new_source = []
                for line in source:
                    # Change the sorting column to True_ROI
                    if "nlargest(top_n, 'Investment_Potential_Index')" in line:
                        new_line = line.replace("'Investment_Potential_Index'", "'True_ROI'")
                        new_source.append(new_line)
                    # Update the print statement
                    elif "Top {top_n} Investment Opportunities (Real ROI Best Practice)" in line:
                        new_source.append(line)
                    else:
                        new_source.append(line)
                
                cell['source'] = new_source
                modified = True
                print("Updated to rank by True_ROI.")
                break

    if modified:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print(f"Notebook updated: {notebook_path}")
        print("Suburbs will now be ranked strictly by True_ROI (with realistic filters applied).")
    else:
        print("Could not find the target cell to modify.")

if __name__ == "__main__":
    rank_by_true_roi_final()
