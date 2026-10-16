"""
Prompt loader utility.
Loads prompt templates from the prompts/ folder and caches them.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache(maxsize=16)
def load_prompt(name: str) -> str:
    """
    Load a prompt template by name (without .txt extension).

    Example:
        load_prompt("intent_prompt")
    """
    if name.endswith(".txt"):
        name = name[:-4]
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8").strip()


if __name__ == "__main__":
    print("[TEST] Prompt Loader")
    for name in ["summary_prompt", "intent_prompt", "sentiment_prompt",
                 "entity_prompt", "response_prompt"]:
        content = load_prompt(name)
        print(f"  [OK] {name}.txt ({len(content)} chars)")
    print("\n[DONE] All prompts loaded!")