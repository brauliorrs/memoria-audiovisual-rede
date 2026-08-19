from memoria_audiovisual.digital_infrastructure.surface_typing import (
    SURFACE_TYPES,
    classify_surface_type,
)


def test_vocabulary_keeps_institutional_and_archive_landing_pages_separate():
    assert "institutional_landing_page" in SURFACE_TYPES
    assert "archive_landing_page" in SURFACE_TYPES


def test_ina_root_non_home_path_is_institutional_landing_page():
    decision = classify_surface_type(
        url="https://www.ina.fr/institut-national-audiovisuel",
        root_url="https://www.ina.fr/institut-national-audiovisuel",
        title="Institut national de l'audiovisuel",
        text="L'INA conserve et valorise le patrimoine audiovisuel.",
    )
    assert decision.surface_type == "institutional_landing_page"
    assert decision.is_item_level is False


def test_ecpad_general_archives_page_is_archive_landing_page():
    decision = classify_surface_type(
        url="https://archives.ecpad.fr/archives/archives",
        root_url="https://archives.ecpad.fr/archives/archives",
        title="Archives - ECPAD",
        text="Consulter les archives et explorer les collections.",
    )
    assert decision.surface_type == "archive_landing_page"
    assert decision.is_item_level is False


def test_search_surface_is_not_item_level():
    decision = classify_surface_type(
        url="https://example.org/recherche?q=timor",
        root_url="https://example.org/",
        title="Résultats de recherche",
        text="Résultats pour Timor",
    )
    assert decision.surface_type == "search_or_index"
    assert decision.is_item_level is False


def test_news_article_is_editorial_not_item():
    decision = classify_surface_type(
        url="https://example.org/news/2026/archive-ai-project",
        root_url="https://example.org/",
        title="News: archive AI project",
        structured_text='{"@type":"NewsArticle"}',
    )
    assert decision.surface_type == "news_or_editorial"
    assert decision.is_item_level is False


def test_item_record_requires_combined_item_signals():
    decision = classify_surface_type(
        url="https://example.org/record/film-123456",
        root_url="https://example.org/",
        title="Film 123456",
        structured_text='{"identifier":"film-123456","@type":"CreativeWork"}',
    )
    assert decision.surface_type == "item_record"
    assert decision.is_item_level is True


def test_audiovisual_item_requires_item_and_media_evidence():
    decision = classify_surface_type(
        url="https://example.org/video/item-987654",
        root_url="https://example.org/",
        title="Interview 987654",
        structured_text=(
            '{"@type":"VideoObject","identifier":"987654",'
            '"contentUrl":"https://cdn.example.org/987654.mp4"}'
        ),
        media_urls=("https://cdn.example.org/987654.mp4",),
    )
    assert decision.surface_type == "audiovisual_item"
    assert decision.is_item_level is True
    assert decision.confidence == "high"


def test_embedded_video_on_homepage_does_not_turn_homepage_into_item():
    decision = classify_surface_type(
        url="https://example.org/",
        root_url="https://example.org/",
        title="Example Archive",
        media_urls=("https://youtube.com/embed/hero",),
    )
    assert decision.surface_type == "homepage"
    assert decision.is_item_level is False


def test_blocked_surface_is_separate_from_negative_classification():
    decision = classify_surface_type(
        url="https://example.org/item/123456",
        root_url="https://example.org/",
        fetch_status="blocked_by_robots",
    )
    assert decision.surface_type == "restricted_or_unavailable"
    assert decision.is_item_level is False


def test_ambiguous_page_stays_unknown():
    decision = classify_surface_type(
        url="https://example.org/project",
        root_url="https://example.org/",
        title="Digital project",
        text="A public project page.",
    )
    assert decision.surface_type == "unknown"
    assert decision.confidence == "low"
