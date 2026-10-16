"""
Sentiment Analysis Agent.
Detects customer sentiment (neutral/positive/negative/urgent).
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from models.llm_loader import invoke_llm_json
from models.schemas import AgentState, SentimentResult, SentimentType
from utils.prompt_loader import load_prompt


class SentimentAnalysisAgent(BaseAgent):
    name = "SentimentAnalysisAgent"
    description = "Detects customer sentiment"

    def run(self, state: AgentState) -> AgentState:
        if not state.email:
            raise ValueError("No email in state")

        prompt_template = load_prompt("sentiment_prompt")
        prompt = prompt_template.format(email_body=state.email.body)

        result = invoke_llm_json(prompt)
        self.log.info("sentiment_raw", result=result)

        sentiment_str = result.get("sentiment", "neutral")
        try:
            sentiment = SentimentType(sentiment_str)
        except ValueError:
            sentiment = SentimentType.NEUTRAL

        state.sentiment_result = SentimentResult(
            sentiment=sentiment,
            confidence=float(result.get("confidence", 0.0)),
            reasoning=result.get("reasoning"),
        )

        self.log.info(
            "sentiment_analyzed",
            email_id=state.email.email_id,
            sentiment=sentiment.value,
            confidence=state.sentiment_result.confidence,
        )
        return state

    def _summarize_output(self, state: AgentState) -> str:
        if not state.sentiment_result:
            return "No sentiment"
        return f"Sentiment: {state.sentiment_result.sentiment.value}"