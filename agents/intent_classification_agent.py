"""
Intent Classification Agent.
Identifies customer intent(s) from the email body.
Supports multiple intents in a single email.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from models.llm_loader import invoke_llm_json
from models.schemas import AgentState, IntentResult, IntentType
from utils.prompt_loader import load_prompt


class IntentClassificationAgent(BaseAgent):
    name = "IntentClassificationAgent"
    description = "Classifies customer intent(s) from email"

    def run(self, state: AgentState) -> AgentState:
        if not state.email:
            raise ValueError("No email in state")

        prompt_template = load_prompt("intent_prompt")
        prompt = prompt_template.format(email_body=state.email.body)

        result = invoke_llm_json(prompt)
        self.log.info("intent_raw", result=result)

        # Convert to typed IntentResult
        intent_strings = result.get("intents", ["unknown"])
        intents = []
        for i in intent_strings:
            try:
                intents.append(IntentType(i))
            except ValueError:
                intents.append(IntentType.UNKNOWN)

        state.intent_result = IntentResult(
            intents=intents,
            confidence=float(result.get("confidence", 0.0)),
            reasoning=result.get("reasoning"),
        )

        self.log.info(
            "intent_classified",
            email_id=state.email.email_id,
            intents=[i.value for i in intents],
            confidence=state.intent_result.confidence,
        )
        return state

    def _summarize_output(self, state: AgentState) -> str:
        if not state.intent_result:
            return "No intent"
        return f"Intents: {[i.value for i in state.intent_result.intents]}"