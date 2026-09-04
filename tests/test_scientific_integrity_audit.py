from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_audiovisual.scientific_infrastructure.scientific_integrity_audit import (
    IntegrityFinding,
    ScientificIntegrityReport,
    assert_scientific_integrity,
    audit_scientific_integrity,
)

ROOT = Path(__file__).resolve().parents[1]


def test_repository_scientific_integrity_contract_passes():
    report = audit_scientific_integrity(ROOT)
    assert report.is_valid
    assert report.indicator_count == 9
    assert report.implementation_count == 9
    assert report.methodology_count == 9
    assert report.pending_methodologies == ()
    assert_scientific_integrity(report)


def test_integrity_assertion_reports_contract_and_message():
    report = ScientificIntegrityReport(
        registry_version="1.0.0",
        indicator_count=1,
        implementation_count=0,
        methodology_count=0,
        pending_methodologies=(),
        findings=(IntegrityFinding("registry_implementation", "sem implementação: x"),),
    )
    with pytest.raises(ValueError, match=r"\[registry_implementation\].*sem implementação: x"):
        assert_scientific_integrity(report)


def test_legacy_catalog_is_forbidden(tmp_path: Path):
    source_registry = ROOT / "data/templates/analytics/indicator_registry.json"
    source_methodology = ROOT / "data/templates/analytics/methodology_registry.json"
    target_registry = tmp_path / "data/templates/analytics/indicator_registry.json"
    target_methodology = tmp_path / "data/templates/analytics/methodology_registry.json"
    target_registry.parent.mkdir(parents=True)
    target_registry.write_text(source_registry.read_text(encoding="utf-8"), encoding="utf-8")
    target_methodology.write_text(source_methodology.read_text(encoding="utf-8"), encoding="utf-8")

    interface_source = ROOT / "src/memoria_audiovisual/ui/scientific_infrastructure.py"
    interface_target = tmp_path / "src/memoria_audiovisual/ui/scientific_infrastructure.py"
    interface_target.parent.mkdir(parents=True)
    interface_target.write_text(interface_source.read_text(encoding="utf-8"), encoding="utf-8")

    legacy_path = tmp_path / "data/templates/analytics/indicator_catalog.json"
    legacy_path.write_text(json.dumps({"indicators": []}), encoding="utf-8")

    report = audit_scientific_integrity(tmp_path)
    assert any(
        finding.contract == "single_source" and "catálogo legado" in finding.message
        for finding in report.findings
    )


def test_methodology_registry_version_mismatch_is_blocking(tmp_path: Path):
    source_registry = ROOT / "data/templates/analytics/indicator_registry.json"
    source_methodology = ROOT / "data/templates/analytics/methodology_registry.json"
    target_registry = tmp_path / "data/templates/analytics/indicator_registry.json"
    target_methodology = tmp_path / "data/templates/analytics/methodology_registry.json"
    target_registry.parent.mkdir(parents=True)
    target_registry.write_text(source_registry.read_text(encoding="utf-8"), encoding="utf-8")

    methodology_payload = json.loads(source_methodology.read_text(encoding="utf-8"))
    methodology_payload["registry_version"] = "9.9.9"
    target_methodology.write_text(
        json.dumps(methodology_payload, ensure_ascii=False),
        encoding="utf-8",
    )

    interface_source = ROOT / "src/memoria_audiovisual/ui/scientific_infrastructure.py"
    interface_target = tmp_path / "src/memoria_audiovisual/ui/scientific_infrastructure.py"
    interface_target.parent.mkdir(parents=True)
    interface_target.write_text(interface_source.read_text(encoding="utf-8"), encoding="utf-8")

    report = audit_scientific_integrity(tmp_path)
    assert any(
        finding.contract == "methodology" and "versão do registro metodológico divergente" in finding.message
        for finding in report.findings
    )
