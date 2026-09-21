from fastapi import APIRouter
from backend.database import get_audit_logs

router = APIRouter()


@router.get("/audit")
def get_audit():

    records = get_audit_logs()

    total = 0
    scope1 = 0
    scope2 = 0
    scope3 = 0

    for record in records:

        emissions = record.get(
            "emissions_kg_co2e",
            0
        ) or 0

        total += emissions

        if record.get("scope") == "Scope 1":
            scope1 += emissions

        elif record.get("scope") == "Scope 2":
            scope2 += emissions

        elif record.get("scope") == "Scope 3":
            scope3 += emissions

    return {
        "status": "success",

        "summary": {
            "total_emissions_kg_co2e": round(total, 4),
            "scope_1_kg_co2e": round(scope1, 4),
            "scope_2_kg_co2e": round(scope2, 4),
            "scope_3_kg_co2e": round(scope3, 4)
        },

        "count": len(records),

        "records": records
    }