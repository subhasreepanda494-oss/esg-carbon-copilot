def calculate_emissions(quantity: float, factor: float):
    if quantity < 0:
        raise ValueError("Quantity cannot be negative")

    if factor < 0:
        raise ValueError("Emission factor cannot be negative")

    emissions = quantity * factor

    return {
        "quantity": quantity,
        "factor": factor,
        "emissions_kg_co2e": round(emissions, 4),
        "formula": f"{quantity} × {factor} = {round(emissions, 4)} kgCO2e"
    }