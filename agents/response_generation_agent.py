"""
Response Generation Agent.
Generates professional customer response emails based on all processed data.
Handles partial success/failure gracefully.
"""
from __future__ import annotations

import json

from agents.base_agent import BaseAgent
from models.llm_loader import invoke_llm
from models.schemas import (
    AgentState,
    GeneratedResponse,
    ProcessingStatus,
    ValidationStatus,
)
from utils.prompt_loader import load_prompt


class ResponseGenerationAgent(BaseAgent):
    name = "ResponseGenerationAgent"
    description = "Generates professional customer response email"

    def run(self, state: AgentState) -> AgentState:
        if not state.email or not state.intent_result:
            raise ValueError("Missing email or intent result")

        # CHECK INPUT QUALITY - if insufficient, return polite error
        quality_issue = self._check_input_quality(state)
        if quality_issue:
            state.generated_response = GeneratedResponse(
                subject=f"Re: {state.email.subject or 'Your Banking Request'}",
                body=(
                    f"Dear Customer,\n\n"
                    f"{quality_issue}\n\n"
                    f"Thank you,\nCustomer Support Team"
                ),
                status=ProcessingStatus.FAILED,
                needs_human_approval=True,
                confidence=0.0,
            )
            self.log.info(
                "input_quality_failed",
                email_id=state.email.email_id,
                reason=quality_issue[:80],
            )
            return state

        # Build request summary
        request_summary = self._build_request_summary(state)

        # Build processed data (compact)
        processed_data = self._build_processed_data(state)

        # Build errors list
        errors = self._build_errors(state)

        # Sentiment
        sentiment = (
            state.sentiment_result.sentiment.value
            if state.sentiment_result else "neutral"
        )

        # Load prompt and format
        prompt_template = load_prompt("response_prompt")
        prompt = prompt_template.format(
            request_summary=request_summary,
            processed_data=processed_data,
            errors=errors,
            sentiment=sentiment,
        )

        body = invoke_llm(prompt)

        # Determine overall status
        status = self._determine_status(state)

        state.generated_response = GeneratedResponse(
            subject=f"Re: {state.email.subject or 'Your Banking Request'}",
            body=body,
            status=status,
            needs_human_approval=True,
            confidence=self._compute_confidence(state),
        )

        self.log.info(
            "response_generated",
            email_id=state.email.email_id,
            status=status.value,
            body_length=len(body),
        )
        return state

    # --------------------------------------------------------
    # Input quality check
    # --------------------------------------------------------
    def _check_input_quality(self, state: AgentState) -> str | None:
        """
        Check if the input is sufficient to process.
        Returns error message if insufficient, else None.
        """
        intents = (
            [i.value for i in state.intent_result.intents]
            if state.intent_result else []
        )
        entities = state.entities

        # Check 1: no intent detected
        if not intents or intents == ["unknown"]:
            return (
                "We could not understand your request. "
                "Please provide the appropriate prompt. "
                "For example: 'Please provide my savings account balance "
                "for account number 1234567890.'"
            )

        # Check 2: balance intent but no account number
        if "balance_enquiry" in intents and not (
            entities and entities.account_numbers
        ):
            return (
                "We could not find an account number in your message. "
                "Please provide the appropriate prompt with your account number. "
                "For example: 'Please provide my savings account balance "
                "for account number 1234567890.'"
            )

        # Check 3: card intent but no card number
        if "card_usage" in intents and not (
            entities and entities.card_numbers
        ):
            return (
                "We could not find a card number in your message. "
                "Please provide the appropriate prompt with your card number. "
                "For example: 'Please share my last 5 credit card transactions "
                "for card 4567890123456789.'"
            )

        # Check 4: statement intent but missing account or date
        if "statement_request" in intents:
            if not (entities and entities.account_numbers):
                return (
                    "We could not find an account number in your message. "
                    "Please provide the appropriate prompt with your account number. "
                    "For example: 'Please send my bank statement for April 2026 "
                    "for account 1234567890.'"
                )
            if not (entities and entities.date_range):
                return (
                    "We could not find a statement period in your message. "
                    "Please provide the appropriate prompt with the period. "
                    "For example: 'Please send my bank statement for April 2026 "
                    "for account 1234567890.'"
                )

        return None

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def _build_request_summary(self, state: AgentState) -> str:
        intents = [i.value for i in state.intent_result.intents]
        return f"Customer intents: {', '.join(intents)}"

    def _build_processed_data(self, state: AgentState) -> str:
        if not state.api_responses:
            return "No data retrieved."

        lines = []
        for api in state.api_responses:
            lines.append(f"\n[{api.api_name}] status={api.status.value}")
            if api.data:
                data_str = json.dumps(api.data, indent=2, default=str)
                lines.append(data_str)
            if api.error:
                lines.append(f"error: {api.error}")
        return "\n".join(lines)

    def _build_errors(self, state: AgentState) -> str:
        errors = []
        v = state.validation_result
        if v:
            if v.account_status == ValidationStatus.INVALID:
                errors.append(f"Account validation failed: {v.account_number}")
            if v.card_status == ValidationStatus.INVALID:
                errors.append(
                    f"Card validation failed: {v.card_error or v.card_number}"
                )
        for api in state.api_responses:
            if api.status == ValidationStatus.ERROR:
                errors.append(f"{api.api_name}: {api.error}")
        return "\n".join(errors) if errors else "None"

    def _determine_status(self, state: AgentState) -> ProcessingStatus:
        v = state.validation_result
        if not v:
            return ProcessingStatus.FAILED

        has_account = v.account_status is not None
        has_card = v.card_status is not None

        account_ok = v.account_status == ValidationStatus.VALID
        card_ok = v.card_status == ValidationStatus.VALID

        if (has_account and account_ok) or (has_card and card_ok):
            if (has_account and not account_ok) or (has_card and not card_ok):
                return ProcessingStatus.PARTIAL
            return ProcessingStatus.SUCCESS

        if has_account or has_card:
            return ProcessingStatus.FAILED
        return ProcessingStatus.FAILED

    def _compute_confidence(self, state: AgentState) -> float:
        scores = []
        if state.intent_result:
            scores.append(state.intent_result.confidence)
        if state.sentiment_result:
            scores.append(state.sentiment_result.confidence)
        return sum(scores) / len(scores) if scores else 0.0

    def _summarize_output(self, state: AgentState) -> str:
        if not state.generated_response:
            return "No response"
        return (
            f"Status: {state.generated_response.status.value}, "
            f"length: {len(state.generated_response.body)}"
        )