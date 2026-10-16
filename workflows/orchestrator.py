"""
LangGraph orchestrator for the email processing pipeline.
Connects all agents into a stateful workflow.
"""
from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from agents.email_understanding_agent import EmailUnderstandingAgent
from agents.intent_classification_agent import IntentClassificationAgent
from agents.sentiment_analysis_agent import SentimentAnalysisAgent
from agents.entity_extraction_agent import EntityExtractionAgent
from agents.validation_agent import ValidationAgent
from agents.response_generation_agent import ResponseGenerationAgent
from models.schemas import AgentState, IncomingEmail
from utils.logger import get_logger, setup_logging
from utils.alert_manager import get_alert_manager
from utils.mcp_server import get_mcp_server

log = get_logger("orchestrator")


# ============================================================
# AGENT SINGLETONS (reuse)
# ============================================================

_understanding = EmailUnderstandingAgent()
_intent = IntentClassificationAgent()
_sentiment = SentimentAnalysisAgent()
_entity = EntityExtractionAgent()
_validation = ValidationAgent()
_response = ResponseGenerationAgent()


# ============================================================
# NODE FUNCTIONS
# ============================================================

def _node_understanding(state: AgentState) -> AgentState:
    """Node 1: Email Understanding."""
    return _understanding(state)


def _node_intent(state: AgentState) -> AgentState:
    """Node 2: Intent Classification."""
    return _intent(state)


def _node_sentiment(state: AgentState) -> AgentState:
    """Node 3: Sentiment Analysis."""
    return _sentiment(state)


def _node_entity(state: AgentState) -> AgentState:
    """Node 4: Entity Extraction."""
    return _entity(state)


def _node_validation(state: AgentState) -> AgentState:
    """Node 5: Validation + API calls."""
    return _validation(state)


def _node_response(state: AgentState) -> AgentState:
    """Node 6: Response Generation."""
    return _response(state)


# ============================================================
# CONDITIONAL EDGE: should we stop on error?
# ============================================================

def _should_continue(state: AgentState) -> str:
    """If any agent set state.error, stop the pipeline."""
    if state.error:
        log.warning("orchestrator_error_short_circuit", error=state.error)
        return "end"
    return "continue"


# ============================================================
# BUILD GRAPH
# ============================================================

def build_workflow() -> Any:
    """Build and compile the LangGraph workflow."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("understanding", _node_understanding)
    graph.add_node("intent", _node_intent)
    graph.add_node("sentiment", _node_sentiment)
    graph.add_node("entity", _node_entity)
    graph.add_node("validation", _node_validation)
    graph.add_node("response", _node_response)

    # Set entry point
    graph.set_entry_point("understanding")

    # Edges
    graph.add_edge("understanding", "intent")
    graph.add_edge("intent", "sentiment")
    graph.add_edge("sentiment", "entity")
    graph.add_edge("entity", "validation")
    graph.add_edge("validation", "response")
    graph.add_edge("response", END)

    return graph.compile()


# ============================================================
# PUBLIC API
# ============================================================

_compiled_graph = None


def get_pipeline():
    """Lazy-init the compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_workflow()
    return _compiled_graph



def process_email(email: IncomingEmail) -> AgentState:
    pipeline = get_pipeline()
    initial_state = AgentState(email=email)
    alerts = get_alert_manager()
    mcp = get_mcp_server() 

    log.info(
        "pipeline_start", 
         email_id=email.email_id,
         mcp_tools=len(mcp.discover()),
        
        )

    try:
        result_dict = pipeline.invoke(initial_state.model_dump())
        final_state = AgentState(**result_dict)

        # Alert on partial failure
        if final_state.validation_result:
            v = final_state.validation_result
            if v.card_status and v.card_status.value == "INVALID":
                alerts.validation_failed(
                    email_id=email.email_id,
                    detail=f"Card invalid: {v.card_error or v.card_number}",
                )

        log.info(
            "pipeline_end",
            email_id=email.email_id,
            status=(
                final_state.generated_response.status.value
                if final_state.generated_response else "NO_RESPONSE"
            ),
            audit_entries=len(final_state.audit_trail),
        )
        return final_state

    except Exception as e:
        alerts.pipeline_failed(
            email_id=email.email_id,
            stage="orchestrator",
            error=str(e),
        )
        raise


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    from datetime import datetime, timezone

    setup_logging()

    email = IncomingEmail(
        email_id="orch-test-001",
        sender="customer@example.com",
        subject="Balance Enquiry",
        body="Please provide my savings account balance for account number 1234567890.",
        received_at=datetime.now(timezone.utc),
    )

    print("\n" + "=" * 70)
    print("PIPELINE TEST")
    print("=" * 70)
    print(f"\n[INPUT EMAIL]\n{email.body}\n")

    final_state = process_email(email)

    print(f"\n[SUMMARY] {final_state.summary}")
    print(f"[INTENT] {[i.value for i in final_state.intent_result.intents]}")
    print(f"[SENTIMENT] {final_state.sentiment_result.sentiment.value}")
    print(f"[ENTITIES] Accounts={final_state.entities.account_numbers}")
    print(f"[VALIDATION] Account={final_state.validation_result.account_status.value}")
    print(f"[API CALLS] {len(final_state.api_responses)}")
    print(f"[STATUS] {final_state.generated_response.status.value.upper()}")
    print(f"\n[FINAL RESPONSE]\n{final_state.generated_response.body}")
    print(f"\n[AUDIT ENTRIES] {len(final_state.audit_trail)}")
    print("\n[DONE] Orchestrator test complete!")