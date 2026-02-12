from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
VENV_PY = ROOT / '.venv' / 'Scripts' / 'python.exe'


def run_step(step_name: str, cmd: list[str], cwd: Path) -> None:
    print(f'\n=== {step_name} ===')
    print(' '.join(cmd))
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(f'{step_name} failed with exit code {result.returncode}')


def main() -> None:
    python_bin = str(VENV_PY if VENV_PY.exists() else Path(sys.executable))

    run_step(
        'Data Preparation',
        [python_bin, 'data_preparation.py'],
        ROOT,
    )

    run_step(
        'Model Training',
        [python_bin, 'model_training.py'],
        ROOT,
    )

    print('\nWorkflow complete.')
    print('1) Start backend:')
    print('   cd backend && ..\\.venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 8000')
    print('2) Start frontend:')
    print('   cd frontend && npm run dev')


if __name__ == '__main__':
    main()
