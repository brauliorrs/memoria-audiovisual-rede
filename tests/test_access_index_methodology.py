from __future__ import annotations

import json
from pathlib import Path

from memoria_audiovisual.analytics.indicators.access import (
    AudiovisualArchiveAccessIndex,
)

ROOT = Path(__file__).resolve().parents[1]
METHODOLOGY_PATH = ROOT / "data/templates/analytics/methodology_registry.json"


def _access_methodology() -> dict:
    payload = json.loads(METHODOLOGY_PATH.read_text(encoding="utf-8"))
    rows = payload["methodologies"]
    return next(
        item
        for item in rows
        if item["indicator_id"] == "audiovisual_archive_access_index"
    )


def test_access_index_methodology_is_registered_and_versioned():
    payload = json.loads(METHODOLOGY_PATH.read_text(encoding="utf-8"))
    methodology = _access_methodology()

    assert payload["registry_version"] == "1.3.0"
    assert methodology["indicator_version"] == AudiovisualArchiveAccessIndex.version
    assert methodology["methodology_version"] == AudiovisualArchiveAccessIndex.methodology_version
    assert methodology["formula"] == (
        "100 * arquivos_elegiveis_sem_barreira_observada / "
        "arquivos_elegiveis_avaliaveis"
    )


def test_access_index_methodology_declares_denominator_and_exclusions():
    methodology = _access_methodology()

    assert set(methodology["included_statuses"]) == {
        "detected",
        "not_detected",
        "unknown",
    }
    assert set(methodology["excluded_statuses"]) == {
        "error",
        "not_assessable",
        "missing_observation",
    }
    assert "corpus científico" in methodology["denominator_rule"]
    assert "bancos comerciais pagos" in methodology["exclusion_policy"]
    assert len(methodology["evidence_requirements"]) >= 5
    assert len(methodology["limitations"]) >= 3


def test_access_index_methodology_covers_implemented_barriers():
    methodology = _access_methodology()
    normalized_terms = {
        term.casefold().replace("-", " ")
        for term in methodology["barrier_terms"]
    }

    expected_terms = {
        "cadastro",
        "registro",
        "login",
        "autenticação",
        "solicitação formal",
        "formulário de acesso",
        "autorização institucional",
        "paid access",
        "pagamento",
        "assinatura",
    }
    assert expected_terms <= normalized_terms
