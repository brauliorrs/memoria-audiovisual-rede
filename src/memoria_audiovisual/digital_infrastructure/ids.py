"""Identificadores determinísticos para entidades e versões."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from typing import Any


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def stable_id(entity_type: str, natural_key: str, *, namespace: str = "digital_infrastructure") -> str:
    """Gera ID estável a partir do tipo e da chave natural.

    O sufixo criptográfico reduz colisões sem expor integralmente a chave original.
    """
    entity = _slug(entity_type)
    key = natural_key.strip()
    if not entity or not key:
        raise ValueError("entity_type e natural_key são obrigatórios")
    digest = hashlib.sha256(f"{namespace}:{entity}:{key}".encode("utf-8")).hexdigest()[:12]
    readable = _slug(key)[:48] or "registro"
    return f"{entity}_{readable}_{digest}"


def version_id(entity_id: str, payload: Mapping[str, Any]) -> str:
    """Gera ID imutável para uma versão específica de uma entidade."""
    if not entity_id.strip():
        raise ValueError("entity_id é obrigatório")
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:16]
    return f"{entity_id}@{digest}"
