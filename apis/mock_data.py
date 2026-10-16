"""
Mock banking data for the simulated core banking system.
Contains sample accounts, cards, transactions, and statements.
"""
from __future__ import annotations

from datetime import datetime


# ============================================================
# SAMPLE ACCOUNTS
# ============================================================

ACCOUNTS: dict[str, dict] = {
    "1234567890": {
        "account_number": "1234567890",
        "customer_name": "John Doe",
        "account_type": "SAVINGS",
        "balance": 125000.00,
        "currency": "INR",
        "status": "ACTIVE",
        "branch": "Mumbai Main",
    },
    "9876543210": {
        "account_number": "9876543210",
        "customer_name": "Jane Smith",
        "account_type": "SAVINGS",
        "balance": 54200.50,
        "currency": "INR",
        "status": "ACTIVE",
        "branch": "Delhi CP",
    },
    "1111222233": {
        "account_number": "1111222233",
        "customer_name": "Bob Wilson",
        "account_type": "CURRENT",
        "balance": 300000.00,
        "currency": "INR",
        "status": "ACTIVE",
        "branch": "Bangalore HSR",
    },
}


# ============================================================
# SAMPLE CARDS
# ============================================================

CARDS: dict[str, dict] = {
    "4567890123456789": {
        "card_number": "4567890123456789",
        "customer_name": "John Doe",
        "card_type": "CREDIT",
        "status": "ACTIVE",
        "limit": 200000.00,
        "available_limit": 150000.00,
        "expiry": "12/2028",
    },
    "9876543210987654": {
        "card_number": "9876543210987654",
        "customer_name": "Jane Smith",
        "card_type": "CREDIT",
        "status": "ACTIVE",
        "limit": 100000.00,
        "available_limit": 80000.00,
        "expiry": "06/2027",
    },
    "5555666677778888": {
        "card_number": "5555666677778888",
        "customer_name": "Bob Wilson",
        "card_type": "CREDIT",
        "status": "BLOCKED",
        "limit": 50000.00,
        "available_limit": 0.0,
        "expiry": "03/2026",
    },
}


# ============================================================
# SAMPLE CARD TRANSACTIONS
# ============================================================

CARD_TRANSACTIONS: dict[str, list[dict]] = {
    "4567890123456789": [
        {"date": "2026-04-01", "amount": 2500.00, "merchant": "Amazon", "type": "DEBIT"},
        {"date": "2026-04-03", "amount": 800.00, "merchant": "Swiggy", "type": "DEBIT"},
        {"date": "2026-04-05", "amount": 12000.00, "merchant": "Flipkart", "type": "DEBIT"},
        {"date": "2026-04-07", "amount": 500.00, "merchant": "Starbucks", "type": "DEBIT"},
        {"date": "2026-04-10", "amount": 1500.00, "merchant": "Uber", "type": "DEBIT"},
        {"date": "2026-04-12", "amount": 30000.00, "merchant": "Croma", "type": "DEBIT"},
        {"date": "2026-04-15", "amount": 450.00, "merchant": "Zomato", "type": "DEBIT"},
    ],
    "9876543210987654": [
        {"date": "2026-04-02", "amount": 3000.00, "merchant": "Myntra", "type": "DEBIT"},
        {"date": "2026-04-06", "amount": 15000.00, "merchant": "Apple Store", "type": "DEBIT"},
        {"date": "2026-04-09", "amount": 250.00, "merchant": "Chai Point", "type": "DEBIT"},
        {"date": "2026-04-11", "amount": 5000.00, "merchant": "Decathlon", "type": "DEBIT"},
    ],
    "5555666677778888": [],
}


# ============================================================
# SAMPLE STATEMENTS
# ============================================================

