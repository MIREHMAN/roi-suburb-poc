import numpy as np
import pandas as pd
from pathlib import Path

SEIFA_FILE = Path("abs_data/SEIFA_2021_SAL.xlsx")
DATAPACK_DIR = Path(
    "abs_data/census_2021_datapack_sal/Australia/2021 Census GCP Suburbs and Localities for AUS"
)
G01_CSV = DATAPACK_DIR / "2021Census_G01_AUST_SAL.csv"
G02_CSV = DATAPACK_DIR / "2021Census_G02_AUST_SAL.csv"
OUTPUT_FILE = Path("prepared_data/suburb_roi_features.csv")

SEIFA_RENAMED_COLUMNS = {
    "2021 Suburbs and Localities (SAL) Code": "SAL_CODE_2021",
    "2021 Suburbs and Localities (SAL) Name": "SAL_NAME_2021",
    "Score": "IRSD_Score",
    "Decile": "IRSD_Decile",
    "Score.1": "IRSAD_Score",
    "Decile.1": "IRSAD_Decile",
    "Score.2": "IER_Score",
    "Decile.2": "IER_Decile",
    "Score.3": "IEO_Score",
    "Decile.3": "IEO_Decile",
    "Usual Resident Population": "Usual_Resident_Population",
}

G02_KEEP_COLS = [
    "SAL_CODE_2021",
    "Median_age_persons",
    "Median_mortgage_repay_monthly",
    "Median_tot_prsnl_inc_weekly",
    "Median_rent_weekly",
    "Median_tot_fam_inc_weekly",
    "Average_num_psns_per_bedroom",
    "Median_tot_hhd_inc_weekly",
    "Average_household_size",
]

G01_KEEP_COLS = [
    "SAL_CODE_2021",
    "Tot_P_P",
    "Age_0_4_yr_P",
    "Age_5_14_yr_P",
    "Age_15_19_yr_P",
    "Age_20_24_yr_P",
    "Age_25_34_yr_P",
    "Age_35_44_yr_P",
    "Age_45_54_yr_P",
    "Age_55_64_yr_P",
    "Age_65_74_yr_P",
    "Age_75_84_yr_P",
    "Age_85ov_P",
    "Birthplace_Elsewhere_P",
    "Lang_used_home_Oth_Lang_P",
    "Australian_citizen_P",
]

NUMERIC_COLS = [
    "IRSD_Score",
    "IRSAD_Score",
    "IER_Score",
    "IEO_Score",
    "Median_age_persons",
    "Median_mortgage_repay_monthly",
    "Median_tot_prsnl_inc_weekly",
    "Median_rent_weekly",
    "Median_tot_fam_inc_weekly",
    "Average_num_psns_per_bedroom",
    "Median_tot_hhd_inc_weekly",
    "Average_household_size",
    "Tot_P_P",
    "Age_0_4_yr_P",
    "Age_5_14_yr_P",
    "Age_15_19_yr_P",
    "Age_20_24_yr_P",
    "Age_25_34_yr_P",
    "Age_35_44_yr_P",
    "Age_45_54_yr_P",
    "Age_55_64_yr_P",
    "Age_65_74_yr_P",
    "Age_75_84_yr_P",
    "Age_85ov_P",
    "Birthplace_Elsewhere_P",
    "Lang_used_home_Oth_Lang_P",
    "Australian_citizen_P",
]


def normalize_sal_code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace("SAL", "", regex=False).str.strip()


def safe_norm(series: pd.Series) -> pd.Series:
    lo = series.min()
    hi = series.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(0.0, index=series.index)
    return (series - lo) / (hi - lo)


def monthly_payment_to_principal(monthly_payment: pd.Series, annual_rate: float = 0.062, years: int = 30) -> pd.Series:
    r = annual_rate / 12
    n = years * 12
    factor = ((1 + r) ** n - 1) / (r * (1 + r) ** n)
    return monthly_payment * factor


def load_seifa(filepath: Path) -> pd.DataFrame:
    df = pd.read_excel(filepath, sheet_name="Table 1", skiprows=5)
    df = df.rename(columns=SEIFA_RENAMED_COLUMNS)
    df = df[list(SEIFA_RENAMED_COLUMNS.values())].copy()
    df["SAL_CODE_2021_clean"] = normalize_sal_code(df["SAL_CODE_2021"])
    return df


def load_g02(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, usecols=G02_KEEP_COLS)
    df["SAL_CODE_2021_clean"] = normalize_sal_code(df["SAL_CODE_2021"])
    return df


