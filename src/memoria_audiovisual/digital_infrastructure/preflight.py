"""Validação pré-execução do ciclo periódico infraestrutura digital."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

SNAPSHOT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")


@dataclass(frozen=True, slots=True)
class PreflightIssue:
    code: str
    severity: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PreflightReport:
    snapshot_id: str
    selected_corpora: tuple[str, ...]
    history_exists: bool
    checks: int
    issues: tuple[PreflightIssue, ...]

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "selected_corpora": list(self.selected_corpora),
            "history_exists": self.history_exists,
            "checks": self.checks,
            "ok": self.ok,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class PeriodicReviewPreflight:
    """Verifica contratos, caminhos e memória antes de iniciar qualquer coleta."""

    REQUIRED_REPOSITORY_PATHS = (
        "schemas/digital_infrastructure/schema_registry.json",
        "schemas/digital_infrastructure_audit.schema.json",
        "scripts/audit_digital_infrastructure.py",
    )
    STATE_JSONL_FILES = (
        "ledger.jsonl",
        "ingestion_batches.jsonl",
        "coverage/snapshot_coverage_index.jsonl",
    )

    def __init__(self, repository_root: str | Path, state_dir: str | Path) -> None:
        self.repository_root = Path(repository_root)
        self.state_dir = Path(state_dir)

    def validate(
        self,
        *,
        snapshot_id: str,
        corpora: Mapping[str, Mapping[str, Any]],
        selected_corpora: Iterable[str] = (),
        history_exists: bool,
    ) -> PreflightReport:
        issues: list[PreflightIssue] = []
        checks = 0
        selected = tuple(dict.fromkeys(str(code).strip() for code in selected_corpora if str(code).strip()))

        checks += 1
        if not SNAPSHOT_PATTERN.fullmatch(snapshot_id):
            issues.append(PreflightIssue("PRE-001", "error", "snapshot_id inválido"))

        checks += 1
        snapshot_dir = self.state_dir / "coverage" / snapshot_id
        if snapshot_dir.exists():
            issues.append(PreflightIssue("PRE-002", "error", "snapshot_id já existe", str(snapshot_dir)))

        for relative in self.REQUIRED_REPOSITORY_PATHS:
            checks += 1
            path = self.repository_root / relative
            if not path.is_file():
                issues.append(PreflightIssue("PRE-003", "error", "arquivo estrutural ausente", str(path)))

        checks += 1
        registry_path = self.repository_root / "schemas/digital_infrastructure/schema_registry.json"
        if registry_path.is_file():
            self._validate_schema_registry(registry_path, issues)

        checks += 1
        unknown = sorted(set(selected).difference(corpora))
        if unknown:
            issues.append(PreflightIssue("PRE-004", "error", f"corpora desconhecidos: {', '.join(unknown)}"))

        checks += 1
        candidates = selected or tuple(code for code, item in corpora.items() if item.get("organism_active", False))
        without_url = sorted(code for code in candidates if code in corpora and not corpora[code].get("source_url"))
        if without_url:
            issues.append(PreflightIssue("PRE-005", "error", f"corpora sem source_url: {', '.join(without_url)}"))

        checks += 1
        if history_exists and not self.state_dir.exists():
            issues.append(PreflightIssue("PRE-006", "error", "branch histórica indicada, mas estado não foi restaurado", str(self.state_dir)))
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "coverage").mkdir(parents=True, exist_ok=True)

        for relative in self.STATE_JSONL_FILES:
            checks += 1
            path = self.state_dir / relative
            if path.exists():
                self._validate_jsonl(path, issues)

        checks += 1
        self._validate_snapshot_index(issues)

        checks += 1
        probe = self.state_dir / ".preflight-write-probe"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            issues.append(PreflightIssue("PRE-010", "error", f"estado sem permissão de escrita: {exc}", str(self.state_dir)))

        return PreflightReport(snapshot_id, selected, history_exists, checks, tuple(issues))

    def _validate_schema_registry(self, path: Path, issues: list[PreflightIssue]) -> None:
        try:
            registry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(PreflightIssue("PRE-011", "error", f"registro de schemas inválido: {exc}", str(path)))
            return
        seen: set[str] = set()
        for item in registry.get("schemas", []):
            entity = str(item.get("entity") or "")
            relative = str(item.get("path") or "")
            if not entity or not relative:
                issues.append(PreflightIssue("PRE-012", "error", "entrada incompleta no registro de schemas", str(path)))
                continue
            if entity in seen:
                issues.append(PreflightIssue("PRE-013", "error", f"schema duplicado: {entity}", str(path)))
            seen.add(entity)
            schema_path = self.repository_root / relative
            if not schema_path.is_file():
                issues.append(PreflightIssue("PRE-014", "error", f"schema registrado não existe: {relative}", str(schema_path)))
                continue
            try:
                json.loads(schema_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                issues.append(PreflightIssue("PRE-015", "error", f"schema JSON inválido: {exc}", str(schema_path)))

    @staticmethod
    def _validate_jsonl(path: Path, issues: list[PreflightIssue]) -> None:
        try:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(PreflightIssue("PRE-007", "error", f"JSONL inválido na linha {number}: {exc.msg}", str(path)))
        except OSError as exc:
            issues.append(PreflightIssue("PRE-008", "error", f"não foi possível ler o arquivo: {exc}", str(path)))

    def _validate_snapshot_index(self, issues: list[PreflightIssue]) -> None:
        index = self.state_dir / "coverage" / "snapshot_coverage_index.jsonl"
        if not index.exists():
            return
        seen: set[str] = set()
        for number, line in enumerate(index.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                return
            snapshot_id = str(item.get("snapshot_id") or "")
            if not snapshot_id:
                issues.append(PreflightIssue("PRE-016", "error", f"índice sem snapshot_id na linha {number}", str(index)))
                continue
            if snapshot_id in seen:
                issues.append(PreflightIssue("PRE-017", "error", f"snapshot duplicado no índice: {snapshot_id}", str(index)))
            seen.add(snapshot_id)
            coverage_path = self.state_dir / "coverage" / snapshot_id / "parameter_coverage.json"
            if not coverage_path.is_file():
                issues.append(PreflightIssue("PRE-018", "error", f"snapshot indexado sem cobertura: {snapshot_id}", str(coverage_path)))
