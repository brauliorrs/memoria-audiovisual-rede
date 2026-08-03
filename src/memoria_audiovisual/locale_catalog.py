from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DEFAULT_LANGUAGE = "pt"
SUPPORTED_LANGUAGES = ("pt", "en", "es")
LOCALE_DIR = Path(__file__).resolve().parent / "locales"


@lru_cache(maxsize=None)
def load_locale(language: str) -> dict[str, str]:
    language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    path = LOCALE_DIR / f"{language}.json"
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in payload.items()):
        raise ValueError(f"Invalid locale catalogue: {path}")
    return payload


def translate_key(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    default_catalogue = load_locale(DEFAULT_LANGUAGE)
    catalogue = load_locale(language)
    text = catalogue.get(key, default_catalogue.get(key, key))
    return text.format(**kwargs) if kwargs else text


def validate_catalogues() -> dict[str, set[str]]:
    canonical = set(load_locale(DEFAULT_LANGUAGE))
    return {
        language: canonical - set(load_locale(language))
        for language in SUPPORTED_LANGUAGES
        if language != DEFAULT_LANGUAGE
    }
