"""Compatibilidade: ledger canônico vive em digital_infrastructure."""
from ..digital_infrastructure.ledger import AtomicLedger, LedgerEntry

__all__ = ["AtomicLedger", "LedgerEntry"]
