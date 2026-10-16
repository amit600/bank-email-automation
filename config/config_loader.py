"""
Configuration loader for Bank Email Automation System.
Loads YAML config once and caches it.
"""
import os
from pathlib import Path
from functools import lru_cache
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()


class ConfigError(Exception):
    """Config-related errors."""
    pass


@lru_cache(maxsize=1)
def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load YAML configuration once and cache it."""
    if config_path is None:
        project_root = Path(__file__).resolve().parent.parent
        config_path = str(project_root / "config" / "config.yaml")

    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(config, dict):
        raise ConfigError(f"Config root must be a mapping, got {type(config)}")

    _apply_env_overrides(config)
    return config


def _apply_env_overrides(config: dict) -> None:
    """Override config values from environment variables."""
    env_map = {
        "IMAP_USER": ("email", "username"),
        "IMAP_PASS": ("email", "password"),
        "IMAP_HOST": ("email", "imap_host"),
        "SMTP_HOST": ("email", "smtp_host"),
        "OLLAMA_URL": ("llm", "base_url"),
        "LLM_MODEL": ("llm", "model"),
        "API_BASE": ("apis", "base_url"),
    }
    for env_key, (section, key) in env_map.items():
        value = os.getenv(env_key)
        if value:
            config.setdefault(section, {})[key] = value


def get(section: str, key: str, default: Any = None) -> Any:
    """Convenience getter."""
    cfg = load_config()
    return cfg.get(section, {}).get(key, default)


if __name__ == "__main__":
    cfg = load_config()
    print("[OK] Config loaded successfully")
    print(f"     App Name : {cfg['app']['name']}")
    print(f"     LLM      : {cfg['llm']['model']} @ {cfg['llm']['base_url']}")
    print(f"     API Base : {cfg['apis']['base_url']}")
    print(f"     Schedule : every {cfg['app']['schedule_interval_minutes']} min")