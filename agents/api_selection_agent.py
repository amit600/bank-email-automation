"""
API Selection Agent.
Determines which core banking APIs need to be called based on intents + entities.
Outputs an ordered execution plan (with parallel hints).

Note: In this implementation, Validation Agent consumes this plan.
Separating it as its own agent follows Single Responsibility Principle.
"""
from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent
from models.schemas import AgentState


# Map intent -> required API(s)
INTENT_TO_APIS: dict[str, list[str]] = {
    "balance_enquiry": ["ValidateAccountAPI", "GetAccountBalanceAPI"],
    "card_usage": ["ValidateCardAPI", "GetCardTransactionsAPI"],
    "statement_request": ["ValidateAccountAPI", "GetStatementAPI"],
}

# APIs that can run in parallel (independent of each other)
PARALLEL_GROUPS: list[list[str]] = [
    ["ValidateAccountAPI", "ValidateCardAPI"],
]


class APISelectionAgent(BaseAgent):
    name = "APISelectionAgent"
    description = "Determines which APIs to call based on intents"

    def run(self, state: AgentState) -> AgentState:
        if not state.intent_result:
            raise ValueError("No intent result in state")

        intents = [i.value for i in state.intent_result.intents]
        entities = state.entities

        # Build execution plan
        plan = self._build_plan(intents, entities)
        state.api_plan = plan

        self.log.info(
            "api_plan_built",
            intents=intents,
            plan=plan,
        )
        return state

    def _build_plan(self, intents: list[str], entities) -> dict[str, Any]:
        """
        Returns:
        {
          "required_apis": ["ValidateAccountAPI", ...],
          "parallel_groups": [["ValidateAccountAPI", "ValidateCardAPI"]],
          "execution_order": ["ValidateAccountAPI", "GetAccountBalanceAPI"],
        }
        """
        required: list[str] = []
        for intent in intents:
            for api in INTENT_TO_APIS.get(intent, []):
                if api not in required:
                    required.append(api)

        # If no account entity, don't call account APIs
        has_account = bool(entities and entities.account_numbers)
        has_card = bool(entities and entities.card_numbers)

        filtered: list[str] = []
        for api in required:
            if "Account" in api and not has_account:
                continue
            if "Card" in api and not has_card:
                continue
            filtered.append(api)

        # Parallel groups (only include APIs in our list)
        parallel = [
            [a for a in group if a in filtered]
            for group in PARALLEL_GROUPS
        ]
        parallel = [g for g in parallel if len(g) > 1]

        return {
            "required_apis": filtered,
            "parallel_groups": parallel,
            "execution_order": filtered,
        }

    def _summarize_output(self, state: AgentState) -> str:
        plan = getattr(state, "api_plan", None) or {}
        return f"APIs: {plan.get('required_apis', [])}"