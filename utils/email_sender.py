"""
Email sender utility.
Sends reply emails to customers after human approval.

Modes:
- MOCK (default): Logs the email, saves to logs/sent_emails.log — no real send
- REAL: Uses SMTP (config from config.yaml / env vars)
"""
from __future__ import annotations

import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from config.config_loader import load_config
from utils.logger import get_logger

log = get_logger("email_sender")


# ============================================================
# EMAIL SENDER
# ============================================================

class EmailSender:
    """Send reply emails via SMTP (or mock)."""

    def __init__(self, mock: bool = True):
        """
        Args:
            mock: If True, don't actually send — just log.
                  Set to False for real SMTP.
        """
        cfg = load_config()
        email_cfg = cfg.get("email", {})
        self.mock = mock
        self.smtp_host = email_cfg.get("smtp_host", "smtp.mockbank.com")
        self.smtp_port = email_cfg.get("smtp_port", 587)
        self.username = email_cfg.get("username", "support@mockbank.com")
        self.password = email_cfg.get("password", "mockpassword")
        self.sent_log = Path("logs/sent_emails.log")
        self.sent_log.parent.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------
    def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        email_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an email.

        Returns:
            {"ok": bool, "mode": "mock"|"smtp", "to": ..., "error": ...}
        """
        result: dict[str, Any] = {
            "ok": False,
            "mode": "mock" if self.mock else "smtp",
            "to": to_email,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat() + "Z",
            "email_id": email_id,
            "error": None,
        }

        # ----- Always log to file (audit trail) -----
        self._log_sent(to_email, subject, body, email_id)

        if self.mock:
            result["ok"] = True
            log.info(
                "email_mock_sent",
                to=to_email,
                subject=subject,
                email_id=email_id,
                body_length=len(body),
            )
            print(f"\n📧 [MOCK SEND] To: {to_email}")
            print(f"   Subject: {subject}")
            print(f"   Body preview: {body[:120]}...\n")
            return result

        # ----- Real SMTP -----
        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            result["ok"] = True
            log.info("email_sent_smtp", to=to_email, subject=subject)
        except Exception as e:
            result["error"] = str(e)
            log.error("email_send_failed", to=to_email, error=str(e))

        return result

    # --------------------------------------------------------
    # Internal: append to sent log
    # --------------------------------------------------------
    def _log_sent(
        self,
        to_email: str,
        subject: str,
        body: str,
        email_id: str | None,
    ) -> None:
        entry = {
            "sent_at": datetime.utcnow().isoformat() + "Z",
            "to": to_email,
            "subject": subject,
            "email_id": email_id,
            "body": body,
            "mode": "mock" if self.mock else "smtp",
        }
        with open(self.sent_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")


# ============================================================
# SINGLETON
# ============================================================

_sender: EmailSender | None = None


def get_sender(mock: bool = True) -> EmailSender:
    """Get a singleton email sender."""
    global _sender
    if _sender is None:
        _sender = EmailSender(mock=mock)
    return _sender


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging()

    print("[TEST] Email Sender (MOCK mode)")
    print("=" * 60)

    sender = get_sender(mock=True)

    result = sender.send(
        to_email="customer@example.com",
        subject="Re: Balance Enquiry",
        body=(
            "Dear Customer,\n\n"
            "Your account balance is INR 1,25,000.\n\n"
            "Thank you,\nCustomer Support Team"
        ),
        email_id="test-001",
    )

    print(f"[RESULT] {result}")

    # Show sent log
    path = Path("logs/sent_emails.log")
    if path.exists():
        print("\n[sent_emails.log] last entry:")
        last = path.read_text(encoding="utf-8").strip().split("\n")[-1]
        print(f"  {last[:200]}...")

    print("\n[DONE] Email Sender test complete!")