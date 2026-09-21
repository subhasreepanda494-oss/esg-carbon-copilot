import re


GREENWASHING_PATTERNS = [
    r"\b100%\s*carbon\s*neutral\b",
    r"\b100%\s*sustainable\b",
    r"\bzero\s*carbon\b",
    r"\bcompletely\s*green\b",
    r"\bcarbon\s*free\b",
    r"\bnet\s*zero\b",
]


def detect_greenwashing(text: str):

    if not text:
        return {
            "status": "NO_TEXT",
            "flags": []
        }

    flags = []

    for pattern in GREENWASHING_PATTERNS:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:
            flags.append({
                "claim": match,
                "status": "UNVERIFIED",
                "reason": (
                    "Sustainability claim requires "
                    "supporting evidence."
                )
            })

    if flags:
        return {
            "status": "REVIEW_REQUIRED",
            "flags": flags
        }

    return {
        "status": "NO_UNVERIFIED_CLAIMS",
        "flags": []
    }