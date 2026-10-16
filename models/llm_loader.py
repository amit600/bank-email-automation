"""
LLM Loader for the Bank Email Automation System.
Connects to Llama 3 via Ollama and provides invoke helpers.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config.config_loader import load_config


# ============================================================
# LLM SINGLETON
# ============================================================

@lru_cache(maxsize=1)
def get_llm() -> Ollama:
    """
    Get a cached Llama 3 instance via Ollama.
    First call initializes; subsequent calls reuse.
    """
    cfg = load_config()
    llm_cfg = cfg.get("llm", {})

    llm = Ollama(
        model=llm_cfg.get("model", "llama3"),
        base_url=llm_cfg.get("base_url", "http://localhost:11434"),
        temperature=llm_cfg.get("temperature", 0.2),
        num_predict=llm_cfg.get("max_tokens", 1024),
    )
    return llm


# ============================================================
# BASIC INVOKE
# ============================================================

def invoke_llm(prompt: str) -> str:
    """
    Send a prompt to Llama 3 and get a text response.

    Args:
        prompt: The full prompt string.

    Returns:
        LLM response as plain text (stripped).
    """
    llm = get_llm()
    chain = PromptTemplate.from_template("{input}") | llm | StrOutputParser()
    response = chain.invoke({"input": prompt})
    return response.strip()


# ============================================================
# JSON INVOKE (for structured agents)
# ============================================================

def _extract_json(text: str) -> str:
    """
    Extract JSON from LLM response.
    LLMs sometimes wrap JSON in markdown code fences or add extra text.
    This strips those.
    """
    text = text.strip()

    # Remove markdown code fences
    fence_pattern = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
    match = fence_pattern.search(text)
    if match:
        return match.group(1).strip()

    # Try to find first { ... } or [ ... ]
    for opener, closer in [("{", "}"), ("[", "]")]:
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1].strip()

    return text


def invoke_llm_json(prompt: str, retries: int = 2) -> Any:
    """
    Send a prompt expecting JSON output. Retries on parse failure.

    Args:
        prompt: The full prompt string (must ask for JSON).
        retries: Number of retries on JSON parse failure.

    Returns:
        Parsed Python object (dict or list).

    Raises:
        ValueError: If JSON cannot be parsed after retries.
    """
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            raw = invoke_llm(prompt)
            cleaned = _extract_json(raw)
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            last_error = e
            # On retry, add hint to prompt
            prompt = (
                prompt
                + "\n\nIMPORTANT: Your previous response was not valid JSON. "
                  "Reply with ONLY valid JSON. No markdown, no explanation."
            )
        except Exception as e:
            last_error = e
            break

    raise ValueError(f"Failed to get valid JSON from LLM: {last_error}")


# ============================================================
# HEALTH CHECK
# ============================================================

def check_llm_health() -> bool:
    """Quick health check — is Llama 3 reachable?"""
    try:
        response = invoke_llm("Reply with exactly one word: OK")
        return "ok" in response.lower()
    except Exception:
        return False


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    print("[TEST] LLM Loader")
    print("=" * 50)

    # Test 1: Basic invoke
    print("\n[Test 1] Basic prompt:")
    response = invoke_llm("Reply with exactly: Hello from Llama 3")
    print(f"  Response: {response}")

    # Test 2: JSON invoke
    print("\n[Test 2] JSON prompt:")
    json_prompt = """Extract the account number from this email.
Return ONLY a JSON object like: {"account_number": "1234567890"}

Email: "Please provide balance for account 9876543210"
"""
    result = invoke_llm_json(json_prompt)
    print(f"  Result: {result}")
    print(f"  Type: {type(result).__name__}")

    # Test 3: Intent classification
    print("\n[Test 3] Intent classification:")
    intent_prompt = """Classify this email into ONE of these intents:
- balance_enquiry
- card_usage
- statement_request

Return ONLY JSON: {"intent": "<one_of_the_above>"}

Email: "Please share my last 5 credit card transactions for card 4567XXXX8901."
"""
    intent_result = invoke_llm_json(intent_prompt)
    print(f"  Result: {intent_result}")

    # Test 4: Health check
    print("\n[Test 4] Health check:")
    print(f"  LLM healthy: {check_llm_health()}")

    print("\n[DONE] LLM Loader tests passed!")