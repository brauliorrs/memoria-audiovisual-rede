"""Compatibilidade para o antigo namespace Estado–tecnologia.

Novos consumidores devem importar de ``memoria_audiovisual.digital_infrastructure``.
"""

from ..digital_infrastructure.ids import stable_id, version_id
from ..digital_infrastructure.models import EntityRecord, ProvenanceRecord
from ..digital_infrastructure.persistence import JsonlRepository

__all__ = [
    "EntityRecord",
    "JsonlRepository",
    "ProvenanceRecord",
    "stable_id",
    "version_id",
]
