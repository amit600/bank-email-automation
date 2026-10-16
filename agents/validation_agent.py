"""
Validation Agent.
Validates extracted entities (account/card) and fetches required data via APIs.
Handles partial validation failures gracefully.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from models.schemas import (
    AgentState,
    APIResponse,
    IntentType,
    ValidationResult,
    ValidationStatus,
)
from utils.api_client import get_client


class ValidationAgent(BaseAgent):
    name = "ValidationAgent"
    description = "Validates account/card numbers and fetches required data"

    def run(self, state: AgentState) -> AgentState:
        if not state.entities or not state.intent_result:
            raise ValueError("Missing entities or intent")

        client = get_client()
        intents = [i.value for i in state.intent_result.intents]
        entities = state.entities

        validation = ValidationResult()
        api_responses: list[APIResponse] = []

        # =====================================================
        # ACCOUNT FLOW
        # =====================================================
        if entities.account_numbers:
            account_number = entities.account_numbers[0]
            validation.account_number = account_number

            # Step 1: Validate account
            v_resp = client.validate_account(account_number)
            account_valid = (
                v_resp["status"] == "OK"
                and v_resp["data"].get("status") == "VALID"
            )
            validation.account_status = (
                ValidationStatus.VALID if account_valid else ValidationStatus.INVALID
            )

            if account_valid:
                validation.customer_name = v_resp["data"].get("customer_name")

                # Step 2: If balance intent → fetch balance
                if "balance_enquiry" in intents:
                    b_resp = client.get_account_balance(account_number)
                    api_responses.append(
                        APIResponse(
                            api_name="GetAccountBalanceAPI",
                            status=(
                                ValidationStatus.VALID
                                if b_resp["status"] == "OK"
                                else ValidationStatus.ERROR
                            ),
                            data=b_resp.get("data"),
                            error=b_resp.get("error"),
                            latency_ms=b_resp.get("latency_ms"),
                        )
                    )

                # Step 3: If statement intent → fetch statement
                if "statement_request" in intents:
                    period = entities.date_range or ""
                    s_resp = client.get_statement(account_number, period)
                    api_responses.append(
                        APIResponse(
                            api_name="GetStatementAPI",
                            status=(
                                ValidationStatus.VALID
                                if s_resp["status"] == "OK"
                                else ValidationStatus.ERROR
                            ),
                            data=s_resp.get("data"),
                            error=s_resp.get("error"),
                            latency_ms=s_resp.get("latency_ms"),
                        )
                    )
            else:
                validation.account_status = ValidationStatus.INVALID

        # =====================================================
        # CARD FLOW
        # =====================================================
        if entities.card_numbers:
            card_number = entities.card_numbers[0]
            validation.card_number = card_number

            v_resp = client.validate_card(card_number)
            card_valid = (
                v_resp["status"] == "OK"
                and v_resp["data"].get("status") == "VALID"
            )
            validation.card_status = (
                ValidationStatus.VALID if card_valid else ValidationStatus.INVALID
            )

            if card_valid:
                # Fetch card transactions
                limit = entities.transaction_count or 5
                t_resp = client.get_card_transactions(card_number, limit=limit)
                api_responses.append(
                    APIResponse(
                        api_name="GetCardTransactionsAPI",
                        status=(
                            ValidationStatus.VALID
                            if t_resp["status"] == "OK"
                            else ValidationStatus.ERROR
                        ),
                        data=t_resp.get("data"),
                        error=t_resp.get("error"),
                        latency_ms=t_resp.get("latency_ms"),
                    )
                )
            else:
                # Save error for partial failure scenario
                if v_resp.get("data"):
                    validation.card_error = v_resp["data"].get("error")

        state.validation_result = validation
        state.api_responses = api_responses

        self.log.info(
            "validation_complete",
            email_id=state.email.email_id if state.email else "unknown",
            account_status=validation.account_status.value if validation.account_status else None,
            card_status=validation.card_status.value if validation.card_status else None,
            api_calls=len(api_responses),
        )
        return state

    def _summarize_output(self, state: AgentState) -> str:
        v = state.validation_result
        if not v:
            return "No validation"
        return (
            f"Account: {v.account_status.value if v.account_status else 'N/A'}, "
            f"Card: {v.card_status.value if v.card_status else 'N/A'}, "
            f"API calls: {len(state.api_responses)}"
        )