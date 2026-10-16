"""
Base Agent class for all AI agents.
Provides common functionality: logging, audit trail, name, timing.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from models.schemas import AgentState, AuditEntry
from utils.logger import AuditLogger, get_logger


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Subclasses must implement `run(state) -> state`.
    """

    name: str = "BaseAgent"
    description: str = ""

    def __init__(self):
        self.log = get_logger(self.__class__.__name__)
        self.audit = AuditLogger()

    # --------------------------------------------------------
    # Abstract method — subclasses must implement
    # --------------------------------------------------------
    @abstractmethod
    def run(self, state: AgentState) -> AgentState:
        """
        Execute the agent's logic on the given state.
        Return the updated state.
        """
        raise NotImplementedError

    # --------------------------------------------------------
    # Template method — handles timing, logging, audit
    # --------------------------------------------------------
    def __call__(self, state: AgentState) -> AgentState:
        """Entry point — wraps run() with timing + audit."""
        start = time.time()
        email_id = state.email.email_id if state.email else "unknown"
        self.log.info("agent_start", agent=self.name, email_id=email_id)

        try:
            state = self.run(state)
            latency_ms = round((time.time() - start) * 1000, 2)

            # Audit log
            entry = AuditEntry(
                email_id=email_id,
                agent_name=self.name,
                action="run",
                output_summary=self._summarize_output(state),
                status="OK",
            )
            state.audit_trail.append(entry)

            self.audit.log_decision(
                email_id=email_id,
                agent_name=self.name,
                action="run",
                output_summary=self._summarize_output(state),
                status="OK",
                extra={"latency_ms": latency_ms},
            )
            self.log.info("agent_end", agent=self.name, latency_ms=latency_ms)
            return state

        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 2)
            self.log.error("agent_error", agent=self.name, error=str(e))
            self.audit.log_decision(
                email_id=email_id,
                agent_name=self.name,
                action="run",
                status="ERROR",
                error=str(e),
                extra={"latency_ms": latency_ms},
            )
            state.error = f"{self.name} failed: {e}"
            raise

    # --------------------------------------------------------
    # Helper to summarize state for audit (override-able)
    # --------------------------------------------------------
    def _summarize_output(self, state: AgentState) -> str:
        return f"{self.name} completed"