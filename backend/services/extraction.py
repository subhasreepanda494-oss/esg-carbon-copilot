from pathlib import Path
from pypdf import PdfReader
import re


def extract_pdf_text(file_path: str):
    path = Path(file_path)

    if not path.exists():
        return {
            "status": "ERROR",
            "message": "File not found."
        }

    try:
        reader = PdfReader(str(path))
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Could not read PDF: {str(e)}"
        }

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    if not text.strip():
        return {
            "status": "UNVERIFIED",
            "message": "No readable text found in PDF."
        }

    return {
        "status": "SUCCESS",
        "filename": path.name,
        "text": text.strip()
    }


def extract_activity_data(text: str):
    text_lower = text.lower()

    activity = None
    unit = None

    # Electricity
    if "electricity" in text_lower:
        activity = "Electricity"
        unit = "kWh"

    # Diesel
    elif "diesel" in text_lower:
        activity = "Diesel"
        unit = "L"

    # Petrol
    elif "petrol" in text_lower:
        activity = "Petrol"
        unit = "L"

    # Quantity extraction
    patterns = [
        r"(\d+(?:\.\d+)?)\s*kwh",
        r"(\d+(?:\.\d+)?)\s*litres",
        r"(\d+(?:\.\d+)?)\s*l\b"
    ]

    quantity = None

    for pattern in patterns:
        match = re.search(pattern, text_lower)

        if match:
            quantity = float(match.group(1))
            break

    # Activity or quantity missing
    if not activity or quantity is None:
        return {
            "status": "UNVERIFIED",
            "message": (
                "Could not reliably identify "
                "activity and quantity."
            )
        }

    return {
        "status": "SUCCESS",
        "activity": activity,
        "quantity": quantity,
        "unit": unit
    }