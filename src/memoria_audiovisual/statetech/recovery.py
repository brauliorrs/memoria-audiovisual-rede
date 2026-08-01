"""Inspeção e recuperação cautelosa de cauda truncada do ledger JSONL."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    path: str
    valid_lines: int
    invalid_line: int | None
    invalid_reason: str | None
    repaired: bool
    backup_path: str | None


class LedgerRecovery:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def inspect(self) -> RecoveryReport:
        if not self.path.exists():
            return RecoveryReport(str(self.path), 0, None, None, False, None)
        valid = 0
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    if not isinstance(payload, dict) or "transaction_id" not in payload or "records" not in payload:
                        raise ValueError("estrutura de transação inválida")
                except (json.JSONDecodeError, ValueError) as exc:
                    return RecoveryReport(str(self.path), valid, line_number, str(exc), False, None)
                valid += 1
        return RecoveryReport(str(self.path), valid, None, None, False, None)

    def repair_truncated_tail(self) -> RecoveryReport:
        report = self.inspect()
        if report.invalid_line is None:
            return report
        lines = self.path.read_text(encoding="utf-8").splitlines(keepends=True)
        nonempty_after = any(line.strip() for line in lines[report.invalid_line :])
        if nonempty_after:
            raise ValueError("falha não está restrita à cauda; reparo automático bloqueado")
        backup = self.path.with_suffix(self.path.suffix + ".bak")
        backup.write_bytes(self.path.read_bytes())
        kept = lines[: report.invalid_line - 1]
        self.path.write_text("".join(kept), encoding="utf-8")
        return RecoveryReport(
            path=str(self.path),
            valid_lines=report.valid_lines,
            invalid_line=report.invalid_line,
            invalid_reason=report.invalid_reason,
            repaired=True,
            backup_path=str(backup),
        )
