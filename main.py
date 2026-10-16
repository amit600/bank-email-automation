"""
Main entry point for the Bank Email Automation System.
Runs a scheduler that processes emails every N minutes.
"""
from __future__ import annotations

import signal
import sys
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler

from config.config_loader import load_config
from models.schemas import IncomingEmail
from utils.logger import get_logger, setup_logging
from workflows.orchestrator import process_email


log = get_logger("main")
_scheduler: BlockingScheduler | None = None


# ============================================================
# EMAIL FETCHER (Mocked)
# ============================================================

MOCK_INBOX = [
    "Please provide my savings account balance for account number 1234567890.",
    "Please share my last 5 credit card transactions for card 4567890123456789.",
    "Kindly send my bank statement for April 2026 for account 1234567890.",
    "Please share my account balance for account 1234567890 and also send last 3 transactions of my credit card 9876543210987654.",
    "Please provide balance for account 1234567890 and card transactions for card 9999999999999999.",
]

_mock_index = 0


def fetch_new_emails(max_count: int = 3) -> list[IncomingEmail]:
    """
    Mock email fetcher — cycles through sample emails.
    In production: replace with IMAP fetch.
    """
    global _mock_index
    emails = []
    for _ in range(min(max_count, len(MOCK_INBOX))):
        body = MOCK_INBOX[_mock_index % len(MOCK_INBOX)]
        _mock_index += 1
        emails.append(
            IncomingEmail(
                email_id=f"auto-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_mock_index}",
                sender="customer@example.com",
                subject="Auto-fetched Email",
                body=body,
                received_at=datetime.now(timezone.utc),
            )
        )
    return emails


# ============================================================
# SCHEDULED JOB
# ============================================================

def scheduled_job() -> None:
    """Runs every N minutes — fetches and processes emails."""
    log.info("scheduled_job_start", time=datetime.now(timezone.utc).isoformat())

    try:
        emails = fetch_new_emails(max_count=3)
        log.info("emails_fetched", count=len(emails))

        for email in emails:
            try:
                final_state = process_email(email)
                status = (
                    final_state.generated_response.status.value
                    if final_state.generated_response else "NO_RESPONSE"
                )
                log.info(
                    "email_processed",
                    email_id=email.email_id,
                    status=status,
                    audit_entries=len(final_state.audit_trail),
                )
                # In production: push to human approval queue here
                print(f"\n[PROCESSED] {email.email_id}: {status}")
                if final_state.generated_response:
                    print(f"[RESPONSE]\n{final_state.generated_response.body[:200]}...\n")
            except Exception as e:
                log.error("email_processing_failed", email_id=email.email_id, error=str(e))

    except Exception as e:
        log.error("scheduled_job_failed", error=str(e))


# ============================================================
# GRACEFUL SHUTDOWN
# ============================================================

def _shutdown(signum, frame) -> None:  # noqa: ARG001
    log.info("shutdown_signal_received", signal=signum)
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    sys.exit(0)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    global _scheduler
    setup_logging()

    cfg = load_config()
    interval = cfg.get("app", {}).get("schedule_interval_minutes", 10)

    log.info("scheduler_starting", interval_minutes=interval)
    print(f"\n{'='*70}")
    print(f"  BANK EMAIL AUTOMATION — SCHEDULER")
    print(f"  Runs every {interval} minutes. Press Ctrl+C to stop.")
    print(f"{'='*70}\n")

    # Run once immediately for demo
    print("[DEMO] Running first job immediately...\n")
    scheduled_job()

    # Then schedule
    _scheduler = BlockingScheduler()
    _scheduler.add_job(
        scheduled_job,
        "interval",
        minutes=interval,
        id="email_processor",
        next_run_time=datetime.now(timezone.utc),
    )

    # Graceful shutdown
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        _scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        _shutdown(0, None)


if __name__ == "__main__":
    main()