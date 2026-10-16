"""
Test for API Selection Agent.
"""
from datetime import datetime, timezone

from agents.intent_classification_agent import IntentClassificationAgent
from agents.entity_extraction_agent import EntityExtractionAgent
from agents.api_selection_agent import APISelectionAgent
from models.schemas import AgentState, IncomingEmail
from utils.logger import setup_logging


SCENARIOS = [
    {
        "id": "apisel-1",
        "body": "Please provide my savings account balance for account number 1234567890.",
        "expect_apis_contains": ["ValidateAccountAPI", "GetAccountBalanceAPI"],
    },
    {
        "id": "apisel-4",
        "body": "Please share my account balance for account 1234567890 and also send last 3 transactions of my credit card 9876543210987654.",
        "expect_apis_contains": [
            "ValidateAccountAPI", "GetAccountBalanceAPI",
            "ValidateCardAPI", "GetCardTransactionsAPI",
        ],
    },
]


def main():
    setup_logging()

    intent_agent = IntentClassificationAgent()
    entity_agent = EntityExtractionAgent()
    apisel_agent = APISelectionAgent()

    for scenario in SCENARIOS:
        print(f"\n{'='*60}")
        print(f"[{scenario['id']}]")
        print(f"Email: {scenario['body'][:80]}...")

        email = IncomingEmail(
            email_id=scenario["id"],
            sender="customer@example.com",
            body=scenario["body"],
            received_at=datetime.now(timezone.utc),
        )
        state = AgentState(email=email)

        state = intent_agent(state)
        state = entity_agent(state)
        state = apisel_agent(state)

        plan = state.api_plan
        print(f"  Required APIs : {plan['required_apis']}")
        print(f"  Parallel      : {plan['parallel_groups']}")

        detected = set(plan["required_apis"])
        expected = set(scenario["expect_apis_contains"])
        status = "PASS" if expected.issubset(detected) else "CHECK"
        print(f"  {status}")

    print("\n[DONE] API Selection Agent tests complete!")


if __name__ == "__main__":
    main()