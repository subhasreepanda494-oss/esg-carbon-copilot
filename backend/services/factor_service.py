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
                row_activity == activity.strip().lower()
                and
                row_unit == unit.strip().lower()
            ):

                factor_status = row.get(
                    "status", "UNVERIFIED"
                ).strip().upper()

                try:
                    factor = float(row["factor"])
                except (ValueError, TypeError):
                    return {
                        "status": "UNVERIFIED",
                        "message": "Emission factor is not a valid number."
                    }

                # DEMO factors must never be treated as verified
                if factor_status != "OFFICIAL":
                    return {
                        "status": "UNVERIFIED",
                        "activity": row["activity"],
                        "unit": row["unit"],
                        "factor": factor,
                        "source": row.get("source", "Unknown"),
                        "year": row.get("year", "Unknown"),
                        "factor_status": factor_status,
                        "message": (
                            "Emission factor exists, but it is not "
                            "officially verified."
                        )
                    }

                return {
                    "status": "VERIFIED",
                    "activity": row["activity"],
                    "unit": row["unit"],
                    "factor": factor,
                    "source": row.get("source", "Unknown"),
                    "year": row.get("year", "Unknown"),
                    "factor_status": factor_status,
                    "provenance": {
                        "source": row.get("source", "Unknown"),
                        "year": row.get("year", "Unknown"),
                        "status": factor_status
                    }
                }

    return {
        "status": "UNVERIFIED",
        "message": "No verified emission factor found."
    }