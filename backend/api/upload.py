from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import shutil
import csv

from backend.services.extraction import (
    extract_pdf_text,
    extract_activity_data
)
from backend.services.classifier import classify_scope
from backend.services.factor_service import get_emission_factor
from backend.services.calculator import calculate_emissions
from backend.services.greenwashing import detect_greenwashing
from backend.database import save_audit


router = APIRouter()


OFFICIAL_SOURCE_FIELDS = (
    "factor_version",
    "source_url",
    "source_row_id"
)


def factor_metadata(factor_data):
    return {
        field: factor_data.get(field)
        for field in OFFICIAL_SOURCE_FIELDS
    }


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def process_activity(activity, quantity, unit, source_file):
    """
    Process one ESG activity.

    OFFICIAL factor:
        -> VERIFIED
        -> Calculate CO2e
        -> Save audit

    REVIEW_REQUIRED factor:
        -> REVIEW_REQUIRED
        -> Do NOT calculate CO2e
        -> Save audit

    Missing factor:
        -> UNVERIFIED
        -> Do NOT calculate CO2e
        -> Save audit
    """

    # -----------------------------
    # 1. Scope classification
    # -----------------------------
    scope = classify_scope(activity)

    # -----------------------------
    # 2. Factor lookup
    # -----------------------------
    factor_data = get_emission_factor(
        activity,
        unit
    )

    # -----------------------------
    # 3. VERIFIED factor
    # -----------------------------
    if factor_data["status"] == "VERIFIED":

        result = calculate_emissions(
            quantity,
            factor_data["factor"]
        )

        audit_record = {
            "activity": activity,
            "scope": scope,
            "quantity": quantity,
            "unit": unit,
            "factor": factor_data["factor"],
            "factor_source": factor_data["source"],
            "factor_year": factor_data["year"],
            "emissions_kg_co2e": result["emissions_kg_co2e"],
            "formula": result["formula"],
            "status": "VERIFIED",
            "source_file": source_file,
            **factor_metadata(factor_data)
        }

        save_audit(audit_record)

        return {
            "status": "VERIFIED",
            "activity": activity,
            "scope": scope,
            "quantity": quantity,
            "unit": unit,
            "factor": factor_data["factor"],
            "factor_source": factor_data["source"],
            "factor_year": factor_data["year"],
            "emissions_kg_co2e": result["emissions_kg_co2e"],
            "formula": result["formula"],
            "source_file": source_file,
            **factor_metadata(factor_data)
        }

    # -----------------------------
    # 4. REVIEW_REQUIRED factor
    # -----------------------------
    if factor_data.get("status") == "REVIEW_REQUIRED":

        audit_record = {
            "activity": activity,
            "scope": scope,
            "quantity": quantity,
            "unit": unit,
            "factor": factor_data.get("factor"),
            "factor_source": factor_data.get(
                "source",
                "Unknown"
            ),
            "factor_year": factor_data.get(
                "year",
                "Unknown"
            ),
            "emissions_kg_co2e": 0,
            "formula": "Not calculated - direct official factor match required",
            "status": "REVIEW_REQUIRED",
            "source_file": source_file,
            **factor_metadata(factor_data)
        }

        save_audit(audit_record)

        return {
            "status": "REVIEW_REQUIRED",
            "activity": activity,
            "scope": scope,
            "quantity": quantity,
            "unit": unit,
            "factor": factor_data.get("factor"),
            "factor_source": factor_data.get(
                "source",
                "Unknown"
            ),
            "factor_year": factor_data.get(
                "year",
                "Unknown"
            ),
            "emissions_kg_co2e": 0,
            "formula": "Not calculated - direct official factor match required",
            "message": factor_data.get(
                "message",
                "A direct official factor match is required."
            ),
            "source_file": source_file,
            **factor_metadata(factor_data)
        }

    # -----------------------------
    # 5. Missing factor
    # -----------------------------
    audit_record = {
        "activity": activity,
        "scope": scope,
        "quantity": quantity,
        "unit": unit,
        "factor": None,
        "factor_source": "Not found",
        "factor_year": "N/A",
        "emissions_kg_co2e": 0,
        "formula": "Not calculated - no verified emission factor found",
        "status": "UNVERIFIED",
        "source_file": source_file,
        **factor_metadata(factor_data)
    }

    save_audit(audit_record)

    return {
        "status": "UNVERIFIED",
        "activity": activity,
        "scope": scope,
        "quantity": quantity,
        "unit": unit,
        "factor": None,
        "factor_source": "Not found",
        "factor_year": "N/A",
        "emissions_kg_co2e": 0,
        "formula": "Not calculated",
        "message": "No verified emission factor found.",
        "source_file": source_file,
        **factor_metadata(factor_data)
    }


