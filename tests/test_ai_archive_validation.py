from memoria_audiovisual.digital_infrastructure.ai_archive_validation import (
    validate_ai_use_in_observed_archive,
)
from memoria_audiovisual.digital_infrastructure.ai_content_production import (
    classify_ai_content_usage,
)


def test_term_positive_outside_corpus_is_not_archive_positive():
    terminology = classify_ai_content_usage(
        entity_id="bfi",
        item_id="external-film",
        texts=["The film used AI-assisted production."],
    )
    result = validate_ai_use_in_observed_archive(
        terminology,
        item_in_observed_corpus=False,
        evidence_linked_to_item=True,
    )
    assert terminology.is_ai_positive
    assert result.status == "item_outside_observed_corpus"
    assert result.is_archive_ai_positive is False


def test_general_archive_page_is_not_item_level_observation():
    terminology = classify_ai_content_usage(
        entity_id="ecpad",
        item_id="archives-page",
        texts=["Intelligence artificielle utilisée dans la production audiovisuelle."],
    )
    result = validate_ai_use_in_observed_archive(
        terminology,
        is_item_level_observation=False,
        item_in_observed_corpus=True,
        evidence_linked_to_item=False,
    )
    assert result.status == "not_item_level_observation"
    assert result.is_archive_ai_positive is False


def test_institution_ai_article_without_item_link_is_not_archive_positive():
    terminology = classify_ai_content_usage(
        entity_id="example",
        item_id="item-1",
        texts=["The production used generative AI to create images."],
    )
    result = validate_ai_use_in_observed_archive(
        terminology,
        item_in_observed_corpus=True,
        evidence_linked_to_item=False,
    )
    assert result.status == "evidence_not_linked_to_item"
    assert result.is_archive_ai_positive is False


def test_only_two_positive_gates_confirm_ai_in_archive():
    terminology = classify_ai_content_usage(
        entity_id="example",
        item_id="item-2",
        texts=["The documentary used an AI-generated voice."],
    )
    result = validate_ai_use_in_observed_archive(
        terminology,
        item_in_observed_corpus=True,
        evidence_linked_to_item=True,
    )
    assert result.status == "confirmed_ai_use_in_observed_archive"
    assert result.is_archive_ai_positive is True


def test_gate2_is_not_run_as_positive_when_gate1_is_negative():
    terminology = classify_ai_content_usage(
        entity_id="example",
        item_id="item-3",
        texts=["Historical film digitised in 2024."],
    )
    result = validate_ai_use_in_observed_archive(
        terminology,
        item_in_observed_corpus=True,
        evidence_linked_to_item=True,
    )
    assert result.status == "gate1_terminology_not_positive"
    assert result.is_archive_ai_positive is False


def test_unknown_membership_or_link_is_not_assessable():
    terminology = classify_ai_content_usage(
        entity_id="example",
        item_id="item-4",
        texts=["The film used AI-assisted editing."],
    )
    result = validate_ai_use_in_observed_archive(
        terminology,
        item_in_observed_corpus=None,
        evidence_linked_to_item=True,
    )
    assert result.status == "not_assessable"
    assert result.is_archive_ai_positive is False
