# POC Workflow

## 1) Prepare data + train model

```powershell
.\.venv\Scripts\python.exe scripts\run_workflow.py
```

This creates:
- `prepared_data/suburb_roi_features.csv`
- `models/roi_model.pkl`

Expected training behavior (realistic, non-perfect):
- target: `Realistic_ROI_Target`
- typical metrics in this POC: `R2 ~ 0.30-0.45`, `MAE ~ 0.02-0.04`

## 2) Run backend

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Health check:
- `http://localhost:8000/api/health`

Core APIs:
- `http://localhost:8000/api/suburbs?min_roi=10&top_n=20`
- `http://localhost:8000/api/features`
- `http://localhost:8000/api/suburb-names?limit=200`
- `http://localhost:8000/api/opportunities?top_n=20`
- `http://localhost:8000/api/report/csv?min_roi=10&top_n=20`
- `http://localhost:8000/api/report/pdf?min_roi=10&top_n=20`

Prediction API example:
```powershell
curl -X POST http://localhost:8000/api/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"suburb_name\":\"Abbotsbury\",\"feature_values\":{\"Median_rent_weekly\":620}}"
```

## 3) Run frontend

```powershell
cd frontend
npm run dev
```

Frontend URL:
- `http://localhost:5173`

What the UI now supports:
- Filtered suburb opportunity explorer (ROI, price, SEIFA, top-N).
- Prediction sandbox:
  - pick a suburb baseline from dropdown/typeahead,
  - choose features from dropdown,
  - set custom values,
  - run trained-model ROI prediction.
- Investment insights panel:
  - summary KPIs,
  - top opportunities with insight tags.
- Download recommendation report buttons:
  - `Download Report (CSV)` with active filters
  - `Download Report (PDF)` with active filters

## 4) Quick backend smoke test (optional)

With backend running:

```powershell
.\.venv\Scripts\python.exe scripts\test_script.py
```
