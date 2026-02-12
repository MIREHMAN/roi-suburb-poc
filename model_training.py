import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib

DATA_FILE = Path("prepared_data/suburb_roi_features.csv")
MODEL_FILE = Path("models/roi_model.pkl")

TARGET = "Realistic_ROI_Target"

# Intentionally excludes direct-yield proxy fields to reduce leakage.
FEATURES = [
    "IRSD_Score",
    "IRSAD_Score",
    "IER_Score",
    "IEO_Score",
    "Median_age_persons",
    "Median_tot_prsnl_inc_weekly",
    "Median_tot_hhd_inc_weekly",
    "Average_household_size",
    "Tot_P_P",
    "Working_Age_Share",
    "Senior_Share",
    "Diversity_Share",
    "Rent_to_Income_Ratio",
]


def main() -> None:
    print("Loading prepared data...")
    df = pd.read_csv(DATA_FILE)

    available_features = [f for f in FEATURES if f in df.columns]
    df = df.dropna(subset=available_features + [TARGET])

    X = df[available_features]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training model...")
    model = RandomForestRegressor(
        n_estimators=500,
        max_depth=10,
        min_samples_leaf=6,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    print("Evaluating model...")
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    print("R2:", round(r2, 4))
    print("MAE:", round(mae, 4))
    print("RMSE:", round(rmse, 4))

    print("Saving model...")
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": available_features,
            "target": TARGET,
            "metrics": {"r2": float(r2), "mae": float(mae), "rmse": float(rmse)},
        },
        MODEL_FILE,
    )

    print(f"Model saved at: {MODEL_FILE}")


if __name__ == "__main__":
    main()
