from __future__ import annotations

from datetime import datetime
from io import BytesIO, StringIO
import csv
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph, Table, TableStyle

from data_loader import (
    dataset_to_api_rows,
    filter_suburbs,
    get_feature_metadata,
    investment_opportunities,
    load_dataset,
    load_model_artifact,
    opportunities_from_rows,
    predict_from_inputs,
    suburbs_closest_to_roi,
    suburb_names,
    user_input_guidance,
)

app = FastAPI(title="ROI Suburb Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_ARTIFACT = load_model_artifact()
DATA_DF = load_dataset(MODEL_ARTIFACT)
SUBURBS_DATA = dataset_to_api_rows(DATA_DF)
MODEL_FEATURES = MODEL_ARTIFACT.get("features", []) if MODEL_ARTIFACT else []


class PredictRequest(BaseModel):
    suburb_name: Optional[str] = None
    feature_values: dict[str, float] = Field(default_factory=dict)


@app.get("/")
async def root():
    return {"message": "Welcome to the ROI Suburb Finder API"}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "suburbs_loaded": len(SUBURBS_DATA),
        "model_loaded": MODEL_ARTIFACT is not None,
        "model_features": len(MODEL_FEATURES),
    }


@app.get("/api/features")
async def features():
    if MODEL_ARTIFACT is None:
        return {"features": [], "message": "Model not loaded."}
    return {"features": get_feature_metadata(DATA_DF, MODEL_FEATURES)}


@app.get("/api/input-guidance")
async def input_guidance():
    return {"guidance": user_input_guidance(DATA_DF)}


@app.get("/api/model-info")
async def model_info():
    if MODEL_ARTIFACT is None:
        return {
            "model_loaded": False,
            "target": None,
            "feature_count": 0,
            "metrics": {},
        }
    return {
        "model_loaded": True,
        "target": MODEL_ARTIFACT.get("target"),
        "feature_count": len(MODEL_FEATURES),
        "metrics": MODEL_ARTIFACT.get("metrics", {}),
    }


@app.get("/api/suburb-names")
async def get_suburb_names(q: Optional[str] = None, limit: int = 200):
    return {"names": suburb_names(DATA_DF, q=q, limit=limit)}


@app.get("/api/suburbs")
async def get_suburbs(
    name: Optional[str] = None,
    min_roi: Optional[float] = None,
    max_price: Optional[float] = None,
    min_seifa: Optional[float] = None,
    top_n: int = 100,
):
    filtered_data = filter_suburbs(
        SUBURBS_DATA,
        name=name,
        min_roi=min_roi,
        max_price=max_price,
        min_seifa=min_seifa,
    )
    top_n = max(1, min(top_n, 500))
    return filtered_data[:top_n]


@app.get("/api/opportunities")
async def opportunities(top_n: int = 20):
    return investment_opportunities(DATA_DF, top_n=top_n)


@app.get("/api/suburbs-near-roi")
@app.get("/api/suburbs-near-roi/")
@app.get("/api/suburbs_near_roi")
async def suburbs_near_roi(roi: float, top_n: int = 5):
    return {
        "target_roi": roi,
        "suburbs": suburbs_closest_to_roi(SUBURBS_DATA, target_roi=roi, top_n=top_n),
    }


def _format_filters(
    name: Optional[str],
    min_roi: Optional[float],
    max_price: Optional[float],
    min_seifa: Optional[float],
    top_n: int,
) -> dict[str, str]:
    return {
        "Suburb Name Filter": name or "Any",
        "Min ROI (%)": str(min_roi) if min_roi is not None else "Any",
        "Max Mortgage Proxy": str(max_price) if max_price is not None else "Any",
        "Min SEIFA": str(min_seifa) if min_seifa is not None else "Any",
        "Top N": str(top_n),
    }


