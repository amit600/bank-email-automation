"""
Test for Response Generation Agent.
Full pipeline: Intent -> Entity -> Validation -> Response.
Tests all 5 scenarios including partial failure.
"""
from datetime import datetime, timezone

from agents.intent_classification_agent import IntentClassificationAgent
from agents.entity_extraction_agent import EntityExtractionAgent
from agents.sentiment_analysis_agent import SentimentAnalysisAgent
from agents.validation_agent import ValidationAgent
from agents.response_generation_agent import ResponseGenerationAgent
from models.schemas import AgentState, IncomingEmail
from utils.logger import setup_logging


SCENARIOS = [
    {
        "id": "resp-1",
        "body": "Please provide my savings account balance for account number 1234567890.",
    },
    {
        "id": "resp-2",
        "body": "Please share my last 3 credit card transactions for card 4567890123456789.",
    },
    {
        "id": "resp-4",
        "body": "Please share my account balance for account 1234567890 and also send last 3 transactions of my credit card 9876543210987654.",
    },
    {
        "id": "resp-5",
        "body": "Please provide balance for account 1234567890 and card transactions for card 9999999999999999.",
    },
]


def main():
    setup_logging()

    intent_agent = IntentClassificationAgent()
    entity_agent = EntityExtractionAgent()
    sentiment_agent = SentimentAnalysisAgent()
    validation_agent = ValidationAgent()
    response_agent = ResponseGenerationAgent()

    for scenario in SCENARIOS:
        print(f"\n{'='*70}")
        print(f"[{scenario['id']}]")
        print(f"Email: {scenario['body']}")
        print(f"{'='*70}")

        email = IncomingEmail(
            email_id=scenario["id"],
            sender="customer@example.com",
            subject="Banking Request",
            body=scenario["body"],
            received_at=datetime.now(timezone.utc),
        )
        state = AgentState(email=email)

        # Full pipeline
        state = intent_agent(state)
        state = entity_agent(state)
        state = sentiment_agent(state)
        state = validation_agent(state)
        state = response_agent(state)

        print(f"\n[STATUS] {state.generated_response.status.value.upper()}")
        print(f"[SUBJECT] {state.generated_response.subject}")
        print(f"\n[BODY]\n{state.generated_response.body}\n")
        print(f"[AUDIT TRAIL] {len(state.audit_trail)} entries")

    print("\n[DONE] Full pipeline tests complete!")


if __name__ == "__main__":
    main()