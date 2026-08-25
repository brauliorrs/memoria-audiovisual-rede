import json
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.surface_typing import (
    SURFACE_TYPES,
    SURFACE_TYPING_PROTOCOL_VERSION,
    classify_surface_type,
)

CALIBRATION_FIXTURE = Path("tests/fixtures/m3_surface_typing_calibration_v1.json")


def test_vocabulary_keeps_institutional_and_archive_landing_pages_separate():
    assert "institutional_landing_page" in SURFACE_TYPES
    assert "archive_landing_page" in SURFACE_TYPES
    assert SURFACE_TYPING_PROTOCOL_VERSION == "2.0.0"


def test_configured_non_root_entry_can_be_platform_homepage():
    decision = classify_surface_type(
        url="https://www.ina.fr/institut-national-audiovisuel",
        root_url="https://www.ina.fr/institut-national-audiovisuel",
        title="Institut national de l'audiovisuel",
        text="L'INA conserve et valorise le patrimoine audiovisuel.",
    )
    assert decision.surface_type == "homepage"
    assert decision.is_item_level is False


def test_ecpad_general_archives_page_is_archive_landing_page():
    decision = classify_surface_type(
        url="https://archives.ecpad.fr/archives/archives",
        root_url="https://archives.ecpad.fr/archives/archives",
        title="Archives - ECPAD",
        text="Explorer les archives et les collections.",
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


def test_thematic_research_route_remains_search_when_collector_redirects():
    decision = classify_surface_type(
        url="https://example.org/archives/aide-a-la-recherche/premiere-guerre-mondiale",
        root_url="https://example.org/archives/consulter-les-archives-en-ligne",
        fetch_status="redirect_outside_scope",
    )
    assert decision.surface_type == "search_or_index"
    assert decision.access_state == "redirect_outside_scope"


def test_news_article_is_editorial_not_item():
    decision = classify_surface_type(
        url="https://example.org/news/2026/archive-ai-project",
        root_url="https://example.org/",
        title="News: archive AI project",
        structured_text='{"@type":"NewsArticle"}',
    )
    assert decision.surface_type == "news_or_editorial"
    assert decision.is_item_level is False


def test_about_partner_archive_page_is_informational_editorial():
    decision = classify_surface_type(
        url="https://example.org/about/partner-archives",
        root_url="https://example.org/search",
        title="Partner Archives",
    )
    assert decision.surface_type == "news_or_editorial"
    assert decision.is_item_level is False


def test_item_record_requires_combined_item_signals_without_forcing_audiovisual():
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


def test_specific_video_route_can_remain_item_when_playback_is_geo_restricted():
    decision = classify_surface_type(
        url="https://example.org/video/0480337c-e444-5b53-89e9-da6da693da47",
        root_url="https://example.org/search",
        title="Searching",
        text=(
            "Playback Denied: Location; PLAYER_ERR_GEO_RESTRICTED; "
            "Video is unavailable from your current location."
        ),
    )
    assert decision.surface_type == "audiovisual_item"
    assert decision.is_item_level is True
    assert decision.access_state == "geo_restricted"


def test_embedded_video_on_homepage_does_not_turn_homepage_into_item():
    decision = classify_surface_type(
        url="https://example.org/",
        root_url="https://example.org/",
        title="Example Archive",
        media_urls=("https://youtube.com/embed/hero",),
    )
    assert decision.surface_type == "homepage"
    assert decision.is_item_level is False


def test_collector_block_does_not_replace_recoverable_surface_role():
    decision = classify_surface_type(
        url="https://example.org/",
        root_url="https://example.org/",
        fetch_status="blocked_by_robots",
    )
    assert decision.surface_type == "homepage"
    assert decision.is_item_level is False
    assert decision.access_state == "collector_blocked"


def test_nested_archive_taxonomy_can_represent_search_or_index():
    decision = classify_surface_type(
        url="https://example.org/collections-audiovisuelles/archives-emblematiques",
        root_url="https://example.org/institut",
        title="Archives emblématiques",
    )
    assert decision.surface_type == "search_or_index"
    assert decision.is_item_level is False


def test_single_curated_collection_entry_remains_archive_landing_page():
    decision = classify_surface_type(
        url="https://example.org/curated-collections",
        root_url="https://example.org/search",
        title="Curated Collections",
    )
    assert decision.surface_type == "archive_landing_page"
    assert decision.is_item_level is False


def test_press_vocabulary_alone_does_not_force_editorial_role():
    decision = classify_surface_type(
        url="https://example.org/institut/collections-audiovisuelles/presse-filmee-et-cinema",
        root_url="https://example.org/institut",
        title="Presse filmée et cinema",
    )
    assert decision.surface_type == "institutional_landing_page"
    assert decision.is_item_level is False


def test_unrecoverable_request_error_uses_restricted_class():
    decision = classify_surface_type(
        url="https://example.org/project",
        root_url="https://example.org/",
        fetch_status="request_error",
    )
    assert decision.surface_type == "restricted_or_unavailable"
    assert decision.access_state == "request_error"


def test_ambiguous_page_stays_unknown():
    decision = classify_surface_type(
        url="https://example.org/project",
        root_url="https://example.org/",
        title="Digital project",
        text="A public project page.",
    )
    assert decision.surface_type == "unknown"
    assert decision.confidence == "low"


def test_m3_human_calibration_set_is_a_regression_fixture_not_validation_metric():
    fixture = json.loads(CALIBRATION_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["is_independent_validation_sample"] is False
    assert fixture["scientific_role"] == "development_and_regression_calibration_only"
    assert fixture["units_total"] == 17

    mismatches = []
    for unit in fixture["units"]:
        decision = classify_surface_type(
            url=unit["url"],
            root_url=unit["root_url"],
            title=unit.get("title"),
            text=unit.get("text", ""),
            metadata_text=unit.get("metadata_text", ""),
            structured_text=unit.get("structured_text", ""),
            media_urls=tuple(unit.get("media_urls", [])),
            fetch_status=unit.get("fetch_status", "fetched"),
        )
        observed = (decision.surface_type, decision.is_item_level, decision.access_state)
        expected = (
            unit["expected_surface_type"],
            unit["expected_item_level"],
            unit["expected_access_state"],
        )
        if observed != expected:
            mismatches.append((unit["review_unit_id"], observed, expected, decision.evidence))

    assert mismatches == []
