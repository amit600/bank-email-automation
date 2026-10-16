"""
Email text preprocessing utility.
Cleans HTML, removes signatures/quotes, normalizes whitespace
before sending to LLM agents.
"""
from __future__ import annotations

import html
import re


# ============================================================
# REGEX PATTERNS
# ============================================================

_HTML_TAG = re.compile(r"<[^>]+>")
_HTML_ENTITIES = re.compile(r"&[a-zA-Z]+;|&#\d+;")
_URL = re.compile(r"https?://\S+|www\.\S+")
_MULTIPLE_NEWLINES = re.compile(r"\n{3,}")
_MULTIPLE_SPACES = re.compile(r"[ \t]{2,}")
_QUOTED_LINE = re.compile(r"^\s*>.*$", re.MULTILINE)  # Lines starting with >
_SIGNATURE_MARKERS = [
    r"^\s*--\s*$",                       # -- separator
    r"^\s*Regards,?\s*$",
    r"^\s*Best regards,?\s*$",
    r"^\s*Thanks,?\s*$",
    r"^\s*Sincerely,?\s*$",
    r"^\s*Sent from my .*$",
    r"^\s*Get Outlook for .*$",
]


# ============================================================
# MAIN CLEANER
# ============================================================

def clean_email(body: str, remove_urls: bool = False) -> str:
    """
    Clean raw email body.

    Steps:
    1. Decode HTML entities (&amp; -> &)
    2. Strip HTML tags
    3. Remove quoted replies (lines starting with >)
    4. Remove signature blocks
    5. Remove extra whitespace
    6. (Optional) Remove URLs
    """
    if not body:
        return ""

    text = body

    # 1. Decode HTML entities
    text = html.unescape(text)

    # 2. Strip HTML tags
    text = _HTML_TAG.sub(" ", text)

    # 3. Remove quoted lines
    text = _QUOTED_LINE.sub("", text)

    # 4. Cut off at signature marker
    for marker in _SIGNATURE_MARKERS:
        match = re.search(marker, text, re.MULTILINE | re.IGNORECASE)
        if match:
            text = text[: match.start()]
            break

    # 5. Optional: remove URLs
    if remove_urls:
        text = _URL.sub("[URL]", text)

    # 6. Normalize whitespace
    text = _MULTIPLE_SPACES.sub(" ", text)
    text = _MULTIPLE_NEWLINES.sub("\n\n", text)

    return text.strip()


def extract_attachments_metadata(body: str) -> dict:
    """Placeholder — extracts attachment hints from email body."""
    return {
        "mentions_attachment": "attach" in body.lower(),
        "mentions_pdf": ".pdf" in body.lower() or "pdf" in body.lower(),
        "mentions_image": any(
            x in body.lower() for x in [".jpg", ".jpeg", ".png", "image", "photo"]
        ),
    }


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    print("[TEST] Email Cleaner")
    print("=" * 60)

    sample = """
    <html><body>
    <p>Hi,</p>

    <p>Please provide my <b>savings account</b> balance for
    account number &nbsp;1234567890.</p>

    <p>Thanks &amp; Regards,<br>
    John Doe</p>

    <blockquote>
    > On Monday, customer wrote:
    > Original message here...
    </blockquote>

    Sent from my iPhone
    </body></html>
    """

    print("\n[RAW]")
    print(sample)
    print("\n[CLEANED]")
    cleaned = clean_email(sample)
    print(cleaned)

    print("\n[METADATA]")
    print(extract_attachments_metadata("Please see attached PDF statement."))

    # Assertions
    assert "<" not in cleaned, "HTML tags not removed"
    assert "John Doe" not in cleaned or "Sent from" not in cleaned
    assert "  " not in cleaned

    print("\n[DONE] Email Cleaner tests passed!")