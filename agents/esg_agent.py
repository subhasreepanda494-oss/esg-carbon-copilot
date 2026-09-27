"""
Lyzr-backed ESG compliance agent.

IMPORTANT: the Lyzr SDK is contacted lazily, never at import time.

The agent used to be built while this module was being imported, which meant a
network call to the Lyzr API ran during ``import backend.main``. Any DNS blip,
offline machine, expired key or Lyzr outage therefore crashed the *entire*
FastAPI application before it could serve a single request, even though only
one endpoint (/ai-analyze) actually needs the AI.

Building lazily keeps the deterministic core of the product (classification,
factor lookup, calculation, uploads, audit, dashboard) fully available, and
degrades only the optional AI feature.
"""

import logging
import os
import threading

from dotenv import load_dotenv

from backend.services.classifier import classify_scope
from backend.services.factor_service import get_emission_factor
from backend.services.calculator import calculate_emissions

load_dotenv()

logger = logging.getLogger(__name__)


class AgentUnavailableError(RuntimeError):
    """
    Raised when the optional Lyzr AI backend cannot be used.

    Surfaced by the API layer as HTTP 503 so the caller gets an actionable
    message instead of an opaque 500 or a dead application.
    """


AGENT_NAME = "ESG Carbon Compliance Copilot"
AGENT_PROVIDER = os.getenv("LYZR_PROVIDER", "gpt-4o")
AGENT_ROLE = "ESG carbon accounting compliance assistant"
AGENT_GOAL = (
    "Analyze ESG activity data using deterministic tools "
    "and produce traceable results."
)
AGENT_TEMPERATURE = 0.1


# ============================================================
# DETERMINISTIC TOOLS (no network - always safe to import)
# ============================================================

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


AGENT_INSTRUCTIONS = """
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
"""

TOOLS = (classify_esg_scope, lookup_emission_factor, calculate_co2e)


# ============================================================
# LAZY, CACHED AGENT CONSTRUCTION (network happens here only)
# ============================================================

_build_lock = threading.Lock()
_agent = None


def _find_existing_agent(studio):
    """
    Return an already-provisioned agent with our name, if any.

    Without this, every process start (and every --reload restart) created a
    brand new duplicate agent in Lyzr Studio.
    """
    try:
        agents = studio.agents.list()
    except Exception as exc:
        logger.warning("Could not list Lyzr agents, will create one: %s", exc)
        return None

    for agent in agents:
        if getattr(agent, "name", None) == AGENT_NAME:
            return agent

    return None


def _build_agent():
    """
    Build or reuse the remote Lyzr agent. Performs network I/O.
    """
    try:
        from lyzr import Studio
    except ImportError as exc:
        raise AgentUnavailableError(
            "The optional 'lyzr-adk' package is not installed, so AI analysis "
            "is unavailable. Install it with: python -m pip install lyzr-adk"
        ) from exc

    if not os.getenv("LYZR_API_KEY"):
        raise AgentUnavailableError(
            "LYZR_API_KEY is not set. Add it to the .env file in the project "
            "root and restart the server to enable AI analysis."
        )

    try:
        studio = Studio()
    except Exception as exc:
        raise AgentUnavailableError(
            f"Could not authenticate with the Lyzr API: {exc}"
        ) from exc

    try:
        agent = _find_existing_agent(studio)

        if agent is None:
            agent = studio.create_agent(
                name=AGENT_NAME,
                provider=AGENT_PROVIDER,
                role=AGENT_ROLE,
                goal=AGENT_GOAL,
                instructions=AGENT_INSTRUCTIONS,
                temperature=AGENT_TEMPERATURE,
            )

        # Tool registration is local/in-memory, so re-running it on a reused
        # agent is cheap and idempotent.
        for tool in TOOLS:
            agent.add_tool(tool)

        return agent

    except Exception as exc:
        raise AgentUnavailableError(
            f"Could not prepare the Lyzr ESG agent: {exc}. Check network "
            "connectivity and that LYZR_API_KEY is valid, then retry."
        ) from exc


def get_agent():
    """
    Return the shared Lyzr agent, creating it on first use only.

    Raises:
        AgentUnavailableError: if the AI backend cannot be configured/reached.
    """
    global _agent

    if _agent is not None:
        return _agent

    with _build_lock:
        # Re-check: another thread may have won the race while we waited.
        if _agent is None:
            _agent = _build_agent()

    return _agent


def reset_agent():
    """
    Drop the cached agent so the next call rebuilds it.

    Useful after fixing .env or after a transient network failure.
    """
    global _agent

    with _build_lock:
        _agent = None


def ai_available() -> bool:
    """
    Report whether the AI feature is usable, without raising.
    """
    try:
        get_agent()
        return True
    except AgentUnavailableError:
        return False


def run_esg_agent(message: str):
    """
    Run the Lyzr ESG compliance agent.

    Raises:
        AgentUnavailableError: if the AI backend is unavailable or the call
            fails. The deterministic endpoints never take this path.
    """
    agent = get_agent()

    try:
        response = agent.run(message)
    except Exception as exc:
        # A stale handle or a dropped connection should not poison the cache:
        # rebuild from scratch on the next request.
        reset_agent()
        raise AgentUnavailableError(
            f"The Lyzr AI analysis call failed: {exc}"
        ) from exc

    return response.response

