"""
Test for Validation Agent.
Tests all 5 business scenarios including partial failure.
"""
from datetime import datetime, timezone

from agents.email_understanding_agent import EmailUnderstandingAgent
from agents.intent_classification_agent import IntentClassificationAgent
from agents.sentiment_analysis_agent import SentimentAnalysisAgent
from agents.entity_extraction_agent import EntityExtractionAgent
from agents.validation_agent import ValidationAgent
from models.schemas import AgentState, IncomingEmail
from utils.logger import setup_logging


SCENARIOS = [
    {
        "id": "val-1",
        "body": "Please provide my savings account balance for account number 1234567890.",
        "expect_account": "VALID",
        "expect_card": None,
    },
    {
        "id": "val-2",
        "body": "Please share my last 3 credit card transactions for card 4567890123456789.",
        "expect_account": None,
        "expect_card": "VALID",
    },
    {
        "id": "val-3",
        "body": "Kindly send my bank statement for April 2026 for account 1234567890.",
        "expect_account": "VALID",
        "expect_card": None,
    },
    {
        "id": "val-4",
        "body": "Please share my account balance for account 1234567890 and also send last 3 transactions of my credit card 9876543210987654.",
        "expect_account": "VALID",
        "expect_card": "VALID",
    },
    {
        "id": "val-5",
        "body": "Please provide balance for account 1234567890 and card transactions for card 9999999999999999.",
        "expect_account": "VALID",
        "expect_card": "INVALID",  # Partial failure
    },
]


def main():
    setup_logging()

    # Agents pipeline
    intent_agent = IntentClassificationAgent()
    entity_agent = EntityExtractionAgent()
    validation_agent = ValidationAgent()

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

        # Run pipeline: intent -> entity -> validation
        state = intent_agent(state)
        state = entity_agent(state)
        state = validation_agent(state)

        v = state.validation_result
        print(f"\n  Account Status : {v.account_status.value if v.account_status else 'N/A'}")
        print(f"  Card Status    : {v.card_status.value if v.card_status else 'N/A'}")
        print(f"  Card Error     : {v.card_error}")
        print(f"  API calls made : {len(state.api_responses)}")
        for api in state.api_responses:
            print(f"    {api.api_name}: {api.status.value}")

        # Verify
        ok = True
        if scenario["expect_account"] and v.account_status:
            if v.account_status.value != scenario["expect_account"]:
                ok = False
        if scenario["expect_card"] and v.card_status:
            if v.card_status.value != scenario["expect_card"]:
                ok = False
        print(f"  {'PASS' if ok else 'CHECK'}")

    print("\n[DONE] Agent 5 tests complete!")


if __name__ == "__main__":
    main()