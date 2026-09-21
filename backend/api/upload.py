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

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def process_activity(activity, quantity, unit, source_file):
    """
    Process one ESG activity.

    OFFICIAL factor:
        -> VERIFIED
        -> Calculate CO2e
        -> Save audit

    DEMO factor:
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
            "source_file": source_file
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
            "source_file": source_file
        }

    # -----------------------------
    # 4. DEMO / unverified factor
    # -----------------------------
    factor_status = factor_data.get(
        "factor_status",
        ""
    ).upper()

    if factor_status == "DEMO":

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
            "formula": "Not calculated - emission factor requires verification",
            "status": "REVIEW_REQUIRED",
            "source_file": source_file
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
            "formula": "Not calculated - factor requires verification",
            "message": "Emission factor is DEMO and requires verification.",
            "source_file": source_file
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
        "source_file": source_file
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
        "source_file": source_file
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

    file_path = UPLOAD_DIR / file.filename

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