def load_g01(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath, usecols=G01_KEEP_COLS)
    df["SAL_CODE_2021_clean"] = normalize_sal_code(df["SAL_CODE_2021"])
    return df


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Income_to_Mortgage_Ratio"] = (
        (df["Median_tot_hhd_inc_weekly"] * 4.33) / df["Median_mortgage_repay_monthly"]
    )

    df["Rent_to_Income_Ratio"] = df["Median_rent_weekly"] / df["Median_tot_hhd_inc_weekly"]

    df["Working_Age_Share"] = (
        df["Age_25_34_yr_P"] + df["Age_35_44_yr_P"] + df["Age_45_54_yr_P"]
    ) / df["Tot_P_P"]

    df["Senior_Share"] = (
        df["Age_65_74_yr_P"] + df["Age_75_84_yr_P"] + df["Age_85ov_P"]
    ) / df["Tot_P_P"]

    df["Diversity_Share"] = (
        df["Birthplace_Elsewhere_P"] + df["Lang_used_home_Oth_Lang_P"]
    ) / (2 * df["Tot_P_P"])

    # Approximate purchase price from mortgage repayments to create realistic yield signal.
    df["Estimated_Property_Price"] = monthly_payment_to_principal(df["Median_mortgage_repay_monthly"])
    df["Annual_Rent"] = df["Median_rent_weekly"] * 52
    df["Estimated_Gross_Yield_Pct"] = (df["Annual_Rent"] / df["Estimated_Property_Price"]) * 100

    # Legacy proxy kept for compatibility and comparison.
    df["ROI_Proxy_Score"] = (
        0.35 * safe_norm(df["Income_to_Mortgage_Ratio"])
        + 0.30 * safe_norm(df["Median_rent_weekly"])
        + 0.20 * safe_norm(df["IRSAD_Score"])
        + 0.15 * safe_norm(df["Working_Age_Share"])
    )

    # Less-perfect target with broader components and mild stochastic market noise.
    demand_score = (
        0.45 * safe_norm(df["Working_Age_Share"])
        + 0.30 * safe_norm(df["Diversity_Share"])
        + 0.25 * safe_norm(np.log1p(df["Tot_P_P"]))
    )
    risk_penalty = (
        0.50 * safe_norm(df["Senior_Share"])
        + 0.30 * safe_norm(df["Rent_to_Income_Ratio"])
        + 0.20 * (1 - safe_norm(df["IRSD_Score"]))
    )

    base_target = (
        0.40 * safe_norm(df["Estimated_Gross_Yield_Pct"])
        + 0.25 * safe_norm(df["Income_to_Mortgage_Ratio"])
        + 0.20 * safe_norm(df["IRSAD_Score"])
        + 0.15 * demand_score
        - 0.20 * risk_penalty
    )

    rng = np.random.default_rng(42)
    market_noise = rng.normal(loc=0.0, scale=0.035, size=len(df))

    df["Realistic_ROI_Target"] = (base_target + market_noise).clip(0.02, 0.95)
    df["ROI_Rank"] = df["Realistic_ROI_Target"].rank(method="dense", ascending=False).astype("Int64")
    df["Top20_Flag"] = (df["Realistic_ROI_Target"] >= df["Realistic_ROI_Target"].quantile(0.80)).astype(int)

    return df


def main() -> None:
    print("Loading SEIFA, G01, G02...")
    seifa = load_seifa(SEIFA_FILE)
    g02 = load_g02(G02_CSV)
    g01 = load_g01(G01_CSV)

    print("Merging datasets...")
    df = (
        seifa.merge(g02, on="SAL_CODE_2021_clean", how="left", suffixes=("", "_G02"))
        .merge(g01, on="SAL_CODE_2021_clean", how="left", suffixes=("", "_G01"))
    )

    if "SAL_CODE_2021_G02" in df.columns:
        df = df.drop(columns=["SAL_CODE_2021_G02"])
    if "SAL_CODE_2021_G01" in df.columns:
        df = df.drop(columns=["SAL_CODE_2021_G01"])

    df = feature_engineering(df)

    key_cols = [
        "SAL_CODE_2021",
        "SAL_NAME_2021",
        "IRSD_Score",
        "IRSAD_Score",
        "IER_Score",
        "IEO_Score",
        "Median_age_persons",
        "Median_mortgage_repay_monthly",
        "Median_tot_prsnl_inc_weekly",
        "Median_rent_weekly",
        "Median_tot_hhd_inc_weekly",
        "Average_household_size",
        "Tot_P_P",
        "Income_to_Mortgage_Ratio",
        "Rent_to_Income_Ratio",
        "Working_Age_Share",
        "Senior_Share",
        "Diversity_Share",
        "Estimated_Property_Price",
        "Estimated_Gross_Yield_Pct",
        "ROI_Proxy_Score",
        "Realistic_ROI_Target",
        "ROI_Rank",
        "Top20_Flag",
    ]
    existing_cols = [c for c in key_cols if c in df.columns]
    df = df[existing_cols].copy()

    print("Saving prepared dataset...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Data preparation complete: {OUTPUT_FILE}")
    print(f"Rows: {len(df)} | Columns: {len(df.columns)}")


if __name__ == "__main__":
    main()
