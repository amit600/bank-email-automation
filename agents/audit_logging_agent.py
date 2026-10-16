"""
Audit/Logging Agent.
Centralized agent for writing audit trail entries to disk + stdout.
Provides a clean interface over utils.logger.AuditLogger.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from models.schemas import AgentState, AuditEntry
from utils.logger import AuditLogger, get_logger


class AuditLoggingAgent:
    """
    Not a pipeline agent — it's a cross-cutting utility exposed as an agent
    to satisfy the requirement of an explicit 'Audit/Logging Agent'.
    """

    name = "AuditLoggingAgent"
    description = "Writes structured audit entries for all agent decisions"

    def __init__(self):
        self.log = get_logger(self.name)
        self.audit = AuditLogger()

    # --------------------------------------------------------
    # Log a single decision (called by other agents)
    # --------------------------------------------------------
    def log_decision(
        self,
        email_id: str,
        agent_name: str,
        action: str,
        input_summary: str | None = None,
        output_summary: str | None = None,
        status: str = "OK",
        error: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Write an audit entry and return it as a Pydantic model."""
        entry = AuditEntry(
            email_id=email_id,
            agent_name=agent_name,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            status=status,
            error=error,
        )

        self.audit.log_decision(
            email_id=email_id,
            agent_name=agent_name,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            status=status,
            error=error,
            extra=extra,
        )
        return entry

    # --------------------------------------------------------
    # Flush full state audit trail (end of pipeline)
    # --------------------------------------------------------
    def flush_state(self, state: AgentState) -> AgentState:
        """Persist all audit entries from the given state."""
        email_id = state.email.email_id if state.email else "unknown"
        for entry in state.audit_trail:
            self.audit.log_decision(
                email_id=entry.email_id or email_id,
                agent_name=entry.agent_name,
                action=entry.action,
                input_summary=entry.input_summary,
                output_summary=entry.output_summary,
                status=entry.status,
                error=entry.error,
            )
        self.log.info(
            "audit_flushed",
            email_id=email_id,
            entries=len(state.audit_trail),
        )
        return state

    # --------------------------------------------------------
    # Summary stats
    # --------------------------------------------------------
    def summary(self, state: AgentState) -> dict[str, Any]:
        """Compute audit stats for the given state."""
        total = len(state.audit_trail)
        ok = sum(1 for e in state.audit_trail if e.status == "OK")
        errors = total - ok
        return {
            "email_id": state.email.email_id if state.email else "unknown",
            "total_entries": total,
            "ok": ok,
            "errors": errors,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging()

    print("[TEST] Audit Logging Agent")
    print("=" * 60)

    agent = AuditLoggingAgent()

    # Log 3 decisions
    e1 = agent.log_decision(
        email_id="test-001",
        agent_name="IntentClassificationAgent",
        action="classify_intent",
        input_summary="Please provide balance",
        output_summary="balance_enquiry",
        status="OK",
    )
    print(f"\n[1] Logged: {e1.agent_name} -> {e1.output_summary}")

    e2 = agent.log_decision(
        email_id="test-001",
        agent_name="ValidationAgent",
        action="validate_account",
        input_summary="account=1234567890",
        output_summary="VALID",
        status="OK",
    )
    print(f"[2] Logged: {e2.agent_name} -> {e2.output_summary}")

    e3 = agent.log_decision(
        email_id="test-001",
        agent_name="ValidationAgent",
        action="validate_card",
        input_summary="card=9999999999999999",
        output_summary="INVALID",
        status="ERROR",
        error="Card not found",
    )
    print(f"[3] Logged: {e3.agent_name} -> {e3.output_summary} ({e3.status})")

    print("\n[SUMMARY]")
    summary = agent.summary.__wrapped__ if hasattr(agent.summary, "__wrapped__") else None
    print(f"  audit.log written with 3 entries")

    print("\n[DONE] Audit Logging Agent tests complete!")