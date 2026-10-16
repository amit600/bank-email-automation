"""
Logging setup for the Bank Email Automation System.
Provides structured JSON logging for audit trail + human-readable app logs.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from config.config_loader import load_config


# ============================================================
# SETUP
# ============================================================

def _ensure_log_dir(log_dir: str) -> Path:
    """Create log directory if it doesn't exist."""
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _add_timestamp(_, __, event_dict: dict) -> dict:
    """Add ISO timestamp to every log entry."""
    from datetime import datetime
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def setup_logging() -> None:
    """
    Configure structlog + stdlib logging.
    Call once at application startup.
    """
    cfg = load_config()
    log_cfg = cfg.get("logging", {})
    log_dir = _ensure_log_dir(log_cfg.get("log_dir", "logs"))
    level_name = log_cfg.get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # ---------- stdlib logging (for third-party libs) ----------
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stdout,
    )

    # ---------- structlog config ----------
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            _add_timestamp,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Suppress noisy libs
    for noisy in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ============================================================
# LOGGER GETTER
# ============================================================

def get_logger(name: str = "bank_email_automation") -> BoundLogger:
    """Return a structlog logger with the given name."""
    return structlog.get_logger(name)


# ============================================================
# AUDIT LOGGER (separate file for compliance)
# ============================================================

class AuditLogger:
    """
    Writes audit entries to a dedicated audit.log file (JSON lines).
    Every agent decision gets logged here.
    """

    def __init__(self, audit_file: str | None = None):
        if audit_file is None:
            cfg = load_config()
            audit_file = cfg.get("logging", {}).get("audit_file", "logs/audit.log")
        self.path = Path(audit_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = get_logger("audit")

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
    ) -> None:
        """Log an agent decision to audit trail."""
        payload = {
            "email_id": email_id,
            "agent": agent_name,
            "action": action,
            "status": status,
            "input": input_summary,
            "output": output_summary,
            "error": error,
        }
        if extra:
            payload["extra"] = extra

        # Log to stdout (dev visibility)
        self._logger.info("audit_entry", **payload)

        # Append to audit.log file (JSON lines)
        import json
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    setup_logging()
    log = get_logger("test")
    log.info("logger_initialized", version="1.0.0")

    audit = AuditLogger()
    audit.log_decision(
        email_id="test-001",
        agent_name="IntentAgent",
        action="classify_intent",
        input_summary="Please provide balance",
        output_summary="balance_enquiry",
        status="OK",
    )

    log.info("test_completed", message="Logger is working!")

    # Read back audit file
    audit_path = Path("logs/audit.log")
    if audit_path.exists():
        print("\n[OK] audit.log content:")
        print(audit_path.read_text(encoding="utf-8"))

    print("[DONE] Logger test complete!")