"""Post-mortem Agent - thin wrapper around trading.postmortem for the
agent-oriented API/routes layer."""
from trading.postmortem import generate_postmortem


def run_postmortem_agent(trade, ai_service):
    return generate_postmortem(trade, ai_service=ai_service)
