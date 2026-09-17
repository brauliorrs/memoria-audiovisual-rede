"""Núcleo canônico de infraestrutura digital.

Durante a Onda 1, ``memoria_audiovisual.statetech`` permanece disponível como
camada de compatibilidade. Os identificadores históricos continuam usando o
namespace lógico ``statetech`` até que exista uma migração explícita de IDs.
"""

from .ids import stable_id, version_id
from .ledger import AtomicLedger, LedgerEntry
from .models import EntityRecord, ProvenanceRecord
from .persistence import JsonlRepository
from .service import DigitalInfrastructureDataService, StatetechDataService

__all__ = [
    "AtomicLedger",
    "DigitalInfrastructureDataService",
    "EntityRecord",
    "JsonlRepository",
    "LedgerEntry",
    "ProvenanceRecord",
    "StatetechDataService",
    "stable_id",
    "version_id",
]
