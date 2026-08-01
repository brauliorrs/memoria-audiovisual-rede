"""Validação integral dos contratos JSON Schema da camada Estado–tecnologia."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .contracts import ContractValidationError, SchemaRegistry


class ContractValidator:
    def __init__(self, registry: SchemaRegistry) -> None:
        self.registry = registry
        self.format_checker = FormatChecker()

    def validate(self, entity_type: str, record: Mapping[str, Any]) -> None:
        schema = self.registry.load(entity_type)
        validator = Draft202012Validator(schema, format_checker=self.format_checker)
        errors = sorted(validator.iter_errors(dict(record)), key=lambda error: list(error.absolute_path))
        if not errors:
            return
        messages: list[str] = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "$"
            messages.append(f"{location}: {error.message}")
        raise ContractValidationError("; ".join(messages))
