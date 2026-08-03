"""Bloqueio cooperativo de escrita para o ledger local."""

from __future__ import annotations

import os
import time
from pathlib import Path


class LedgerLockTimeout(TimeoutError):
    """O lock não pôde ser adquirido dentro do prazo configurado."""


class FileWriteLock:
    """Lock por arquivo criado de forma exclusiva.

    É adequado ao backend JSONL local e evita dois processos cooperativos
    escrevendo simultaneamente. Não substitui transações de banco de dados.
    """

    def __init__(self, target: str | Path, *, timeout: float = 10.0, poll_interval: float = 0.05) -> None:
        self.path = Path(f"{Path(target)}.lock")
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._acquired = False

    def acquire(self) -> None:
        deadline = time.monotonic() + self.timeout
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(f"pid={os.getpid()}\n")
                self._acquired = True
                return
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise LedgerLockTimeout(f"tempo esgotado aguardando lock: {self.path}")
                time.sleep(self.poll_interval)

    def release(self) -> None:
        if not self._acquired:
            return
        try:
            self.path.unlink(missing_ok=True)
        finally:
            self._acquired = False

    def __enter__(self) -> "FileWriteLock":
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()
