"""
Test for Sentiment Analysis Agent.
Tests all 4 sentiments including negative/urgent tones.
"""
from datetime import datetime, timezone

from agents.sentiment_analysis_agent import SentimentAnalysisAgent
from models.schemas import AgentState, IncomingEmail
from utils.logger import setup_logging


SCENARIOS = [
    {
        "id": "sent-1",
        "body": "Please provide my savings account balance for account 1234567890.",
        "expected": "neutral",
    },
    {
        "id": "sent-2",
        "body": "Thank you so much for your excellent service! Could you kindly share my balance?",
        "expected": "positive",
    },
    {
        "id": "sent-3",
        "body": "This is the THIRD time I am asking! Where is my statement?? Very disappointed with your service!",
        "expected": "negative",
    },
    {
        "id": "sent-4",
        "body": "URGENT! I need my card transactions immediately! There has been a fraud on my card!",
        "expected": "urgent",
    },
]


def main():
    setup_logging()

    for scenario in SCENARIOS:
        print(f"\n{'='*60}")
        print(f"[{scenario['id']}] Expected: {scenario['expected']}")
        print(f"Email: {scenario['body'][:80]}...")

        email = IncomingEmail(
            email_id=scenario["id"],
            sender="customer@example.com",
            body=scenario["body"],
            received_at=datetime.now(timezone.utc),
        )
        state = AgentState(email=email)

        agent = SentimentAnalysisAgent()
        state = agent(state)

        detected = state.sentiment_result.sentiment.value
        status = "PASS" if detected == scenario["expected"] else "CHECK"
        print(f"[{status}] Detected : {detected}")
        print(f"   Confidence: {state.sentiment_result.confidence}")
        print(f"   Reasoning : {state.sentiment_result.reasoning}")

    print("\n[DONE] Agent 3 tests complete!")


if __name__ == "__main__":
    main()