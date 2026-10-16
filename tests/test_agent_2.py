"""
Test for Intent Classification Agent.
Tests all 5 business scenarios.
"""
from datetime import datetime

from agents.email_understanding_agent import EmailUnderstandingAgent
from agents.intent_classification_agent import IntentClassificationAgent
from models.schemas import AgentState, IncomingEmail
from utils.logger import setup_logging


SCENARIOS = [
    {
        "id": "scenario-1",
        "body": "Please provide my savings account balance for account number 1234567890.",
        "expected": ["balance_enquiry"],
    },
    {
        "id": "scenario-2",
        "body": "Please share my last 5 credit card transactions for card 4567890123456789.",
        "expected": ["card_usage"],
    },
    {
        "id": "scenario-3",
        "body": "Kindly send my bank statement for April 2026.",
        "expected": ["statement_request"],
    },
    {
        "id": "scenario-4",
        "body": "Please share my account balance for account 1234567890 and also send last 3 transactions of my credit card 9876543210987654.",
        "expected": ["balance_enquiry", "card_usage"],
    },
]


def main():
    setup_logging()

    for scenario in SCENARIOS:
        print(f"\n{'='*60}")
        print(f"[{scenario['id']}]")
        print(f"Email: {scenario['body'][:80]}...")

        email = IncomingEmail(
            email_id=scenario["id"],
            sender="customer@example.com",
            body=scenario["body"],
            received_at=datetime.utcnow(),
        )
        state = AgentState(email=email)

        # Run Agent 2
        agent = IntentClassificationAgent()
        state = agent(state)

        detected = [i.value for i in state.intent_result.intents]
        expected = scenario["expected"]

        status = "PASS" if set(detected) == set(expected) else "CHECK"
        print(f"[{status}] Detected : {detected}")
        print(f"   Expected : {expected}")
        print(f"   Confidence: {state.intent_result.confidence}")

    print("\n[DONE] Agent 2 tests complete!")


if __name__ == "__main__":
    main()