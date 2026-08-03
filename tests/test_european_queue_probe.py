from memoria_audiovisual.digital_infrastructure.european_queue import evaluate_queue_rows
from memoria_audiovisual.digital_infrastructure.queue_probe import apply_probe_to_row


def _row():
    return {
        "unit_code": "candidate-1",
        "unit_label": "Candidate One",
        "unit_type": "arquivo_audiovisual_individual",
        "source_family": "FIAF",
        "territorial_scope": "França",
        "source_url": "https://example.org",
        "audiovisual_relevance": "arquivo audiovisual",
        "queue_layer": "fila_definitiva_um_por_um",
        "queue_decision": "avaliar_arquivo_individual_um_por_um",
        "definitive_queue_rank": "1",
        "video_location_candidate_url": "https://example.org/catalog",
        "evidence_reference": "diretório oficial",
        "inclusion_gate": "validar antes de incorporar",
    }


def test_probe_fills_only_technical_facts_and_keeps_curatorial_review():
    probe = {
        "unit_code": "candidate-1",
        "checked_at_utc": "2026-08-03T12:00:00Z",
        "observable_surface_confirmed": True,
        "institutional_identity_confirmed": True,
        "audiovisual_relevance_confirmed": True,
        "evidence_ids": ["probe:candidate-1:http-status", "probe:candidate-1:signal:video"],
        "error": "",
    }
    enriched = apply_probe_to_row(_row(), probe)
    assert enriched["observable_surface_confirmed"] == "true"
    assert enriched["institutional_identity_confirmed"] == "true"
    assert enriched["audiovisual_relevance_confirmed"] == "true"
    assert enriched["technical_evidence_ids"].startswith("probe:candidate-1")

    result = evaluate_queue_rows((enriched,))[0]
    assert result.evaluation_status == "requires_human_review"
    assert result.gate_result is not None
    assert "curatorial_decision" in result.gate_result.unknown_codes
    assert result.gate_result.automatic is False


def test_missing_probe_keeps_empirical_facts_unknown():
    enriched = apply_probe_to_row(_row(), None)
    result = evaluate_queue_rows((enriched,))[0]
    assert result.gate_result is not None
    assert "audiovisual_relevance" in result.gate_result.unknown_codes
    assert "institutional_identity" in result.gate_result.unknown_codes
    assert "observable_surface" in result.gate_result.unknown_codes


def test_negative_observable_surface_is_objective_rejection():
    probe = {
        "unit_code": "candidate-1",
        "observable_surface_confirmed": False,
        "institutional_identity_confirmed": None,
        "audiovisual_relevance_confirmed": None,
        "evidence_ids": ["probe:candidate-1:http-status"],
    }
    result = evaluate_queue_rows((apply_probe_to_row(_row(), probe),))[0]
    assert result.evaluation_status == "rejected"
    assert result.gate_result is not None
    assert "observable_surface" in result.gate_result.failed_codes
