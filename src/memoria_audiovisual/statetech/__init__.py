"""Núcleo executável da camada Estado–tecnologia."""

from .ids import stable_id, version_id
from .models import EntityRecord, ProvenanceRecord
from .persistence import JsonlRepository

__all__ = [
    "EntityRecord",
    "JsonlRepository",
    "ProvenanceRecord",
    "stable_id",
    "version_id",
]