# =========================================================
# UPLOAD API
# =========================================================

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...)
):

    allowed = [
        ".pdf",
        ".csv",
        ".xlsx",
        ".xls"
    ]

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in allowed:
        return {
            "status": "ERROR",
            "message": (
                "Only PDF, CSV and Excel files are allowed."
            )
        }

    # -----------------------------
    # Save uploaded file
    # -----------------------------

    # Harden against path traversal: never trust the client-supplied filename.
    # Only the basename is used so an attacker cannot escape the UPLOAD_DIR.
    safe_filename = Path(file.filename).name
    file_path = UPLOAD_DIR / safe_filename

    with open(
        file_path,
        "wb"
    ) as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    # =====================================================
    # PDF
    # =====================================================

    if extension == ".pdf":

        extraction = extract_pdf_text(
            str(file_path)
        )

        greenwashing = detect_greenwashing(
            extraction.get(
                "text",
                ""
            )
        )

        if extraction["status"] != "SUCCESS":

            return {
                "status": "ERROR",
                "filename": file.filename,
                "extraction": extraction,
                "greenwashing_check": greenwashing
            }

        activity_data = extract_activity_data(
            extraction["text"]
        )

        if activity_data["status"] != "SUCCESS":

            return {
                "status": "UNVERIFIED",
                "filename": file.filename,
                "extraction": activity_data,
                "greenwashing_check": greenwashing
            }

        result = process_activity(
            activity_data["activity"],
            activity_data["quantity"],
            activity_data["unit"],
            file.filename
        )

        return {
            "status": "SUCCESS",
            "filename": file.filename,
            **result,
            "calculation_status": result["status"],
            "audit_saved": True,
            "greenwashing_check": greenwashing
        }

    # =====================================================
    # CSV
    # =====================================================

    if extension == ".csv":

        records = []

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8-sig"
            ) as csvfile:

                reader = csv.DictReader(
                    csvfile
                )

                # Detect a social/governance CSV (metric,value,unit) being sent
                # to the environmental activity endpoint. Otherwise every row is
                # skipped and the upload silently returns 0 records.
                fieldnames = reader.fieldnames or []
                if "metric" in fieldnames and "activity" not in fieldnames:
                    return {
                        "status": "ERROR",
                        "filename": file.filename,
                        "message": (
                            "This CSV uses the governance/social format "
                            "(metric, value, unit). Upload governance metrics to "
                            "/upload-governance or social metrics to /upload-social. "
                            "Environmental activity CSVs must use: activity, quantity, unit."
                        ),
                        "records_processed": 0,
                        "records": []
                    }

                for row in reader:

                    activity = row.get(
                        "activity",
                        ""
                    ).strip()

                    quantity_text = row.get(
                        "quantity",
                        ""
                    ).strip()

                    unit = row.get(
                        "unit",
                        ""
                    ).strip()

                    # Skip incomplete rows
                    if (
                        not activity
                        or not quantity_text
                        or not unit
                    ):
                        continue

                    try:
                        quantity = float(
                            quantity_text
                        )

                    except ValueError:
                        records.append({
                            "status": "UNVERIFIED",
                            "activity": activity,
                            "quantity": quantity_text,
                            "unit": unit,
                            "message": (
                                "Quantity is not a valid number."
                            )
                        })

                        continue

                    result = process_activity(
                        activity,
                        quantity,
                        unit,
                        file.filename
                    )

                    records.append(result)

            # -----------------------------
            # Count statuses
            # -----------------------------

            verified = [
                r for r in records
                if r.get("status") == "VERIFIED"
            ]

            review_required = [
                r for r in records
                if r.get("status") == "REVIEW_REQUIRED"
            ]

            unverified = [
                r for r in records
                if r.get("status") == "UNVERIFIED"
            ]

            total_co2e = sum(
                r.get(
                    "emissions_kg_co2e",
                    0
                ) or 0
                for r in records
            )

            if not records:
                return {
                    "status": "SUCCESS",
                    "filename": file.filename,
                    "records_processed": 0,
                    "verified_records": 0,
                    "review_required_records": 0,
                    "unverified_records": 0,
                    "total_emissions_kg_co2e": 0,
                    "records": [],
                    "message": (
                        "No processable activity records were found. The CSV "
                        "must contain activity, quantity and unit columns with "
                        "at least one complete row."
                    )
                }

            return {
                "status": "SUCCESS",
                "filename": file.filename,

                "records_processed": len(records),

                "verified_records": len(
                    verified
                ),

                "review_required_records": len(
                    review_required
                ),

                "unverified_records": len(
                    unverified
                ),

                "total_emissions_kg_co2e": round(
                    total_co2e,
                    4
                ),

                "records": records
            }

        except Exception as e:

            return {
                "status": "ERROR",
                "filename": file.filename,
                "message": str(e)
            }

    # =====================================================
    # EXCEL
    # =====================================================

    if extension in [
        ".xlsx",
        ".xls"
    ]:

        return {
            "status": "UNVERIFIED",
            "filename": file.filename,
            "message": (
                "Excel upload is accepted, "
                "but CSV processing is currently "
                "enabled for the MVP."
            )
        }

