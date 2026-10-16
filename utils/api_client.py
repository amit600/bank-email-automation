"""
API client for Mock Core Banking APIs.
Handles all HTTP calls with timeout, retry, and logging.
"""
from __future__ import annotations

import time
from typing import Any

import requests

from config.config_loader import load_config
from utils.logger import get_logger

log = get_logger("api_client")


# ============================================================
# API CLIENT
# ============================================================

class CoreBankingClient:
    """
    HTTP client for the Mock Core Banking APIs.
    All methods return a dict with 'status' and 'data' keys.
    """

    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        cfg = load_config()
        api_cfg = cfg.get("apis", {})
        self.base_url = base_url or api_cfg.get("base_url", "http://localhost:8000")
        self.timeout = timeout or api_cfg.get("timeout_seconds", 10)
        self.endpoints = api_cfg.get("endpoints", {})

    # --------------------------------------------------------
    # Internal POST helper with retry
    # --------------------------------------------------------
    def _post(self, endpoint: str, payload: dict, retries: int = 1) -> dict[str, Any]:
        """POST with timeout + single retry."""
        url = f"{self.base_url}{endpoint}"
        last_error: str | None = None

        for attempt in range(retries + 1):
            start = time.time()
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"},
                )
                latency_ms = round((time.time() - start) * 1000, 2)

                if resp.status_code == 200:
                    return {
                        "status": "OK",
                        "data": resp.json(),
                        "latency_ms": latency_ms,
                    }
                else:
                    return {
                        "status": "ERROR",
                        "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                        "latency_ms": latency_ms,
                    }
            except requests.Timeout:
                last_error = f"Timeout after {self.timeout}s"
            except requests.ConnectionError:
                last_error = f"Cannot connect to {url} — is the API server running?"
            except Exception as e:
                last_error = f"Unexpected error: {e}"

            log.warning(
                "api_call_retry",
                url=url,
                attempt=attempt + 1,
                error=last_error,
            )

        return {"status": "ERROR", "error": last_error}

    # --------------------------------------------------------
    # API 1: Validate Account
    # --------------------------------------------------------
    def validate_account(self, account_number: str) -> dict:
        endpoint = self.endpoints.get("validate_account", "/api/v1/validate/account")
        result = self._post(endpoint, {"account_number": account_number})
        log.info("api_validate_account", account=account_number[-4:], status=result["status"])
        return result

    # --------------------------------------------------------
    # API 2: Validate Card
    # --------------------------------------------------------
    def validate_card(self, card_number: str) -> dict:
        endpoint = self.endpoints.get("validate_card", "/api/v1/validate/card")
        result = self._post(endpoint, {"card_number": card_number})
        log.info("api_validate_card", card=card_number[-4:], status=result["status"])
        return result

    # --------------------------------------------------------
    # API 3: Get Account Balance
    # --------------------------------------------------------
    def get_account_balance(self, account_number: str) -> dict:
        endpoint = self.endpoints.get("account_balance", "/api/v1/account/balance")
        result = self._post(endpoint, {"account_number": account_number})
        log.info("api_get_balance", account=account_number[-4:], status=result["status"])
        return result

    # --------------------------------------------------------
    # API 4: Get Card Transactions
    # --------------------------------------------------------
    def get_card_transactions(self, card_number: str, limit: int = 5) -> dict:
        endpoint = self.endpoints.get("card_transactions", "/api/v1/card/transactions")
        result = self._post(
            endpoint,
            {"card_number": card_number, "limit": limit},
        )
        log.info(
            "api_get_transactions",
            card=card_number[-4:],
            limit=limit,
            status=result["status"],
        )
        return result

    # --------------------------------------------------------
    # API 5: Get Statement
    # --------------------------------------------------------
    def get_statement(self, account_number: str, period: str) -> dict:
        endpoint = self.endpoints.get("statement", "/api/v1/statement")
        result = self._post(
            endpoint,
            {"account_number": account_number, "period": period},
        )
        log.info(
            "api_get_statement",
            account=account_number[-4:],
            period=period,
            status=result["status"],
        )
        return result

    # --------------------------------------------------------
    # Health check
    # --------------------------------------------------------
    def health(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False


# ============================================================
# SINGLETON
# ============================================================

_client: CoreBankingClient | None = None


def get_client() -> CoreBankingClient:
    """Get a singleton API client."""
    global _client
    if _client is None:
        _client = CoreBankingClient()
    return _client


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging()

    print("[TEST] Core Banking API Client")
    print("=" * 50)

    client = get_client()

    # Health
    print(f"\n[1] Health check: {client.health()}")

    # Validate account
    print("\n[2] Validate account (valid):")
    result = client.validate_account("1234567890")
    print(f"    {result}")

    # Validate account (invalid)
    print("\n[3] Validate account (invalid):")
    result = client.validate_account("0000000000")
    print(f"    {result}")

    # Get balance
    print("\n[4] Get balance:")
    result = client.get_account_balance("1234567890")
    print(f"    {result}")

    # Get card transactions
    print("\n[5] Card transactions (limit=3):")
    result = client.get_card_transactions("4567890123456789", limit=3)
    print(f"    {result}")

    # Statement
    print("\n[6] Statement (April 2026):")
    result = client.get_statement("1234567890", "April 2026")
    print(f"    {result}")

    print("\n[DONE] API Client tests complete!")