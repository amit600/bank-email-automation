"""
Email Understanding Agent.
Summarizes the incoming customer email in one short sentence.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from models.llm_loader import invoke_llm
from models.schemas import AgentState
from utils.prompt_loader import load_prompt
from utils.email_cleaner import clean_email


class EmailUnderstandingAgent(BaseAgent):
    name = "EmailUnderstandingAgent"
    description = "Summarizes customer email"

    def run(self, state: AgentState) -> AgentState:
        if not state.email:
            raise ValueError("No email in state")

        prompt_template = load_prompt("summary_prompt")
        # prompt = prompt_template.format(email_body=state.email.body)
        
        cleaned_body = clean_email(state.email.body)
        prompt = prompt_template.format(email_body=cleaned_body)

        summary = invoke_llm(prompt)
        state.summary = summary

        self.log.info(
            "email_summarized",
            email_id=state.email.email_id,
            summary=summary[:80],
        )
        return state

    def _summarize_output(self, state: AgentState) -> str:
        return f"Summary: {state.summary[:60]}..." if state.summary else "No summary"