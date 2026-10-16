"""
Human-in-the-Loop approval dashboard for bank email responses.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.schemas import IncomingEmail, EmailAttachment
from workflows.orchestrator import process_email
from utils.logger import setup_logging, get_logger
from utils.email_sender import get_sender
from utils.attachment_handler import AttachmentHandler


# ============================================================
# Bootstrap
# ============================================================

setup_logging()
log = get_logger("ui")


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="Bank Email Approval",
    page_icon="",
    layout="wide",
)


# ============================================================
# Session state
# ============================================================

if "pending" not in st.session_state:
    st.session_state.pending = []

if "approved" not in st.session_state:
    st.session_state.approved = []

if "email_body_value" not in st.session_state:
    st.session_state.email_body_value = ""

# Counter to force file_uploader reset
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


# ============================================================
# Sample emails (quick-fill only - no dropdown)
# ============================================================

SAMPLE_EMAILS = {
    "Scenario 1 - Balance": "Please provide my savings account balance for account number 1234567890.",
    "Scenario 2 - Card Txns": "Please share my last 5 credit card transactions for card 4567890123456789.",
    "Scenario 3 - Statement": "Kindly send my bank statement for April 2026 for account 1234567890.",
    "Scenario 4 - Multiple": "Please share my account balance for account 1234567890 and also send last 3 transactions of my credit card 9876543210987654.",
    "Scenario 5 - Partial Fail": "Please provide balance for account 1234567890 and card transactions for card 9999999999999999.",
}


# ============================================================
# Sidebar - Email input
# ============================================================

st.sidebar.title("Incoming Email")

st.sidebar.markdown(
    "**Paste a customer email below** - the AI will automatically "
    "detect intent, sentiment, and entities. No manual selection needed."
)

# Optional quick-fill buttons
st.sidebar.markdown("**Quick fill (optional demo samples):**")
cols = st.sidebar.columns(2)
for i, (label, body) in enumerate(SAMPLE_EMAILS.items()):
    if cols[i % 2].button(label, key=f"fill-{i}"):
        st.session_state.email_body_value = body
        st.rerun()

# Email body input
email_body = st.sidebar.text_area(
    "Customer Email Body",
    value=st.session_state.email_body_value,
    height=180,
    placeholder="Paste customer email here...",
)

# Sender input
sender_email = st.sidebar.text_input(
    "Sender (optional)",
    value="customer@example.com",
)

# Attachment uploader (with dynamic key to allow reset)
st.sidebar.markdown("**Attachments (optional):**")
uploaded_files = st.sidebar.file_uploader(
    "Upload PDF or image (max 5 MB)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key=f"attachment_uploader_{st.session_state.uploader_key}",
)

# Clear attachments button
if uploaded_files:
    if st.sidebar.button("Clear Attachments"):
        st.session_state.uploader_key += 1
        st.rerun()

# Process button
if st.sidebar.button("Process Email", type="primary"):
    if not email_body.strip() and not uploaded_files:
        st.sidebar.error("Please enter an email body or upload an attachment.")
    else:
        with st.spinner("AI agents processing... (30-90s on CPU)"):
            # -------- Process attachments --------
            handler = AttachmentHandler()
            attachments = []
            attachment_text = ""

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    content = uploaded_file.read()
                    result = handler.process(
                        filename=uploaded_file.name,
                        content=content,
                        content_type=uploaded_file.type or "",
                    )

                    if result["safe"]:
                        attachment = EmailAttachment(
                            filename=result["filename"],
                            content_type=result["content_type"],
                            size_bytes=result["size_bytes"],
                            file_path=result["path"],
                        )

                        # Extract text from PDF/image
                        if result["path"]:
                            try:
                                extracted = handler.extract_text(result["path"])
                                attachment.extracted_text = extracted
                                if extracted:
                                    attachment_text += (
                                        f"\n\n[Attachment: {result['filename']}]\n"
                                        f"{extracted}"
                                    )
                            except Exception as e:
                                log.warning(
                                    "attachment_extract_failed",
                                    filename=result["filename"],
                                    error=str(e),
                                )

                        attachments.append(attachment)
                    else:
                        st.sidebar.warning(
                            f"Attachment rejected: {result['filename']} "
                            f"({result['error']})"
                        )

            # -------- Merge email body + attachment text --------
            if not email_body.strip() and attachment_text:
                full_body = (
                    "Please process the attached document.\n"
                    + attachment_text
                )
            elif attachment_text:
                full_body = email_body + attachment_text
            else:
                full_body = email_body

            email = IncomingEmail(
                email_id=f"ui-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                sender=sender_email,
                subject="Customer Email",
                body=full_body,
                received_at=datetime.now(timezone.utc),
                attachments=attachments,
            )
            state = process_email(email)
            # Replace pending - only keep the latest processed email
            st.session_state.pending = [state]

        st.sidebar.success("Processed! Check main panel.")

        # -------- Auto-clear email body AND attachments --------
        st.session_state.email_body_value = ""
        st.session_state.uploader_key += 1
        st.rerun()


# ============================================================
# Main panel
# ============================================================

st.title("Human-in-the-Loop Approval Dashboard")
st.caption(
    "AI automatically detects intent + sentiment + entities from the email. "
    "Review the generated response before sending."
)

# -------- Clear All Pending button (top of main panel) --------
if st.session_state.pending:
    col_top1, col_top2 = st.columns([4, 1])
    with col_top2:
        if st.button("Clear All Pending", key="clear_all_pending"):
            st.session_state.pending = []
            st.rerun()


tab1, tab2 = st.tabs(["Pending Approval", "Approved & Sent"])


# ============================================================
# Tab 1: Pending
# ============================================================

with tab1:
    if not st.session_state.pending:
        st.info(
            "No pending emails. Paste a customer email in the sidebar "
            "and click **Process Email**."
        )
    else:
        for idx, state in enumerate(st.session_state.pending):
            email_id = state.email.email_id if state.email else "unknown"
            with st.expander(
                f"{email_id} - {state.email.subject}",
                expanded=True,
            ):
                col1, col2 = st.columns(2)

                # ---------------- LEFT: Original + AI analysis ----------------
                with col1:
                    st.markdown("### Original Email")
                    st.write(f"**From:** {state.email.sender}")
                    st.write(f"**Subject:** {state.email.subject}")
                    st.text_area(
                        "Body",
                        state.email.body,
                        height=120,
                        disabled=True,
                        key=f"orig-{idx}",
                    )

                    # Show attachments
                    if state.email.attachments:
                        st.markdown("**Attachments:**")
                        for att in state.email.attachments:
                            size_kb = round(att.size_bytes / 1024, 1)
                            st.write(f"- {att.filename} ({size_kb} KB)")

                    st.markdown("### AI Auto-Detection")
                    st.write(f"**Summary:** {state.summary}")

                    if state.intent_result:
                        st.write(
                            f"**Intents:** "
                            f"{[i.value for i in state.intent_result.intents]}"
                        )
                        st.write(
                            f"**Confidence:** {state.intent_result.confidence}"
                        )
                        if state.intent_result.reasoning:
                            st.caption(f"Reasoning: {state.intent_result.reasoning}")

                    if state.sentiment_result:
                        st.write(
                            f"**Sentiment:** "
                            f"{state.sentiment_result.sentiment.value} "
                            f"({state.sentiment_result.confidence})"
                        )
                        if state.sentiment_result.reasoning:
                            st.caption(f"Reasoning: {state.sentiment_result.reasoning}")

                    if state.entities:
                        st.write("**Entities extracted:**")
                        st.json(
                            {
                                "accounts": state.entities.account_numbers,
                                "cards": state.entities.card_numbers,
                                "date_range": state.entities.date_range,
                                "transaction_count": state.entities.transaction_count,
                            }
                        )

                # ---------------- RIGHT: Response + Actions ----------------
                with col2:
                    st.markdown("### AI-Generated Response")
                    if state.generated_response:
                        edited = st.text_area(
                            "Edit before sending",
                            value=state.generated_response.body,
                            height=320,
                            key=f"resp-{idx}",
                        )
                        status = state.generated_response.status.value.upper()
                        st.write(f"**Status:** {status}")
                        st.write(
                            f"**Confidence:** {state.generated_response.confidence}"
                        )

                        col_a, col_b, col_c = st.columns(3)

                        # -------- APPROVE & SEND --------
                        with col_a:
                            if st.button(
                                "Approve & Send",
                                key=f"app-{idx}",
                                type="primary",
                            ):
                                state.generated_response.body = edited

                                # Send the email (mock mode)
                                sender = get_sender(mock=True)
                                send_result = sender.send(
                                    to_email=state.email.sender,
                                    subject=state.generated_response.subject,
                                    body=edited,
                                    email_id=state.email.email_id,
                                )

                                log.info(
                                    "email_approved_and_sent",
                                    email_id=state.email.email_id,
                                    ok=send_result["ok"],
                                    mode=send_result["mode"],
                                )

                                if send_result["ok"]:
                                    st.success(
                                        f"Email sent to {state.email.sender} "
                                        f"({send_result['mode']} mode)"
                                    )
                                else:
                                    st.error(
                                        f"Send failed: {send_result['error']}"
                                    )

                                st.session_state.approved.append(state)
                                st.session_state.pending.pop(idx)
                                st.rerun()

                        # -------- REJECT --------
                        with col_b:
                            if st.button("Reject", key=f"rej-{idx}"):
                                log.info(
                                    "email_rejected",
                                    email_id=state.email.email_id,
                                )
                                st.session_state.pending.pop(idx)
                                st.rerun()

                        # -------- DISMISS (remove from list) --------
                        with col_c:
                            if st.button("Dismiss", key=f"dis-{idx}"):
                                log.info(
                                    "email_dismissed",
                                    email_id=state.email.email_id,
                                )
                                st.session_state.pending.pop(idx)
                                st.rerun()

                # ---------------- Audit Trail ----------------
                st.markdown("### Audit Trail")
                st.json(
                    [entry.model_dump(mode="json") for entry in state.audit_trail]
                )


# ============================================================
# Tab 2: Approved & Sent
# ============================================================

with tab2:
    if not st.session_state.approved:
        st.info("No approved emails yet.")
    else:
        st.caption(
            f"Total: {len(st.session_state.approved)} email(s) approved & sent. "
            "Logged in `logs/sent_emails.log`."
        )
        for state in st.session_state.approved:
            st.success(
                f"{state.email.email_id} - {state.email.subject} "
                f"(sent to {state.email.sender})"
            )
            with st.expander("View sent email", expanded=False):
                st.write(f"**Subject:** {state.generated_response.subject}")
                st.text_area(
                    "Sent body",
                    state.generated_response.body,
                    height=220,
                    disabled=True,
                    key=f"sent-{state.email.email_id}",
                )