@app.get("/api/report/csv")
async def download_report_csv(
    name: Optional[str] = None,
    min_roi: Optional[float] = None,
    max_price: Optional[float] = None,
    min_seifa: Optional[float] = None,
    top_n: int = 20,
):
    filtered = filter_suburbs(
        SUBURBS_DATA,
        name=name,
        min_roi=min_roi,
        max_price=max_price,
        min_seifa=min_seifa,
    )
    insights = opportunities_from_rows(filtered, top_n=top_n)
    summary = insights["summary"]
    opportunities = insights["opportunities"]
    filters = _format_filters(name, min_roi, max_price, min_seifa, top_n)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Report Generated At", datetime.utcnow().isoformat() + "Z"])
    writer.writerow([])
    writer.writerow(["Current Filters"])
    writer.writerow(["Filter", "Value"])
    for k, v in filters.items():
        writer.writerow([k, v])
    writer.writerow([])
    writer.writerow(["Summary Metrics"])
    writer.writerow(["Metric", "Value"])
    for k, v in summary.items():
        writer.writerow([k, v])
    writer.writerow([])
    writer.writerow(["Top Opportunities"])
    writer.writerow(["name", "roi_percent", "price", "rent", "seifa_score", "tags"])
    for row in opportunities:
        writer.writerow(
            [
                row.get("name", ""),
                round(float(row.get("roi", 0) or 0) * 100, 2),
                row.get("price", 0),
                row.get("rent", 0),
                row.get("seifa_score", 0),
                " | ".join(row.get("insight_tags", [])),
            ]
        )

    filename = f"suburb_recommendation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/report/pdf")
async def download_report_pdf(
    name: Optional[str] = None,
    min_roi: Optional[float] = None,
    max_price: Optional[float] = None,
    min_seifa: Optional[float] = None,
    top_n: int = 20,
):
    filtered = filter_suburbs(
        SUBURBS_DATA,
        name=name,
        min_roi=min_roi,
        max_price=max_price,
        min_seifa=min_seifa,
    )
    insights = opportunities_from_rows(filtered, top_n=top_n)
    summary = insights["summary"]
    opportunities = insights["opportunities"]
    filters = _format_filters(name, min_roi, max_price, min_seifa, top_n)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Suburb Recommendation Report", styles["Title"]))
    story.append(Paragraph(f"Generated: {datetime.utcnow().isoformat()}Z", styles["Normal"]))
    story.append(Spacer(1, 10))

    filter_rows = [["Filter", "Value"]] + [[k, v] for k, v in filters.items()]
    filter_table = Table(filter_rows, colWidths=[220, 420])
    filter_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(Paragraph("Current Filters", styles["Heading3"]))
    story.append(filter_table)
    story.append(Spacer(1, 10))

    summary_rows = [["Metric", "Value"]] + [[k, str(v)] for k, v in summary.items()]
    summary_table = Table(summary_rows, colWidths=[280, 200])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#115e59")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(Paragraph("Summary Metrics", styles["Heading3"]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    opp_rows = [["Suburb", "ROI %", "Mortgage", "Rent", "SEIFA", "Tags"]]
    for row in opportunities:
        opp_rows.append(
            [
                str(row.get("name", "")),
                f"{float(row.get('roi', 0) or 0) * 100:.2f}",
                str(row.get("price", 0)),
                str(row.get("rent", 0)),
                str(round(float(row.get("seifa_score", 0) or 0), 2)),
                ", ".join(row.get("insight_tags", [])),
            ]
        )
    opp_table = Table(opp_rows, colWidths=[180, 70, 80, 70, 70, 240])
    opp_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5a4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(Paragraph("Top Opportunities", styles["Heading3"]))
    story.append(opp_table)

    doc.build(story)
    buffer.seek(0)
    filename = f"suburb_recommendation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/predict")
async def predict(payload: PredictRequest):
    if MODEL_ARTIFACT is None:
        return {"error": "Model is not loaded. Run model_training.py first."}

    return predict_from_inputs(
        df=DATA_DF,
        artifact=MODEL_ARTIFACT,
        suburb_name=payload.suburb_name,
        feature_values=payload.feature_values,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
