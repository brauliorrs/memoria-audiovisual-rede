"""Núcleo canônico de infraestrutura digital.

Durante a Onda 1, ``memoria_audiovisual.statetech`` permanece disponível como
camada de compatibilidade. Os identificadores históricos continuam usando o
namespace lógico ``statetech`` até que exista uma migração explícita de IDs.
"""

from .adapters import AdaptedRecord, SourceAdapter
from .ids import stable_id, version_id
from .ingestion import IngestionCoordinator, IngestionResumeMismatch
from .ingestion_batches import BatchManifest, BatchManifestStore
from .raw_artifacts import RawArtifact, RawArtifactStore
from .ledger import AtomicLedger, LedgerEntry
from .models import EntityRecord, ProvenanceRecord
from .persistence import JsonlRepository
from .service import DigitalInfrastructureDataService, StatetechDataService

__all__ = [
    "AdaptedRecord",
    "AtomicLedger",
    "BatchManifest",
    "BatchManifestStore",
    "DigitalInfrastructureDataService",
    "IngestionCoordinator",
    "IngestionResumeMismatch",
    "EntityRecord",
    "JsonlRepository",
    "LedgerEntry",
    "ProvenanceRecord",
    "RawArtifact",
    "RawArtifactStore",
    "SourceAdapter",
    "StatetechDataService",
    "stable_id",
    "version_id",
]
