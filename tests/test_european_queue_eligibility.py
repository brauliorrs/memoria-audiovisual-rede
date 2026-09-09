from memoria_audiovisual.digital_infrastructure.european_queue import (
    SOURCE_ONLY_STATUS,
    candidate_from_queue_row,
    evaluate_queue_rows,
    is_source_only,
)


def _individual_row(**overrides):
    row = {
        "unit_code": "fiaf-example",
        "unit_label": "Example Film Archive",
        "unit_type": "arquivo_audiovisual_individual",
        "source_family": "FIAF",
        "country_or_scope": "Portugal",
        "territorial_scope": "Portugal",
        "source_url": "https://example.org",
        "audiovisual_relevance": "arquivo, cinemateca e acervo audiovisual",
        "queue_layer": "fila_definitiva_um_por_um",
        "queue_decision": "avaliar_arquivo_individual_um_por_um",
        "definitive_queue_rank": "7",
        "queue_reason": "Avaliação individual necessária.",
        "next_action": "sondar_site_catalogo_api_e_disponibilidade_audiovisual",
        "inclusion_gate": "só incorporar após validar rota pública",
        "video_location_candidate_url": "https://example.org/catalog",
        "evidence_reference": "Lista oficial da FIAF.",
        "rule_version": "2026-05-pesquisa-europa-v3",
    }
    row.update(overrides)
    return row


def test_directory_is_preserved_as_source_only():
    row = _individual_row(
        unit_code="fiaf-members",
        unit_type="diretorio_de_arquivos_filmicos",
        queue_layer="fonte_de_fila",
        queue_decision="expandir_diretorio_para_fila_individual",
        inclusion_gate="não entra como corpus; gera candidatos individuais verificáveis",
    )
    assert is_source_only(row)
    result = evaluate_queue_rows((row,))[0]
    assert result.evaluation_status == SOURCE_ONLY_STATUS
    assert result.gate_result is None


def test_individual_candidate_requires_review_without_confirmations():
    result = evaluate_queue_rows((_individual_row(),))[0]
    assert result.evaluation_status == "requires_human_review"
    assert result.gate_result is not None
    assert "audiovisual_relevance" in result.gate_result.unknown_codes
    assert "institutional_identity" in result.gate_result.unknown_codes
    assert "observable_surface" in result.gate_result.unknown_codes
    assert "curatorial_decision" in result.gate_result.unknown_codes


def test_explicit_confirmations_still_require_curatorial_decision():
    row = _individual_row(
        audiovisual_relevance_confirmed="true",
        institutional_identity_confirmed="true",
        observable_surface_confirmed="true",
    )
    result = evaluate_queue_rows((row,))[0]
    assert result.evaluation_status == "requires_human_review"
    assert result.gate_result is not None
    assert result.gate_result.unknown_codes == ("curatorial_decision",)


def test_queue_text_is_not_silently_promoted_to_empirical_confirmation():
    candidate = candidate_from_queue_row(_individual_row())
    assert candidate.audiovisual_relevance is None
    assert candidate.institutional_identity_confirmed is None
    assert candidate.observable_surface is None
    assert candidate.curator_decision == "pending"


def test_queue_is_sorted_by_definitive_rank():
    later = _individual_row(unit_code="later", definitive_queue_rank="12")
    first = _individual_row(unit_code="first", definitive_queue_rank="2")
    results = evaluate_queue_rows((later, first))
    assert [item.unit_code for item in results] == ["first", "later"]
