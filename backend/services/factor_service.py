import csv
from pathlib import Path

FACTOR_FILE = Path("backend/data/emission_factors.csv")


def get_emission_factor(activity: str, unit: str):

    if not FACTOR_FILE.exists():
        return {
            "status": "UNVERIFIED",
            "message": "Emission factor database not found."
        }

    with open(
        FACTOR_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            row_activity = row.get(
                "activity", ""
            ).strip().lower()

            row_unit = row.get(
                "unit", ""
            ).strip().lower()

            if (
                row_activity != activity.strip().lower()
                or row_unit != unit.strip().lower()
            ):
                continue

            factor_status = row.get(
                "status", "REVIEW_REQUIRED"
            ).strip().upper()

            metadata = {
                "activity": row.get("activity", ""),
                "unit": row.get("unit", ""),
                "source": row.get("source", "Unknown"),
                "year": row.get("year", "Unknown"),
                "factor_status": factor_status,
                "scope": row.get("scope", ""),
                "factor_version": row.get("factor_version", "Unknown"),
                "source_url": row.get("source_url", ""),
                "source_row_id": row.get("source_row_id", ""),
                "review_reason": row.get("review_reason", "")
            }

            # Only directly verified rows may be used for calculation.
            if factor_status != "OFFICIAL":
                return {
                    "status": "REVIEW_REQUIRED",
                    "factor": None,
                    "message": (
                        metadata["review_reason"]
                        or "A direct official factor match is required."
                    ),
                    **metadata
                }

            try:
                factor = float(row["factor"])
            except (ValueError, TypeError, KeyError):
                return {
                    "status": "UNVERIFIED",
                    "message": "Official emission factor is not a valid number.",
                    **metadata
                }

            return {
                "status": "VERIFIED",
                "factor": factor,
                "provenance": {
                    "source": metadata["source"],
                    "year": metadata["year"],
                    "status": factor_status,
                    "scope": metadata["scope"],
                    "factor_version": metadata["factor_version"],
                    "source_url": metadata["source_url"],
                    "source_row_id": metadata["source_row_id"]
                },
                **metadata
            }

    return {
        "status": "UNVERIFIED",
        "message": "No verified emission factor found."
    }
