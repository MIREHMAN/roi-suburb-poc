"""
Example: Suburb ROI Analysis Using ABS Census 2021 Data
This script shows how to analyze suburbs for investment opportunities
"""

import pandas as pd
import numpy as np
from pathlib import Path

# =====================================================
# Configuration
# =====================================================
DATA_DIR = Path("abs_data")

# File paths (adjust based on what you downloaded)
SEIFA_FILE = DATA_DIR / "SEIFA_2021_SAL.xlsx"

# For DataPack files, the path depends on which state you downloaded
# Adjust this to match your download:
STATE = "Australia"  # or "NSW", "VIC", etc.
DATAPACK_DIR = DATA_DIR / "census_2021_datapack_sal" / STATE

# =====================================================
# Step 1: Load SEIFA Data
# =====================================================
print("="*70)
print("Loading SEIFA 2021 Data...")
print("="*70)

try:
    # SEIFA has multiple sheets, we want the indexes
    seifa = pd.read_excel(SEIFA_FILE, sheet_name='Table 1')
    print(f"✓ Loaded SEIFA data: {len(seifa)} suburbs")
    print(f"\nColumns available: {seifa.columns.tolist()[:10]}...")
    
    # Display summary statistics
    print("\nSEIFA Score Distributions:")
    print(seifa[['IRSAD_Score', 'IRSD_Score', 'IEO_Score', 'IER_Score']].describe())
    
except FileNotFoundError:
    print(f"✗ SEIFA file not found at: {SEIFA_FILE}")
    print("  Please run download_abs_data_fixed.py first")
    seifa = None

# =====================================================
# Step 2: Find and Load G02 Data (Medians)
# =====================================================
print("\n" + "="*70)
print("Loading Census G02 Data (Medians and Averages)...")
print("="*70)

try:
    # Find G02 CSV files
    g02_files = list(DATAPACK_DIR.glob("**/G02*.csv"))
    
    if g02_files:
        # Use the first G02 file found
        g02_file = g02_files[0]
        print(f"✓ Found G02 file: {g02_file.name}")
        
        g02 = pd.read_csv(g02_file)
        print(f"  Loaded {len(g02)} suburbs")
        print(f"\nSample columns: {g02.columns.tolist()[:15]}...")
        
        # Display some median income statistics
        if 'Median_tot_prsnl_inc_weekly' in g02.columns:
            income_stats = g02['Median_tot_prsnl_inc_weekly'].describe()
            print("\nMedian Personal Income Distribution:")
            print(income_stats)
    else:
        print(f"✗ No G02 files found in {DATAPACK_DIR}")
        print("  Please extract the DataPack ZIP file first")
        g02 = None
        
except Exception as e:
    print(f"✗ Error loading G02 data: {e}")
    g02 = None

