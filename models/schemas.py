"""
Pydantic schemas for the Bank Email Automation System.
Defines strict typed models for emails, intents, entities, and API responses.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================
# ENUMS (Fixed values — typo se bachaata hai)
# ============================================================

class IntentType(str, Enum):
    """Possible customer intents."""
    BALANCE_ENQUIRY = "balance_enquiry"
    CARD_USAGE = "card_usage"
    STATEMENT_REQUEST = "statement_request"
    MULTIPLE = "multiple"
    UNKNOWN = "unknown"


class SentimentType(str, Enum):
    """Customer sentiment categories."""
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    URGENT = "urgent"


class ValidationStatus(str, Enum):
    """Validation result status."""
    VALID = "VALID"
    INVALID = "INVALID"
    ERROR = "ERROR"


class ProcessingStatus(str, Enum):
    """Overall email processing status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING_APPROVAL = "pending_approval"


# ============================================================
# EMAIL MODELS
# ============================================================

class EmailAttachment(BaseModel):
    """Represents an email attachment (PDF/image)."""
    filename: str
    content_type: str
    size_bytes: int = 0
    file_path: Optional[str] = None
    extracted_text: Optional[str] = None

    @field_validator("size_bytes")
    @classmethod
    def check_size(cls, v: int) -> int:
        if v < 0:
            raise ValueError("size_bytes cannot be negative")
        return v


class IncomingEmail(BaseModel):
    """Represents an incoming customer email."""
    email_id: str
    sender: str
    subject: str = ""
    body: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    attachments: list[EmailAttachment] = Field(default_factory=list)


# ============================================================
# INTENT & SENTIMENT MODELS
# ============================================================

class IntentResult(BaseModel):
    """Result of intent classification."""
    intents: list[IntentType]
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reasoning: Optional[str] = None

    @field_validator("intents")
    @classmethod
    def at_least_one(cls, v: list[IntentType]) -> list[IntentType]:
        if not v:
            return [IntentType.UNKNOWN]
        return v


class SentimentResult(BaseModel):
    """Result of sentiment analysis."""
    sentiment: SentimentType
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reasoning: Optional[str] = None


# ============================================================
# ENTITY MODELS
# ============================================================

class ExtractedEntities(BaseModel):
    """Banking entities extracted from email + attachments."""
    account_numbers: list[str] = Field(default_factory=list)
    card_numbers: list[str] = Field(default_factory=list)
    date_range: Optional[str] = None
    transaction_count: Optional[int] = None
    customer_name: Optional[str] = None

    @field_validator("account_numbers", "card_numbers")
    @classmethod
    def clean_numbers(cls, v: list[str]) -> list[str]:
        """Strip spaces and dashes from numbers."""
        return [n.replace(" ", "").replace("-", "") for n in v if n]


# ============================================================
# API MODELS
# ============================================================

class APIRequest(BaseModel):
    """Generic API request wrapper."""
    api_name: str
    payload: dict[str, Any]


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    api_name: str
    status: ValidationStatus
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None


class ValidationResult(BaseModel):
    """Validation agent result for account/card."""
    account_number: Optional[str] = None
    account_status: Optional[ValidationStatus] = None
    customer_name: Optional[str] = None
    card_number: Optional[str] = None
    card_status: Optional[ValidationStatus] = None
    card_error: Optional[str] = None


# ============================================================
# RESPONSE GENERATION
# ============================================================

class GeneratedResponse(BaseModel):
    """Final generated email response."""
    subject: str
    body: str
    status: ProcessingStatus
    needs_human_approval: bool = True
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


# ============================================================
# AUDIT / LOGGING
# ============================================================

class AuditEntry(BaseModel):
    """Single audit log entry for a decision."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    email_id: str
    agent_name: str
    action: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    status: str = "OK"
    error: Optional[str] = None


# ============================================================
# MAIN PIPELINE STATE (LangGraph ke liye)
# ============================================================

class AgentState(BaseModel):
    """
    Shared state flowing through the LangGraph orchestrator.
    Har agent isko update karega.
    """
    # Input
    email: Optional[IncomingEmail] = None

    # Agent outputs
    summary: Optional[str] = None
    intent_result: Optional[IntentResult] = None
    sentiment_result: Optional[SentimentResult] = None
    entities: Optional[ExtractedEntities] = None
    validation_result: Optional[ValidationResult] = None
    api_plan: Optional[dict[str, Any]] = None
    api_responses: list[APIResponse] = Field(default_factory=list)
    generated_response: Optional[GeneratedResponse] = None

    # Audit
    audit_trail: list[AuditEntry] = Field(default_factory=list)
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


# ============================================================
# QUICK SELF-TEST
# ============================================================

if __name__ == "__main__":
    # Test: create an incoming email
    email = IncomingEmail(
        email_id="test-001",
        sender="customer@example.com",
        subject="Balance Enquiry",
        body="Please provide my savings account balance for account number 1234567890.",
    )
    print("[OK] Email model created:")
    print(f"     ID      : {email.email_id}")
    print(f"     Sender  : {email.sender}")
    print(f"     Body    : {email.body[:50]}...")

    # Test: intent
    intent = IntentResult(
        intents=[IntentType.BALANCE_ENQUIRY],
        confidence=0.95,
        reasoning="Customer asked for account balance",
    )
    print(f"\n[OK] Intent model created: {intent.intents}")

    # Test: entities
    entities = ExtractedEntities(
        account_numbers=["1234-567-890"],
        transaction_count=5,
    )
    print(f"\n[OK] Entities model created: {entities.account_numbers}")

    # Test: agent state
    state = AgentState(email=email, intent_result=intent, entities=entities)
    print(f"\n[OK] AgentState created. Keys: {list(state.model_dump().keys())}")

    print("\n[DONE] All schemas validated successfully!")