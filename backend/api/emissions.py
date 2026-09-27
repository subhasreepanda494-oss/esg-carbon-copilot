from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.classifier import classify_scope
from backend.services.factor_service import get_emission_factor
from backend.services.calculator import calculate_emissions
from backend.database import save_audit

from agents.esg_agent import run_esg_agent, AgentUnavailableError


router = APIRouter()


class CalculateRequest(BaseModel):
    activity: str
    quantity: float
    unit: str


# ============================================================
# NORMAL DETERMINISTIC CALCULATION
# ============================================================

@router.post("/calculate")
def calculate(request: CalculateRequest):

    scope = classify_scope(request.activity)

    factor_data = get_emission_factor(
        request.activity,
        request.unit
    )

    if factor_data["status"] != "VERIFIED":
        raise HTTPException(
            status_code=400,
            detail={
                "status": factor_data.get(
                    "status",
                    "REVIEW_REQUIRED"
                ),
                "message": factor_data["message"],
                "factor_version": factor_data.get(
                    "factor_version"
                ),
                "source_url": factor_data.get(
                    "source_url"
                ),
                "source_row_id": factor_data.get(
                    "source_row_id"
                )
            }
        )

    result = calculate_emissions(
        request.quantity,
        factor_data["factor"]
    )

    audit_record = {
        "activity": request.activity,
        "scope": scope,
        "quantity": request.quantity,
        "unit": request.unit,
        "factor": factor_data["factor"],
        "factor_source": factor_data["source"],
        "factor_year": factor_data["year"],
        "factor_version": factor_data.get(
            "factor_version"
        ),
        "source_url": factor_data.get(
            "source_url"
        ),
        "source_row_id": factor_data.get(
            "source_row_id"
        ),
        "emissions_kg_co2e": result["emissions_kg_co2e"],
        "formula": result["formula"],
        "status": "VERIFIED"
    }

    save_audit(audit_record)

    return audit_record


# ============================================================
# LYZR AI ESG ANALYSIS
# ============================================================

@router.post("/ai-analyze")
def ai_analyze(request: CalculateRequest):

    message = f"""
Analyze this ESG carbon accounting activity.

Activity: {request.activity}
Quantity: {request.quantity}
Unit: {request.unit}

Perform the following:

1. Classify the activity into Scope 1, Scope 2,
   Scope 3 or UNCLASSIFIED.

2. Look up the emission factor using the deterministic
   emission factor database.

3. Do NOT invent an emission factor. The official registry is
   authoritative and contains only directly verified UK factors.

4. If a usable official factor exists, calculate CO2e using
   the deterministic calculator. Otherwise state REVIEW REQUIRED.

5. Report:
   - Scope
   - Quantity
   - Unit
   - Emission factor
   - Factor source
   - Factor year
   - CO2e result
   - Calculation formula

6. If the factor is unavailable or unverified,
   clearly say REVIEW REQUIRED.

7. Never describe a REVIEW_REQUIRED or unverified factor as official.
"""

    try:

        response = run_esg_agent(message)

        return {
            "status": "success",
            "activity": request.activity,
            "quantity": request.quantity,
            "unit": request.unit,
            "ai_analysis": response
        }

    except AgentUnavailableError as e:

        # AI is an optional enhancement. The deterministic calculation
        # endpoints still work, so report this as "service unavailable"
        # rather than an unexpected server error.
        raise HTTPException(
            status_code=503,
            detail={
                "status": "AI_UNAVAILABLE",
                "message": str(e),
                "hint": (
                    "Deterministic calculation via /calculate is unaffected. "
                    "Retry once the Lyzr connection or API key is fixed."
                )
            }
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail={
                "status": "ERROR",
                "message": str(e)
            }
        )
