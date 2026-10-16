"""
PDF text extraction utility.
Uses pdfplumber to read text from PDF files.
"""
from __future__ import annotations

from pathlib import Path

from utils.logger import get_logger

log = get_logger("pdf_reader")


def extract_pdf_text(path: str, max_pages: int = 10) -> str:
    """Extract text from a PDF file (first N pages)."""
    try:
        import pdfplumber
    except ImportError:
        log.warning("pdfplumber_missing", hint="pip install pdfplumber")
        return ""

    p = Path(path)
    if not p.exists():
        log.error("pdf_not_found", path=path)
        return ""

    parts: list[str] = []
    try:
        with pdfplumber.open(str(p)) as pdf:
            for i, page in enumerate(pdf.pages[:max_pages]):
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(text)
        result = "\n\n".join(parts)
        log.info("pdf_extracted", path=path, chars=len(result), pages=len(parts))
        return result
    except Exception as e:
        log.error("pdf_extract_failed", path=path, error=str(e))
        return ""


if __name__ == "__main__":
    print("[TEST] PDF Reader")
    print("  (No sample PDF — this is a stub test)")
    print("  Function ready: extract_pdf_text('path/to/file.pdf')")