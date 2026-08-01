"""Leitura dos JSON Schemas e validações estruturais essenciais."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ContractValidationError(ValueError):
    pass


class SchemaRegistry:
    def __init__(self, repository_root: str | Path) -> None:
        self.repository_root = Path(repository_root)
        registry_path = self.repository_root / "schemas/digital_infrastructure/schema_registry.json"
        with registry_path.open("r", encoding="utf-8") as handle:
            registry = json.load(handle)
        self.schema_version = str(registry["schema_version"])
        self.paths = {item["entity"]: item["path"] for item in registry["schemas"]}

    def load(self, entity_type: str) -> dict[str, Any]:
        relative_path = self.paths.get(entity_type)
        if relative_path is None:
            raise KeyError(f"schema não registrado: {entity_type}")
        with (self.repository_root / relative_path).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def validate_structure(self, entity_type: str, record: dict[str, Any]) -> None:
        """Valida o subconjunto crítico do contrato sem biblioteca externa.

        A validação completa Draft 2020-12 poderá ser incorporada posteriormente.
        """
        schema = self.load(entity_type)
        required = set(schema.get("required", []))
        missing = sorted(required - record.keys())
        if missing:
            raise ContractValidationError(f"campos obrigatórios ausentes: {', '.join(missing)}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(record.keys() - properties.keys())
            if unknown:
                raise ContractValidationError(f"campos não previstos: {', '.join(unknown)}")

        for name, value in record.items():
            definition = properties.get(name, {})
            allowed = definition.get("enum")
            if allowed is not None and value not in allowed:
                raise ContractValidationError(f"valor inválido para {name}: {value!r}")
            min_length = definition.get("minLength")
            if min_length and isinstance(value, str) and len(value) < min_length:
                raise ContractValidationError(f"{name} não atende minLength={min_length}")
