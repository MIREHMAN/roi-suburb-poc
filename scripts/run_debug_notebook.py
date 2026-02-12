
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from pathlib import Path
import sys

def run_notebook(notebook_path):
    print(f"Running notebook: {notebook_path}")
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    
    try:
        ep.preprocess(nb, {'metadata': {'path': str(notebook_path.parent)}})
        print("Notebook executed successfully.")
        return True, nb
    except Exception as e:
        print(f"Error executing notebook: {e}")
        return False, nb

if __name__ == "__main__":
    notebook_path = Path(r"c:\Users\ibrah\OneDrive\Documents\Malik Inam\Quantec Team\subrub_roi_poc\combined_suburb_roi_analysis_with_g02.ipynb")
    success, executed_nb = run_notebook(notebook_path)
    
    # Save the executed notebook to see exact output and errors
    with open(notebook_path.with_name("executed_debug.ipynb"), 'w', encoding='utf-8') as f:
        nbformat.write(executed_nb, f)
    
    if not success:
        sys.exit(1)
