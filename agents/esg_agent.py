from dotenv import load_dotenv
from lyzr import Studio

from backend.services.classifier import classify_scope
from backend.services.factor_service import get_emission_factor
from backend.services.calculator import calculate_emissions

load_dotenv()


def classify_esg_scope(activity: str) -> str:
    """
    Classify an ESG activity into Scope 1, Scope 2,
    Scope 3 or UNCLASSIFIED.
    """
    return classify_scope(activity)


def lookup_emission_factor(activity: str, unit: str) -> dict:
    """
    Look up the emission factor from the project's
    deterministic factor database.
    """
    return get_emission_factor(activity, unit)


def calculate_co2e(quantity: float, factor: float) -> dict:
    """
    Deterministic CO2e calculation.
    """
    return calculate_emissions(quantity, factor)


studio = Studio()

esg_agent = studio.create_agent(
    name="ESG Carbon Compliance Copilot",
    provider="gpt-4o",
    role="ESG carbon accounting compliance assistant",
    goal=(
        "Analyze ESG activity data using deterministic tools "
        "and produce traceable results."
    ),
    instructions="""
You are an ESG Carbon Accounting Compliance Copilot.

Follow these rules strictly:

1. Classify the activity using the scope classification tool.
2. Never invent an emission factor.
3. Always use the emission factor lookup tool.
4. Only calculate CO2e when a usable emission factor is available.
5. Always use the deterministic calculator for mathematical calculations.
6. Clearly identify UNVERIFIED information.
7. Never present DEMO factors as official factors.
8. Explain the calculation formula when a calculation is performed.
9. Mention the emission factor source and year when available.
10. Do not fabricate regulatory or sustainability claims.
11. If data is missing, say that the result requires review.

The deterministic backend tools are the source of truth
for classification, emission factors and calculations.
""",
    temperature=0.1,
)

esg_agent.add_tool(classify_esg_scope)
esg_agent.add_tool(lookup_emission_factor)
esg_agent.add_tool(calculate_co2e)


def run_esg_agent(message: str):
    """
    Run the Lyzr ESG compliance agent.
    """
    response = esg_agent.run(message)
    return response.response