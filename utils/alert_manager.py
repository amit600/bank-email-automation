"""
Alert Manager utility.
Raises alerts on failures in any pipeline stage.

Channels:
1. Console (loud print)
2. logs/alerts.log (dedicated file)
3. (Optional) Webhook / Email - stubbed for production
"""
from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path

from utils.logger import get_logger

log = get_logger("alert_manager")


# ============================================================
# ALERT SEVERITY
# ============================================================

class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# ============================================================
# ALERT MANAGER
# ============================================================

class AlertManager:
    """Centralized alert manager for pipeline failures."""

    def __init__(self, alert_file: str = "logs/alerts.log"):
        self.path = Path(alert_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def raise_alert(
        self,
        message: str,
        severity: AlertSeverity = AlertSeverity.WARNING,
        email_id: str | None = None,
        agent_name: str | None = None,
        error: str | None = None,
        extra: dict | None = None,
    ) -> dict:
        """Record an alert via all configured channels."""
        alert = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": severity.value,
            "message": message,
            "email_id": email_id,
            "agent_name": agent_name,
            "error": error,
            "extra": extra or {},
        }

        # 1. Console (loud)
        label = {
            AlertSeverity.INFO: "INFO",
            AlertSeverity.WARNING: "WARNING",
            AlertSeverity.CRITICAL: "CRITICAL",
        }.get(severity, "WARNING")
        print(f"\n[{label}] ALERT - {message}")
        if email_id:
            print(f"     Email : {email_id}")
        if agent_name:
            print(f"     Agent : {agent_name}")
        if error:
            print(f"     Error : {error}")
        print()

        # 2. File
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert, default=str) + "\n")

        # 3. Structured log
        log.warning("alert_raised", **alert)

        # 4. Webhook (production - stubbed)
        self._send_webhook(alert)

        return alert

    def _send_webhook(self, alert: dict) -> None:
        """
        Send alert to external service (Slack/Teams/PagerDuty).
        Stub for production - uncomment and add webhook URL.
        """
        # import requests
        # webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        # if webhook_url:
        #     requests.post(webhook_url, json=alert, timeout=5)
        pass

    # --------------------------------------------------------
    # Convenience methods
    # --------------------------------------------------------
    def pipeline_failed(self, email_id: str, stage: str, error: str) -> dict:
        return self.raise_alert(
            message=f"Pipeline failed at stage: {stage}",
            severity=AlertSeverity.CRITICAL,
            email_id=email_id,
            agent_name=stage,
            error=error,
        )

    def api_failed(self, email_id: str, api_name: str, error: str) -> dict:
        return self.raise_alert(
            message=f"API call failed: {api_name}",
            severity=AlertSeverity.WARNING,
            email_id=email_id,
            agent_name=api_name,
            error=error,
        )

    def validation_failed(self, email_id: str, detail: str) -> dict:
        return self.raise_alert(
            message=f"Validation failed: {detail}",
            severity=AlertSeverity.WARNING,
            email_id=email_id,
            agent_name="ValidationAgent",
            error=detail,
        )


# ============================================================
# SINGLETON
# ============================================================

_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging()

    print("[TEST] Alert Manager")
    print("=" * 60)

    mgr = get_alert_manager()

    # Test 1: Pipeline failure
    mgr.pipeline_failed(
        email_id="test-001",
        stage="ValidationAgent",
        error="API timeout after 10s",
    )

    # Test 2: API failure
    mgr.api_failed(
        email_id="test-002",
        api_name="GetAccountBalanceAPI",
        error="Connection refused",
    )

    # Test 3: Validation failure
    mgr.validation_failed(
        email_id="test-003",
        detail="Card 9999999999999999 not found",
    )

    print("[DONE] Alert Manager tests complete!")

    # Show file
    path = Path("logs/alerts.log")
    if path.exists():
        print(f"\n[alerts.log] last entries:")
        for line in path.read_text(encoding="utf-8").splitlines()[-3:]:
            print(f"  {line}")