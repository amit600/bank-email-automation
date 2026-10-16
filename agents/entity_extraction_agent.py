"""
Entity Extraction Agent.
Extracts account numbers, card numbers, date ranges, and other entities
from the customer email body.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from models.llm_loader import invoke_llm_json
from models.schemas import AgentState, ExtractedEntities
from utils.prompt_loader import load_prompt


class EntityExtractionAgent(BaseAgent):
    name = "EntityExtractionAgent"
    description = "Extracts banking entities (account/card numbers, dates, counts)"

    def run(self, state: AgentState) -> AgentState:
        if not state.email:
            raise ValueError("No email in state")

        prompt_template = load_prompt("entity_prompt")
        prompt = prompt_template.format(email_body=state.email.body)

        result = invoke_llm_json(prompt)
        self.log.info("entities_raw", result=result)

        state.entities = ExtractedEntities(
            account_numbers=result.get("account_numbers", []) or [],
            card_numbers=result.get("card_numbers", []) or [],
            date_range=result.get("date_range"),
            transaction_count=result.get("transaction_count"),
            customer_name=result.get("customer_name"),
        )

        self.log.info(
            "entities_extracted",
            email_id=state.email.email_id,
            accounts=state.entities.account_numbers,
            cards=state.entities.card_numbers,
            date_range=state.entities.date_range,
            txn_count=state.entities.transaction_count,
        )
        return state

    def _summarize_output(self, state: AgentState) -> str:
        if not state.entities:
            return "No entities"
        e = state.entities
        return (
            f"Accounts: {e.account_numbers}, "
            f"Cards: {len(e.card_numbers)} found, "
            f"Period: {e.date_range}, "
            f"TxnCount: {e.transaction_count}"
        )