"""
Test for Email Understanding Agent.
"""
from datetime import datetime

from agents.email_understanding_agent import EmailUnderstandingAgent
from models.schemas import AgentState, IncomingEmail
from utils.logger import setup_logging


def main():
    setup_logging()

    # Create a sample email
    email = IncomingEmail(
        email_id="test-001",
        sender="customer@example.com",
        subject="Balance Enquiry",
        body="Please provide my savings account balance for account number 1234567890.",
        received_at=datetime.utcnow(),
    )

    state = AgentState(email=email)
    print(f"\n[INPUT] {email.body}\n")

    # Run agent
    agent = EmailUnderstandingAgent()
    state = agent(state)

    print(f"[OUTPUT] Summary: {state.summary}")
    print(f"[AUDIT] Entries: {len(state.audit_trail)}")
    print("\n[DONE] Agent 1 test complete!")


if __name__ == "__main__":
    main()