# =====================================================
# Step 3: Merge Datasets
# =====================================================
if seifa is not None and g02 is not None:
    print("\n" + "="*70)
    print("Merging SEIFA and Census Data...")
    print("="*70)
    
    # Merge on suburb code
    merged = pd.merge(
        seifa, 
        g02,
        left_on='SAL_CODE_2021',
        right_on='SAL_CODE_2021',
        how='inner',
        suffixes=('_seifa', '_census')
    )
    
    print(f"✓ Merged dataset: {len(merged)} suburbs")
    
    # =====================================================
    # Step 4: Calculate Investment Metrics
    # =====================================================
    print("\n" + "="*70)
    print("Calculating Investment Opportunity Metrics...")
    print("="*70)
    
    # Create a composite score based on various factors
    # You can adjust these weights based on your investment strategy
    
    # Normalize scores to 0-1 range
    def normalize(series):
        return (series - series.min()) / (series.max() - series.min())
    
    # Calculate individual metrics (higher is better for investment)
    metrics = pd.DataFrame()
    metrics['suburb'] = merged['SAL_NAME_2021_seifa']
    metrics['suburb_code'] = merged['SAL_CODE_2021']
    
    # Affordability (lower IRSAD = potentially undervalued)
    metrics['affordability_score'] = 1 - normalize(merged['IRSAD_Score'])
    
    # Income growth potential (higher income = more purchasing power)
    if 'Median_tot_prsnl_inc_weekly' in merged.columns:
        metrics['income_score'] = normalize(merged['Median_tot_prsnl_inc_weekly'])
    
    # Education and occupation potential (future growth)
    metrics['education_score'] = normalize(merged['IEO_Score'])
    
    # Economic resources (stability)
    metrics['economic_score'] = normalize(merged['IER_Score'])
    
    # Composite ROI score (weighted average)
    # Adjust these weights based on your strategy
    weights = {
        'affordability': 0.3,
        'income': 0.3,
        'education': 0.2,
        'economic': 0.2
    }
    
    metrics['roi_score'] = (
        weights['affordability'] * metrics['affordability_score'] +
        weights['income'] * metrics.get('income_score', 0) +
        weights['education'] * metrics['education_score'] +
        weights['economic'] * metrics['economic_score']
    )
    
    # =====================================================
    # Step 5: Find Top Investment Opportunities
    # =====================================================
    print("\n" + "="*70)
    print("TOP 20 INVESTMENT OPPORTUNITIES")
    print("="*70)
    
    # Sort by ROI score
    top_suburbs = metrics.nlargest(20, 'roi_score')
    
    # Merge back to get full details
    top_suburbs_full = pd.merge(
        top_suburbs,
        merged,
        left_on='suburb_code',
        right_on='SAL_CODE_2021',
        how='left'
    )
    
    # Display results
    display_cols = [
        'suburb',
        'roi_score',
        'IRSAD_Score',
        'IRSAD_Decile',
    ]
    
    # Add income columns if available
    if 'Median_tot_prsnl_inc_weekly' in top_suburbs_full.columns:
        display_cols.append('Median_tot_prsnl_inc_weekly')
    if 'Median_tot_hhd_inc_weekly' in top_suburbs_full.columns:
        display_cols.append('Median_tot_hhd_inc_weekly')
    
    # Format and display
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 30)
    
    print("\n" + top_suburbs_full[display_cols].to_string(index=False))
    
    # =====================================================
    # Step 6: Detailed Analysis of Top Suburb
    # =====================================================
    print("\n" + "="*70)
    print("DETAILED ANALYSIS: Top Opportunity")
    print("="*70)
    
    top_suburb = top_suburbs_full.iloc[0]
    
    print(f"\nSuburb: {top_suburb['suburb']}")
    print(f"ROI Score: {top_suburb['roi_score']:.3f}")
    print(f"\nSEIFA Scores:")
    print(f"  IRSAD (Advantage/Disadvantage): {top_suburb['IRSAD_Score']:.0f} (Decile: {top_suburb['IRSAD_Decile']})")
    print(f"  IRSD (Disadvantage): {top_suburb['IRSD_Score']:.0f} (Decile: {top_suburb['IRSD_Decile']})")
    print(f"  IEO (Education/Occupation): {top_suburb['IEO_Score']:.0f} (Decile: {top_suburb['IEO_Decile']})")
    print(f"  IER (Economic Resources): {top_suburb['IER_Score']:.0f} (Decile: {top_suburb['IER_Decile']})")
    
    if 'Median_tot_prsnl_inc_weekly' in top_suburb:
        print(f"\nIncome Statistics:")
        print(f"  Median Personal Income: ${top_suburb['Median_tot_prsnl_inc_weekly']:.0f}/week")
        if 'Median_tot_hhd_inc_weekly' in top_suburb:
            print(f"  Median Household Income: ${top_suburb['Median_tot_hhd_inc_weekly']:.0f}/week")
    
    # =====================================================
    # Step 7: Export Results
    # =====================================================
    print("\n" + "="*70)
    print("Exporting Results...")
    print("="*70)
    
    # Export to CSV
    output_file = DATA_DIR / "investment_opportunities.csv"
    top_suburbs_full.to_csv(output_file, index=False)
    print(f"✓ Exported top 20 opportunities to: {output_file}")
    
    # Export full scored dataset
    full_output = DATA_DIR / "all_suburbs_scored.csv"
    full_scored = pd.merge(
        metrics,
        merged,
        left_on='suburb_code',
        right_on='SAL_CODE_2021',
        how='left'
    )
    full_scored.to_csv(full_output, index=False)
    print(f"✓ Exported all suburbs with scores to: {full_output}")
    
    # =====================================================
    # Step 8: Summary Statistics
    # =====================================================
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    
    print(f"\nTotal suburbs analyzed: {len(metrics)}")
    print(f"ROI score range: {metrics['roi_score'].min():.3f} to {metrics['roi_score'].max():.3f}")
    print(f"Average ROI score: {metrics['roi_score'].mean():.3f}")
    
    # Distribution of top opportunities by SEIFA decile
    print("\nTop 20 opportunities by SEIFA Advantage Decile:")
    decile_dist = top_suburbs_full['IRSAD_Decile'].value_counts().sort_index()
    for decile, count in decile_dist.items():
        print(f"  Decile {decile}: {count} suburbs")

else:
    print("\n⚠ Cannot perform analysis - required data files missing")
    print("  Please run download_abs_data_fixed.py first")

# =====================================================
# Additional Analysis Ideas
# =====================================================
print("\n" + "="*70)
print("NEXT STEPS FOR ANALYSIS")
print("="*70)
print("""
You can extend this analysis by:

1. Geographic Analysis:
   - Filter by specific states or regions
   - Analyze proximity to CBD, transport, amenities
   - Use GIS data to map opportunities

2. Demographic Deep-Dive:
   - Analyze age distributions (young vs aging populations)
   - Look at household composition
   - Study employment industries

3. Housing Market Analysis:
   - Compare median rent to median income (rental yield proxy)
   - Analyze mortgage stress indicators
   - Look at dwelling types and ownership rates

4. Time Series Analysis:
   - Compare 2021 vs 2016 Census data for growth trends
   - Identify rapidly changing suburbs

5. Machine Learning:
   - Build predictive models for price growth
   - Cluster suburbs by characteristics
   - Identify outliers with unique characteristics

6. External Data Integration:
   - Combine with real estate pricing data
   - Add infrastructure project data
   - Include crime statistics
   - Integrate school ratings

To access more detailed data, explore:
- Other DataPack tables (G01, G03-G61)
- TableBuilder for custom queries
- ABS Time Series data for trends
""")

print("\n" + "="*70)
print("✅ Analysis Complete!")
print("="*70)