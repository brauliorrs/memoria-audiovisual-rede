"""Núcleo executável da camada infraestrutura digital."""

from .ai_contracts import (
    AIEvidenceReference,
    AIExperimentRecord,
    AIExperimentRunManifest,
    AIModelDescriptor,
)
from .ai_flags import AIExperimentFlags
from .ai_runtime import AIExperimentContext, AIShadowRunner
from .ai_storage import AIExperimentStore
from .ids import stable_id, version_id
from .models import EntityRecord, ProvenanceRecord
from .persistence import JsonlRepository

__all__ = [
    "AIEvidenceReference",
    "AIExperimentContext",
    "AIExperimentFlags",
    "AIExperimentRecord",
    "AIExperimentRunManifest",
    "AIExperimentStore",
    "AIModelDescriptor",
    "AIShadowRunner",
    "EntityRecord",
    "JsonlRepository",
    "ProvenanceRecord",
    "stable_id",
    "version_id",
]
