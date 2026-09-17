"""Compatibilidade: modelos canônicos vivem em digital_infrastructure."""
from ..digital_infrastructure.models import EntityRecord, ProvenanceRecord, ValidationStatus, utc_now_iso

__all__ = ["EntityRecord", "ProvenanceRecord", "ValidationStatus", "utc_now_iso"]
