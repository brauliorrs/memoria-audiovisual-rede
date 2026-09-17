"""Compatibilidade: locking canônico vive em digital_infrastructure."""
from ..digital_infrastructure.locking import FileWriteLock, LedgerLockTimeout

__all__ = ["FileWriteLock", "LedgerLockTimeout"]
