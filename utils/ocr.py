"""
OCR utility for image attachments.
Uses pytesseract to extract text from images.
"""
from __future__ import annotations

from pathlib import Path

from utils.logger import get_logger

log = get_logger("ocr")


def extract_image_text(path: str) -> str:
    """Extract text from an image using OCR."""
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        log.warning(
            "ocr_dependencies_missing",
            hint="pip install Pillow pytesseract",
        )
        return ""

    p = Path(path)
    if not p.exists():
        log.error("image_not_found", path=path)
        return ""

    try:
        img = Image.open(str(p))
        text = pytesseract.image_to_string(img)
        result = text.strip()
        log.info("ocr_extracted", path=path, chars=len(result))
        return result
    except Exception as e:
        log.error("ocr_failed", path=path, error=str(e))
        return ""


if __name__ == "__main__":
    print("[TEST] OCR")
    print("  Note: requires Tesseract binary installed separately.")
    print("  On Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    print("  Function ready: extract_image_text('path/to/image.png')")