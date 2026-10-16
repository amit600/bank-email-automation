"""
Attachment handler with file safety layer.
Downloads and validates email attachments (PDF, images) safely.

Safety checks:
1. File size limit
2. Allowed MIME types / extensions
3. Malware signature scan (basic)
4. Safe filename sanitization
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from config.config_loader import load_config
from utils.logger import get_logger

log = get_logger("attachment_handler")


# ============================================================
# ALLOWED TYPES & LIMITS
# ============================================================

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt"}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "text/plain",
}

# Basic EICAR-style malware signature patterns (real AV is much more complex)
MALWARE_SIGNATURES = [
    b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR",
    b"<script>alert(",
    b"eval(base64_decode",
    b"powershell -encodedcommand",
]

# Dangerous filenames
DANGEROUS_EXT = {".exe", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".js", ".scr"}


# ============================================================
# CUSTOM EXCEPTIONS
# ============================================================

class AttachmentError(Exception):
    """Base attachment error."""
    pass


class UnsupportedFileTypeError(AttachmentError):
    pass


class FileTooLargeError(AttachmentError):
    pass


class MalwareDetectedError(AttachmentError):
    pass


# ============================================================
# SAFETY CHECKS
# ============================================================

def _safe_filename(name: str) -> str:
    """Sanitize filename — remove path traversal, control chars."""
    name = Path(name).name                    # strip directories
    name = re.sub(r"[^\w.\-]", "_", name)     # whitelist chars
    name = name.strip("._")
    if not name:
        name = "attachment"
    return name[:200]


def _get_limits() -> tuple[set[str], int]:
    """Read allowed types + max size from config."""
    try:
        cfg = load_config()
        sec = cfg.get("security", {})
        allowed = set(sec.get("allowed_file_types", []))
        allowed = {"." + a.lstrip(".") for a in allowed} or ALLOWED_EXTENSIONS
        max_mb = int(sec.get("max_file_size_mb", 5))
    except Exception:
        allowed = ALLOWED_EXTENSIONS
        max_mb = 5
    return allowed, max_mb


def check_extension(filename: str) -> None:
    """Raise if extension not allowed."""
    allowed, _ = _get_limits()
    ext = Path(filename).suffix.lower()
    if ext in DANGEROUS_EXT:
        raise UnsupportedFileTypeError(f"Dangerous file type blocked: {ext}")
    if ext not in allowed:
        raise UnsupportedFileTypeError(
            f"Extension {ext} not allowed. Allowed: {allowed}"
        )


def check_mime(content_type: str) -> None:
    """Raise if MIME not allowed."""
    if not content_type:
        return  # some clients don't send — allow
    ct = content_type.split(";")[0].strip().lower()
    if ct not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError(
            f"MIME type {ct} not allowed. Allowed: {ALLOWED_MIME_TYPES}"
        )


def check_size(size_bytes: int) -> None:
    """Raise if file too large."""
    _, max_mb = _get_limits()
    max_bytes = max_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileTooLargeError(
            f"File size {size_bytes} bytes exceeds limit {max_bytes} bytes"
        )


def scan_for_malware(content: bytes) -> None:
    """Basic signature scan."""
    for sig in MALWARE_SIGNATURES:
        if sig in content:
            raise MalwareDetectedError(
                f"Malware signature detected: {sig[:30]}..."
            )


# ============================================================
# MAIN API
# ============================================================

class AttachmentHandler:
    """Download + validate attachments safely."""

    def __init__(self, save_dir: str = "logs/attachments"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def process(
        self,
        filename: str,
        content: bytes,
        content_type: str = "",
    ) -> dict[str, Any]:
        """
        Validate and save an attachment.

        Returns dict:
        {
          "safe": bool,
          "filename": <sanitized>,
          "path": <saved path or None>,
          "size_bytes": int,
          "content_type": str,
          "error": <message or None>,
        }
        """
        result: dict[str, Any] = {
            "safe": False,
            "filename": _safe_filename(filename),
            "path": None,
            "size_bytes": len(content),
            "content_type": content_type,
            "error": None,
        }

        try:
            check_extension(filename)
            check_mime(content_type)
            check_size(len(content))
            scan_for_malware(content)

            # Save
            dest = self.save_dir / result["filename"]
            dest.write_bytes(content)
            result["path"] = str(dest)
            result["safe"] = True
            log.info(
                "attachment_saved",
                filename=result["filename"],
                size=result["size_bytes"],
                content_type=content_type,
            )

        except AttachmentError as e:
            result["error"] = str(e)
            log.warning(
                "attachment_rejected",
                filename=filename,
                error=str(e),
            )
        except Exception as e:
            result["error"] = f"Unexpected: {e}"
            log.error("attachment_error", filename=filename, error=str(e))

        return result

    def extract_text(self, path: str) -> str:
        """
        Extract text from PDF or image.
        Delegates to pdf_reader / ocr based on file type.
        """
        p = Path(path)
        if not p.exists():
            raise AttachmentError(f"File not found: {path}")

        ext = p.suffix.lower()

        if ext == ".pdf":
            from utils.pdf_reader import extract_pdf_text
            return extract_pdf_text(str(p))
        elif ext in {".png", ".jpg", ".jpeg"}:
            from utils.ocr import extract_image_text
            return extract_image_text(str(p))
        elif ext == ".txt":
            return p.read_text(encoding="utf-8", errors="ignore")
        else:
            return ""


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    print("[TEST] Attachment Handler")
    print("=" * 60)

    handler = AttachmentHandler(save_dir="logs/attachments_test")

    # 1. Valid PDF
    print("\n[1] Valid PDF:")
    r = handler.process("statement.pdf", b"%PDF-1.4 mock content", "application/pdf")
    print(f"    safe={r['safe']} error={r['error']}")

    # 2. Too large (simulate)
    print("\n[2] File too large (6 MB, limit 5 MB):")
    big_content = b"a" * (6 * 1024 * 1024)
    r = handler.process("big.pdf", big_content, "application/pdf")
    print(f"    safe={r['safe']} error={r['error']}")

    # 3. Dangerous extension
    print("\n[3] Dangerous .exe:")
    r = handler.process("virus.exe", b"binary", "application/octet-stream")
    print(f"    safe={r['safe']} error={r['error']}")

    # 4. Malware signature
    print("\n[4] Malware signature (EICAR):")
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR"
    r = handler.process("test.txt", eicar, "text/plain")
    print(f"    safe={r['safe']} error={r['error']}")

    # 5. Path traversal attempt
    print("\n[5] Path traversal:")
    r = handler.process("../../etc/passwd.pdf", b"%PDF-1.4", "application/pdf")
    print(f"    filename sanitized: {r['filename']} safe={r['safe']}")

    print("\n[DONE] Attachment Handler tests complete!")

    # Cleanup
    shutil.rmtree("logs/attachments_test", ignore_errors=True)