# =========================================================
# SOCIAL AND GOVERNANCE UPLOAD APIs
# =========================================================

def process_sg_csv(file_path: Path, filename: str, category: str):
    records = []
    try:
        with open(file_path, "r", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)

            fieldnames = reader.fieldnames or []

            # Detect an environmental activity CSV being sent to the
            # social/governance endpoint. Without this check every row's
            # metric column is empty, so the upload silently returns 0
            # records instead of a useful message.
            if "activity" in fieldnames and "metric" not in fieldnames:
                return {
                    "status": "ERROR",
                    "filename": filename,
                    "category": category,
                    "records_processed": 0,
                    "verified_records": 0,
                    "invalid_records": 0,
                    "records": [],
                    "message": (
                        f"This CSV uses the activity format "
                        f"(activity, quantity, unit). {category} metrics use "
                        f"the format: metric, value, unit. Upload activity data "
                        f"to /upload instead."
                    )
                }

            for row in reader:
                metric = row.get("metric", "").strip()
                value_text = row.get("value", "").strip()
                unit = row.get("unit", "").strip()

                if not metric or not value_text:
                    continue

                # Skip placeholder/template rows so they do not pollute the
                # audit trail as if they were real metrics.
                metric_lower = metric.lower()
                if (
                    "sample data" in metric_lower
                    or "replace" in metric_lower
                    or "template" in metric_lower
                ):
                    continue

                try:
                    value = float(value_text)
                    status = "VERIFIED"
                except ValueError:
                    status = "INVALID"
                    value = 0

                record = {
                    "activity": metric,
                    "scope": "N/A",
                    "quantity": value,
                    "unit": unit,
                    "status": status,
                    "source_file": filename,
                    "category": category,
                    "formula": "Direct Metric",
                    "emissions_kg_co2e": 0
                }
                save_audit(record)
                records.append(record)

        verified = [r for r in records if r["status"] == "VERIFIED"]
        invalid = [r for r in records if r["status"] == "INVALID"]

        if not records:
            return {
                "status": "SUCCESS",
                "filename": filename,
                "category": category,
                "records_processed": 0,
                "verified_records": 0,
                "invalid_records": 0,
                "records": [],
                "message": (
                    f"No valid {category} metric records were found. "
                    f"Please upload a CSV with columns: metric, value, unit. "
                    f"Download a template from /template/{category.lower()}. "
                    f"If this file is only a template with sample rows, "
                    f"replace them with your organisation's real metrics before uploading."
                )
            }

        return {
            "status": "SUCCESS",
            "filename": filename,
            "category": category,
            "records_processed": len(records),
            "verified_records": len(verified),
            "invalid_records": len(invalid),
            "records": records
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "filename": filename,
            "message": str(e)
        }

@router.post("/upload-social")
async def upload_social_file(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return process_sg_csv(file_path, file.filename, "Social")

@router.post("/upload-governance")
async def upload_governance_file(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return process_sg_csv(file_path, file.filename, "Governance")


from fastapi.responses import StreamingResponse
import io

@router.get("/template/{category}")
async def download_template(category: str):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric", "value", "unit"])
    
    if category.lower() == "social":
        writer.writerow(["employee_turnover_pct", "12.5", "%"])
        writer.writerow(["training_hours_per_employee", "40", "hours"])
        writer.writerow(["workplace_incidents", "2", "incidents"])
        writer.writerow(["employee_satisfaction_pct", "85", "%"])
        writer.writerow(["diversity_female_pct", "45", "%"])
    elif category.lower() == "governance":
        writer.writerow(["board_independent_pct", "75", "%"])
        writer.writerow(["ethics_incidents", "0", "incidents"])
        writer.writerow(["data_privacy_incidents", "0", "incidents"])
        writer.writerow(["whistleblower_cases", "1", "cases"])
    
    # SAMPLE DATA row explicitly requested
    writer.writerow(["SAMPLE DATA - REPLACE WITH REAL METRICS", "0", "N/A"])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={category}_template.csv"}
    )