STATEMENTS: dict[str, dict] = {
    "1234567890_2026-04": {
        "account_number": "1234567890",
        "period": "2026-04",
        "statement_url": "https://mockbank.com/statements/1234567890_2026-04.pdf",
        "generated_at": "2026-05-01T00:00:00Z",
        "opening_balance": 100000.00,
        "closing_balance": 125000.00,
    },
    "1234567890_2026-03": {
        "account_number": "1234567890",
        "period": "2026-03",
        "statement_url": "https://mockbank.com/statements/1234567890_2026-03.pdf",
        "generated_at": "2026-04-01T00:00:00Z",
        "opening_balance": 85000.00,
        "closing_balance": 100000.00,
    },
    "9876543210_2026-04": {
        "account_number": "9876543210",
        "period": "2026-04",
        "statement_url": "https://mockbank.com/statements/9876543210_2026-04.pdf",
        "generated_at": "2026-05-01T00:00:00Z",
        "opening_balance": 50000.00,
        "closing_balance": 54200.50,
    },
}


# ============================================================
# HELPERS
# ============================================================

def get_account(account_number: str) -> dict | None:
    """Lookup account by number."""
    return ACCOUNTS.get(account_number)


def get_card(card_number: str) -> dict | None:
    """Lookup card by number."""
    return CARDS.get(card_number)


def get_card_transactions(card_number: str, limit: int = 5) -> list[dict]:
    """Get last N transactions for a card."""
    txns = CARD_TRANSACTIONS.get(card_number, [])
    return txns[:limit]


def get_statement(account_number: str, period: str) -> dict | None:
    """
    Get statement for account + period (YYYY-MM).

    Example: get_statement("1234567890", "2026-04")
    """
    key = f"{account_number}_{period}"
    return STATEMENTS.get(key)


def normalize_period(period_str: str) -> str | None:
    """
    Convert 'April 2026' -> '2026-04'.
    Supports: 'April 2026', 'Apr 2026', '2026-04', '04/2026'
    """
    if not period_str:
        return None
    period_str = period_str.strip()

    # Already in YYYY-MM format
    if len(period_str) == 7 and period_str[4] == "-":
        return period_str

    months = {
        "january": "01", "jan": "01",
        "february": "02", "feb": "02",
        "march": "03", "mar": "03",
        "april": "04", "apr": "04",
        "may": "05",
        "june": "06", "jun": "06",
        "july": "07", "jul": "07",
        "august": "08", "aug": "08",
        "september": "09", "sep": "09", "sept": "09",
        "october": "10", "oct": "10",
        "november": "11", "nov": "11",
        "december": "12", "dec": "12",
    }

    parts = period_str.lower().replace(",", "").split()
    month_num = None
    year = None

    for p in parts:
        if p in months:
            month_num = months[p]
        elif p.isdigit() and len(p) == 4:
            year = p

    if month_num and year:
        return f"{year}-{month_num}"

    # Try MM/YYYY
    if "/" in period_str:
        try:
            m, y = period_str.split("/")
            return f"{y}-{m.zfill(2)}"
        except ValueError:
            return None

    return None


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    print("[TEST] Mock Data\n")

    print(f"Accounts loaded : {len(ACCOUNTS)}")
    print(f"Cards loaded    : {len(CARDS)}")
    print(f"Statements      : {len(STATEMENTS)}")

    print("\nAccount lookup:")
    print(f"  1234567890 -> {get_account('1234567890')['customer_name']}")
    print(f"  9999999999 -> {get_account('9999999999')}")

    print("\nCard lookup:")
    print(f"  4567890123456789 -> {get_card('4567890123456789')['card_type']}")
    print(f"  9999999999999999 -> {get_card('9999999999999999')}")

    print("\nTransactions (last 3):")
    for t in get_card_transactions("4567890123456789", limit=3):
        print(f"  {t['date']}  {t['merchant']:<12}  INR {t['amount']:>10.2f}")

    print("\nPeriod normalization:")
    for p in ["April 2026", "Apr 2026", "2026-04", "04/2026", "invalid"]:
        print(f"  '{p}' -> {normalize_period(p)}")

    print("\nStatement lookup:")
    stmt = get_statement("1234567890", "2026-04")
    print(f"  1234567890 Apr 2026 -> {stmt['statement_url'] if stmt else None}")

    print("\n[DONE] Mock data ready!")