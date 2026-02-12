
import json
from pathlib import Path

def nb_to_py(nb_path, py_path):
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    with open(py_path, 'w', encoding='utf-8') as f:
        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                f.write("\n# CELL ID: {cell.get('id', 'unknown')}\n")
                if 'display(' in "".join(cell['source']):
                    f.write("def display(x): print(x)\n")
                if 'plt.show()' in "".join(cell['source']):
                    f.write("import matplotlib.pyplot as plt\nplt.show = lambda: None\n")
                for line in cell['source']:
                    if not line.strip().startswith('%') and not line.strip().startswith('!'):
                        f.write(line)
                f.write("\n")

if __name__ == "__main__":
    nb_path = Path(r"c:\Users\ibrah\OneDrive\Documents\Malik Inam\Quantec Team\subrub_roi_poc\combined_suburb_roi_analysis_with_g02.ipynb")
    py_path = Path("debug_nb.py")
    nb_to_py(nb_path, py_path)
    print(f"Converted {nb_path} to {py_path}")
