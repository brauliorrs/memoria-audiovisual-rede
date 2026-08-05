from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DEFAULT_LANGUAGE = "pt"
SUPPORTED_LANGUAGES = ("pt", "en", "es")
LOCALE_DIR = Path(__file__).resolve().parent / "locales"

# Compatibilidade temporária com a tabela de atualização do observatório.
# O renderizador ainda aplica formatação a estas colunas por seus rótulos
# históricos em português depois de renomeá-las. Manter os quatro rótulos
# estáveis evita KeyError em inglês e espanhol até que o renderizador passe
# a trabalhar exclusivamente com nomes internos antes da apresentação.
LEGACY_REFRESH_TABLE_LABELS = {
    "overview.table.column.incluida_na_ultima_rodada": "incluída na última rodada",
    "overview.table.column.situacao_na_ultima_rodada": "situação na última rodada",
    "overview.table.column.ultima_rodada_bem_sucedida": "última rodada bem-sucedida",
    "overview.table.column.ultima_observacao_registrada": "última observação registrada",
}


@lru_cache(maxsize=None)
def load_locale(language: str = DEFAULT_LANGUAGE) -> dict[str, str]:
    language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    path = LOCALE_DIR / f"{language}.json"
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in payload.items()):
        raise ValueError(f"Invalid locale catalogue: {path}")
    return payload


def translate_key(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    if key in LEGACY_REFRESH_TABLE_LABELS:
        text = LEGACY_REFRESH_TABLE_LABELS[key]
    else:
        catalogue = load_locale(language)
        text = catalogue.get(key, key)
    return text.format(**kwargs) if kwargs else text


def validate_catalogues() -> dict[str, set[str]]:
    """Return missing keys for every active translation catalogue."""
    canonical = set(load_locale(DEFAULT_LANGUAGE))
    return {
        language: canonical - set(load_locale(language))
        for language in SUPPORTED_LANGUAGES
        if language != DEFAULT_LANGUAGE
    }
