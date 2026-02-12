from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT_DIR / "prepared_data" / "suburb_roi_features.csv"
MODEL_PATH = ROOT_DIR / "models" / "roi_model.pkl"


def _safe_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_model_artifact() -> dict[str, Any] | None:
    if not MODEL_PATH.exists():
        return None

    artifact = joblib.load(MODEL_PATH)
    if not isinstance(artifact, dict):
        return None
    if "model" not in artifact or "features" not in artifact:
        return None
    return artifact


def load_dataset(artifact: dict[str, Any] | None = None) -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found at {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    if artifact:
        features = [f for f in artifact.get("features", []) if f in df.columns]
        df = _safe_numeric(df, features)
        model_input = df[features].copy()
        model_input = model_input.replace([np.inf, -np.inf], np.nan)
        model_input = model_input.fillna(model_input.median(numeric_only=True)).fillna(0)
        df["roi"] = artifact["model"].predict(model_input)
    else:
        fallback_target = "Realistic_ROI_Target" if "Realistic_ROI_Target" in df.columns else "ROI_Proxy_Score"
        df["roi"] = pd.to_numeric(df.get(fallback_target, 0), errors="coerce").fillna(0)

    if "SAL_NAME_2021" in df.columns:
        df["name"] = df["SAL_NAME_2021"]
    if "Median_mortgage_repay_monthly" in df.columns:
        df["price"] = pd.to_numeric(df["Median_mortgage_repay_monthly"], errors="coerce")
    if "Median_rent_weekly" in df.columns:
        df["rent"] = pd.to_numeric(df["Median_rent_weekly"], errors="coerce")
    if "IRSD_Score" in df.columns:
        df["seifa_score"] = pd.to_numeric(df["IRSD_Score"], errors="coerce")

    if "yield_pct" not in df.columns:
        df["yield_pct"] = 0.0
    if "growth_pct" not in df.columns:
        df["growth_pct"] = 0.0
    if "Top20_Flag" not in df.columns:
        df["Top20_Flag"] = 0

    return df.replace([np.inf, -np.inf], np.nan)


def dataset_to_api_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    output_cols = [
        "name",
        "roi",
        "price",
        "rent",
        "seifa_score",
        "yield_pct",
        "growth_pct",
        "Top20_Flag",
    ]
    existing = [c for c in output_cols if c in df.columns]
    data = df[existing].copy().fillna(0)
    return data.to_dict(orient="records")


def get_feature_metadata(df: pd.DataFrame, model_features: list[str]) -> list[dict[str, Any]]:
    meta: list[dict[str, Any]] = []
    for feature in model_features:
        if feature not in df.columns:
            continue
        s = pd.to_numeric(df[feature], errors="coerce").replace([np.inf, -np.inf], np.nan)
        if s.dropna().empty:
            continue
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1
        safe_min = float(max(s.min(), q1 - 1.5 * iqr)) if iqr > 0 else float(s.min())
        safe_max = float(min(s.max(), q3 + 1.5 * iqr)) if iqr > 0 else float(s.max())
        meta.append(
            {
                "feature": feature,
                "min": round(safe_min, 4),
                "max": round(safe_max, 4),
                "median": round(float(s.median()), 4),
                "mean": round(float(s.mean()), 4),
            }
        )
    return meta


def _build_base_feature_vector(
    df: pd.DataFrame,
    model_features: list[str],
    suburb_name: str | None,
) -> dict[str, float]:
    if suburb_name:
        matched = df[df["name"].str.lower() == suburb_name.lower()]
        if not matched.empty:
            row = matched.iloc[0]
            result: dict[str, float] = {}
            for f in model_features:
                val = pd.to_numeric(row.get(f), errors="coerce")
                if pd.isna(val):
                    val = pd.to_numeric(df[f], errors="coerce").median()
                result[f] = float(val)
            return result

    result = {}
    for f in model_features:
        s = pd.to_numeric(df[f], errors="coerce")
        result[f] = float(s.median())
    return result


def predict_from_inputs(
    df: pd.DataFrame,
    artifact: dict[str, Any],
    suburb_name: str | None,
    feature_values: dict[str, float] | None,
) -> dict[str, Any]:
    model = artifact["model"]
    model_features = [f for f in artifact.get("features", []) if f in df.columns]
    if not model_features:
        raise ValueError("No usable model features are available in prepared data.")

    base = _build_base_feature_vector(df, model_features, suburb_name)
    feature_values = feature_values or {}

    for key, value in feature_values.items():
        if key in base and value is not None:
            base[key] = float(value)

    model_input = pd.DataFrame([base], columns=model_features)
    model_input = model_input.replace([np.inf, -np.inf], np.nan).fillna(0)

    roi_score = float(model.predict(model_input)[0])
    historical = pd.to_numeric(df["roi"], errors="coerce").dropna()
    percentile = 0.0
    if not historical.empty:
        percentile = float((historical <= roi_score).mean() * 100)

    # Lightweight interpretability for POC: combine feature importance with normalized delta.
    medians = {f: float(pd.to_numeric(df[f], errors="coerce").median()) for f in model_features}
    stds = {
        f: float(pd.to_numeric(df[f], errors="coerce").std())
        for f in model_features
    }

    importances = getattr(model, "feature_importances_", np.ones(len(model_features)))
    importances = np.array(importances, dtype=float)

    contributions = []
    for idx, f in enumerate(model_features):
        denom = stds[f] if stds[f] and stds[f] > 0 else 1.0
        delta = (base[f] - medians[f]) / denom
        score = float(importances[idx] * delta)
        direction = "positive" if score >= 0 else "negative"
        contributions.append(
            {
                "feature": f,
                "value": round(base[f], 4),
                "median": round(medians[f], 4),
                "effect": direction,
                "impact_score": round(score, 4),
            }
        )

    top_factors = sorted(contributions, key=lambda x: abs(x["impact_score"]), reverse=True)[:5]

    signal = "Moderate"
    if percentile >= 80:
        signal = "Strong"
    elif percentile <= 40:
        signal = "Cautious"

    return {
        "suburb_name": suburb_name,
        "predicted_roi_score": round(roi_score, 6),
        "predicted_roi_percent": round(roi_score * 100, 2),
        "percentile_vs_all_suburbs": round(percentile, 2),
        "investment_signal": signal,
        "input_features": {k: round(v, 4) for k, v in base.items()},
        "top_factors": top_factors,
    }


def investment_opportunities(df: pd.DataFrame, top_n: int = 20) -> dict[str, Any]:
    working = df.copy()
    working = working.dropna(subset=["name", "roi"])
    working = working.sort_values("roi", ascending=False)

    top_n = max(5, min(top_n, 100))
    top = working.head(top_n).copy()

    rent_p75 = pd.to_numeric(working.get("rent", 0), errors="coerce").quantile(0.75)
    seifa_p60 = pd.to_numeric(working.get("seifa_score", 0), errors="coerce").quantile(0.60)
    mortgage_p40 = pd.to_numeric(working.get("price", 0), errors="coerce").quantile(0.40)

    def tags(row: pd.Series) -> list[str]:
        t: list[str] = []
        if row.get("rent", 0) >= rent_p75:
            t.append("High rent demand")
        if row.get("seifa_score", 0) >= seifa_p60:
            t.append("Socio-economic resilience")
        if row.get("price", 0) <= mortgage_p40:
            t.append("Relatively affordable")
        if row.get("Top20_Flag", 0) == 1:
            t.append("Top ROI cluster")
        if not t:
            t.append("Balanced profile")
        return t

    top["insight_tags"] = top.apply(tags, axis=1)

    summary = {
        "avg_roi_percent_top_n": round(float(top["roi"].mean() * 100), 2),
        "median_roi_percent_all": round(float(working["roi"].median() * 100), 2),
        "max_roi_percent": round(float(working["roi"].max() * 100), 2),
        "suburbs_analyzed": int(len(working)),
    }

    cols = [
        "name",
        "roi",
        "price",
        "rent",
        "seifa_score",
        "Top20_Flag",
        "insight_tags",
    ]
    rows = top[cols].fillna(0).to_dict(orient="records")
    return {"summary": summary, "opportunities": rows}


def filter_suburbs(
    rows: list[dict[str, Any]],
    name: str | None = None,
    min_roi: float | None = None,
    max_price: float | None = None,
    min_seifa: float | None = None,
) -> list[dict[str, Any]]:
    filtered = rows

    if name:
        filtered = [s for s in filtered if name.lower() in str(s.get("name", "")).lower()]

    if min_roi is not None:
        threshold = min_roi / 100 if min_roi > 1 else min_roi
        filtered = [s for s in filtered if float(s.get("roi", 0) or 0) >= threshold]

    if max_price is not None:
        filtered = [s for s in filtered if float(s.get("price", 0) or 0) <= max_price]

    if min_seifa is not None:
        filtered = [s for s in filtered if float(s.get("seifa_score", 0) or 0) >= min_seifa]

    return sorted(filtered, key=lambda x: float(x.get("roi", 0) or 0), reverse=True)


def opportunities_from_rows(rows: list[dict[str, Any]], top_n: int = 20) -> dict[str, Any]:
    if not rows:
        return {
            "summary": {
                "avg_roi_percent_top_n": 0.0,
                "median_roi_percent_all": 0.0,
                "max_roi_percent": 0.0,
                "suburbs_analyzed": 0,
            },
            "opportunities": [],
        }

    working = pd.DataFrame(rows).copy()
    working["roi"] = pd.to_numeric(working.get("roi", 0), errors="coerce").fillna(0)
    working["rent"] = pd.to_numeric(working.get("rent", 0), errors="coerce").fillna(0)
    working["seifa_score"] = pd.to_numeric(working.get("seifa_score", 0), errors="coerce").fillna(0)
    working["price"] = pd.to_numeric(working.get("price", 0), errors="coerce").fillna(0)

    working = working.sort_values("roi", ascending=False)
    top_n = max(5, min(top_n, 100))
    top = working.head(top_n).copy()

    rent_p75 = working["rent"].quantile(0.75)
    seifa_p60 = working["seifa_score"].quantile(0.60)
    mortgage_p40 = working["price"].quantile(0.40)

    def tags(row: pd.Series) -> list[str]:
        t: list[str] = []
        if row.get("rent", 0) >= rent_p75:
            t.append("High rent demand")
        if row.get("seifa_score", 0) >= seifa_p60:
            t.append("Socio-economic resilience")
        if row.get("price", 0) <= mortgage_p40:
            t.append("Relatively affordable")
        if row.get("Top20_Flag", 0) == 1:
            t.append("Top ROI cluster")
        if not t:
            t.append("Balanced profile")
        return t

    top["insight_tags"] = top.apply(tags, axis=1)

    summary = {
        "avg_roi_percent_top_n": round(float(top["roi"].mean() * 100), 2),
        "median_roi_percent_all": round(float(working["roi"].median() * 100), 2),
        "max_roi_percent": round(float(working["roi"].max() * 100), 2),
        "suburbs_analyzed": int(len(working)),
    }

    cols = [
        "name",
        "roi",
        "price",
        "rent",
        "seifa_score",
        "Top20_Flag",
        "insight_tags",
    ]
    opp_rows = top[cols].fillna(0).to_dict(orient="records")
    return {"summary": summary, "opportunities": opp_rows}


def suburb_names(df: pd.DataFrame, q: str | None, limit: int = 200) -> list[str]:
    names = df["name"].dropna().astype(str)
    if q:
        names = names[names.str.contains(q, case=False, na=False)]
    unique_names = sorted(names.unique().tolist())
    return unique_names[: max(1, min(limit, 1000))]
