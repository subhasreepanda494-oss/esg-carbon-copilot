def classify_scope(activity: str):
    text = activity.lower()

    if any(word in text for word in [
        "diesel",
        "petrol",
        "natural gas",
        "fuel"
    ]):
        return "Scope 1"

    if any(word in text for word in [
        "electricity",
        "grid electricity",
        "power"
    ]):
        return "Scope 2"

    if any(word in text for word in [
        "air travel",
        "flight",
        "hotel",
        "employee travel",
        "freight",
        "shipping",
        "transport"
    ]):
        return "Scope 3"

    return "UNCLASSIFIED"