"""
Mock Core Banking APIs (FastAPI).
Simulates the following APIs:
  1. ValidateAccountAPI
  2. ValidateCardAPI
  3. GetAccountBalanceAPI
  4. GetCardTransactionsAPI
  5. GetStatementAPI

Run:  python -m apis.main
Or :  uvicorn apis.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from apis import mock_data


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Mock Core Banking API",
    description="Simulated core banking APIs for the Email Automation System",
    version="1.0.0",
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class AccountRequest(BaseModel):
    account_number: str = Field(..., min_length=4, max_length=20)


class CardRequest(BaseModel):
    card_number: str = Field(..., min_length=4, max_length=20)


class CardTransactionsRequest(BaseModel):
    card_number: str
    limit: int = Field(default=5, ge=1, le=50)


class StatementRequest(BaseModel):
    account_number: str
    period: str = Field(..., description="e.g., 'April 2026' or '2026-04'")


class ValidateResponse(BaseModel):
    status: str                # VALID | INVALID
    customer_name: Optional[str] = None
    error: Optional[str] = None


class BalanceResponse(BaseModel):
    status: str
    account_number_masked: str
    customer_name: str
    balance: float
    currency: str


class Transaction(BaseModel):
    date: str
    amount: float
    merchant: str
    type: str


class TransactionsResponse(BaseModel):
    status: str
    card_number_masked: str
    count: int
    transactions: list[Transaction]


class StatementResponse(BaseModel):
    status: str
    account_number_masked: str
    period: str
    statement_url: str
    generated_at: str
    opening_balance: float
    closing_balance: float


# ============================================================
# UTIL: mask helper (avoid import cycles)
# ============================================================

def _mask(number: str, visible: int = 4) -> str:
    digits = "".join(c for c in number if c.isdigit())
    if len(digits) <= visible:
        return digits
    return "X" * (len(digits) - visible) + digits[-visible:]


# ============================================================
# API 1: Validate Account
# ============================================================

@app.post("/api/v1/validate/account", response_model=ValidateResponse)
def validate_account(req: AccountRequest):
    """Check if account number exists in core banking."""
    acc = mock_data.get_account(req.account_number)
    if acc:
        return ValidateResponse(status="VALID", customer_name=acc["customer_name"])
    return ValidateResponse(
        status="INVALID",
        error=f"Account number {_mask(req.account_number)} not found",
    )


# ============================================================
# API 2: Validate Card
# ============================================================

@app.post("/api/v1/validate/card", response_model=ValidateResponse)
def validate_card(req: CardRequest):
    """Check if card number exists + is ACTIVE."""
    card = mock_data.get_card(req.card_number)
    if not card:
        return ValidateResponse(
            status="INVALID",
            error=f"Card {_mask(req.card_number)} not found",
        )
    if card["status"] != "ACTIVE":
        return ValidateResponse(
            status="INVALID",
            error=f"Card {_mask(req.card_number)} is {card['status']}",
        )
    return ValidateResponse(status="VALID", customer_name=card["customer_name"])


# ============================================================
# API 3: Get Account Balance
# ============================================================

@app.post("/api/v1/account/balance", response_model=BalanceResponse)
def get_account_balance(req: AccountRequest):
    """Fetch balance for an account."""
    acc = mock_data.get_account(req.account_number)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    return BalanceResponse(
        status="OK",
        account_number_masked=_mask(acc["account_number"]),
        customer_name=acc["customer_name"],
        balance=acc["balance"],
        currency=acc["currency"],
    )


# ============================================================
# API 4: Get Card Transactions
# ============================================================

@app.post("/api/v1/card/transactions", response_model=TransactionsResponse)
def get_card_transactions(req: CardTransactionsRequest):
    """Fetch last N transactions for a card."""
    card = mock_data.get_card(req.card_number)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    txns = mock_data.get_card_transactions(req.card_number, limit=req.limit)
    return TransactionsResponse(
        status="OK",
        card_number_masked=_mask(req.card_number),
        count=len(txns),
        transactions=[Transaction(**t) for t in txns],
    )


# ============================================================
# API 5: Get Statement
# ============================================================

@app.post("/api/v1/statement", response_model=StatementResponse)
def get_statement(req: StatementRequest):
    """Fetch account statement for a period."""
    acc = mock_data.get_account(req.account_number)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    period = mock_data.normalize_period(req.period)
    if not period:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period format: {req.period}. Use 'April 2026' or '2026-04'",
        )

    stmt = mock_data.get_statement(req.account_number, period)
    if not stmt:
        raise HTTPException(
            status_code=404,
            detail=f"Statement not available for {period}",
        )

    return StatementResponse(
        status="OK",
        account_number_masked=_mask(req.account_number),
        period=period,
        statement_url=stmt["statement_url"],
        generated_at=stmt["generated_at"],
        opening_balance=stmt["opening_balance"],
        closing_balance=stmt["closing_balance"],
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "Mock Core Banking API",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("[START] Mock Banking API server")
    print("        Docs: http://localhost:8000/docs")
    uvicorn.run("apis.main:app", host="0.0.0.0", port=8000, reload=False)