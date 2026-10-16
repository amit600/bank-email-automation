"""
Test for Entity Extraction Agent.
Tests all 5 business scenarios including multiple entities.
"""
from datetime import datetime, timezone

from agents.entity_extraction_agent import EntityExtractionAgent
from models.schemas import AgentState, IncomingEmail
from utils.logger import setup_logging


SCENARIOS = [
    {
        "id": "ent-1",
        "body": "Please provide my savings account balance for account number 1234567890.",
        "expected": {"accounts": ["1234567890"], "cards": []},
    },
    {
        "id": "ent-2",
        "body": "Please share my last 5 credit card transactions for card 4567890123456789.",
        "expected": {"accounts": [], "cards": ["4567890123456789"], "count": 5},
    },
    {
        "id": "ent-3",
        "body": "Kindly send my bank statement for April 2026 for account 1234567890.",
        "expected": {"accounts": ["1234567890"], "date_range": "April 2026"},
    },
    {
        "id": "ent-4",
        "body": "Please share my account balance for account 1234567890 and also send last 3 transactions of my credit card 9876543210987654.",
        "expected": {
            "accounts": ["1234567890"],
            "cards": ["9876543210987654"],
            "count": 3,
        },
    },
    {
        "id": "ent-5",
        "body": "Please provide balance for account 1234567890 and card transactions for card 9999999999999999.",
        "expected": {"accounts": ["1234567890"], "cards": ["9999999999999999"]},
    },
]


def main():
    setup_logging()

    for scenario in SCENARIOS:
        print(f"\n{'='*60}")
        print(f"[{scenario['id']}]")
        print(f"Email: {scenario['body'][:90]}...")

        email = IncomingEmail(
            email_id=scenario["id"],
            sender="customer@example.com",
            body=scenario["body"],
            received_at=datetime.now(timezone.utc),
        )
        state = AgentState(email=email)

        agent = EntityExtractionAgent()
        state = agent(state)

        e = state.entities
        print(f"  Accounts   : {e.account_numbers}")
        print(f"  Cards      : {e.card_numbers}")
        print(f"  Date Range : {e.date_range}")
        print(f"  Txn Count  : {e.transaction_count}")

        # Verify
        ok = True
        if "accounts" in scenario["expected"]:
            if set(e.account_numbers) != set(scenario["expected"]["accounts"]):
                ok = False
        if "cards" in scenario["expected"]:
            if set(e.card_numbers) != set(scenario["expected"]["cards"]):
                ok = False
        if "count" in scenario["expected"]:
            if e.transaction_count != scenario["expected"]["count"]:
                ok = False
        if "date_range" in scenario["expected"]:
            if e.date_range != scenario["expected"]["date_range"]:
                ok = False

        print(f"  {'PASS' if ok else 'CHECK'}")

    print("\n[DONE] Agent 4 tests complete!")


if __name__ == "__main__":
    main()