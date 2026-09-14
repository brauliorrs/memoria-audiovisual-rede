import json
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.surface_typing import (
    SURFACE_TYPES,
    SURFACE_TYPING_PROTOCOL_VERSION,
    classify_surface_type,
)

CALIBRATION_FIXTURE = Path("tests/fixtures/m3_surface_typing_calibration_v1.json")
POST_VALIDATION_REVIEW = Path(
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_independent_human_review_v2.json"
)
POST_VALIDATION_QUEUE = Path(
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_independent_review_queue_v2.json"
)
POST_VALIDATION_SOURCES = Path(
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_independent_sources_v2"
)
POST_VALIDATION_V21_REVIEW = Path(
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_independent_human_review_v2_1.json"
)
POST_VALIDATION_V21_QUEUE = Path(
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_independent_review_queue_v2_1.json"
)
POST_VALIDATION_V21_SOURCES = Path(
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_independent_sources_v2_1"
)


def test_vocabulary_keeps_institutional_and_archive_landing_pages_separate():
    assert "institutional_landing_page" in SURFACE_TYPES
    assert "archive_landing_page" in SURFACE_TYPES
    assert SURFACE_TYPING_PROTOCOL_VERSION == "2.2.0"


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


def test_catalogue_root_is_search_index_but_specific_catalogue_item_can_be_av_item():
    root_url = "https://www.cinearchives.org/catalogue-1104-0-0-0.html"
    root = classify_surface_type(
        url=root_url,
        root_url=root_url,
        title="Catalogue complet - plus de 900 films en ligne | Ciné-Archives",
    )
    item = classify_surface_type(
        url=(
            "https://www.cinearchives.org/"
            "catalogue-22-extraits-sur-lenine-1104-97-1-1.html"
        ),
        root_url=root_url,
        title="22 EXTRAITS SUR LÉNINE",
        media_urls=("https://example.org/embed/film",),
    )
    assert root.surface_type == "search_or_index"
    assert root.is_item_level is False
    assert item.surface_type == "audiovisual_item"
    assert item.is_item_level is True


def test_blocked_ajax_filter_endpoint_preserves_search_semantics():
    decision = classify_surface_type(
        url="https://www.cinearchives.org/js/ajax/diaPlugins/1104/ajax/add/kwtheme/1438",
        root_url="https://www.cinearchives.org/catalogue-1104-0-0-0.html",
        fetch_status="blocked_by_robots",
    )
    assert decision.surface_type == "search_or_index"
    assert decision.is_item_level is False
    assert decision.access_state == "collector_blocked"


def test_fonds_and_archive_film_browse_routes_are_search_indexes():
    fonds = classify_surface_type(
        url="https://cinememoire.net/archives-cinememoire-ligne/coumes",
        root_url="https://cinememoire.net/recherche-simple",
        title="Fonds Coumes",
    )
    thematic = classify_surface_type(
        url=(
            "https://cinememoire.net/archives-cinememoire-ligne/"
            "films-darchives-des-anciennes-colonies"
        ),
        root_url="https://cinememoire.net/recherche-simple",
        title="Anciennes colonies françaises",
    )
    assert fonds.surface_type == "search_or_index"
    assert thematic.surface_type == "search_or_index"


def test_repeated_archive_context_does_not_suppress_strong_fiche_film_item():
    decision = classify_surface_type(
        url=(
            "https://cinememoire.net/archives-cinememoire-ligne/"
            "archives-cinememoire-ligne/120-fiche-film/"
            "276-film-entomologiste-araignee"
        ),
        root_url="https://cinememoire.net/recherche-simple",
        title="Film entomologiste : araignées",
        media_urls=("https://cinememoire.net/streaming/example.mp4",),
    )
    assert decision.surface_type == "audiovisual_item"
    assert decision.is_item_level is True


def test_access_pro_route_is_restricted_surface_even_when_page_is_accessible():
    decision = classify_surface_type(
        url="https://cinememoire.net/acces-pro",
        root_url="https://cinememoire.net/recherche-simple",
        title="Espace Perso",
        fetch_status="fetched",
    )
    assert decision.surface_type == "restricted_or_unavailable"
    assert decision.is_item_level is False
    assert decision.access_state == "accessible"


def test_facet_query_dominates_year_ids_on_eye_film_database():
    root_url = (
        "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/all/all"
        "?f%5B0%5D=field_cm_media_filter%3Awith+film+fragment"
    )
    urls = (
        root_url,
        (
            "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/all/1896"
            "?f%5B0%5D=field_cm_media_filter%3Awith+film+fragment"
        ),
        (
            "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/all/"
            "1896%2B1897%2B1898%2B1899"
            "?f%5B0%5D=field_cm_media_filter%3Awith+film+fragment"
        ),
    )
    for url in urls:
        decision = classify_surface_type(
            url=url,
            root_url=root_url,
            title="Dutch film history | DEV EYE Filmdatabase",
        )
        assert decision.surface_type == "search_or_index"
        assert decision.is_item_level is False


def test_video_frame_metadata_can_confirm_audiovisual_detail_without_media_url():
    decision = classify_surface_type(
        url=(
            "https://patrimonio.archivioluce.com/luce-web/detail/IL5000052570/2/"
            "l-esercito-americano-italia-durante-prima-guerra-mondiale-"
            "111-h-1228.html?startPage=0"
        ),
        root_url="https://patrimonio.archivioluce.com/luce-web/search/result.html?query=",
        title="L'esercito americano in Italia durante la prima guerra mondiale",
        metadata_text=(
            "og:image: http://image.archivioluce.com/dm_0/IL/"
            "video_frames/high/mpegRW/RW54701.jpg"
        ),
    )
    assert decision.surface_type == "audiovisual_item"
    assert decision.is_item_level is True



def test_explicit_av_detail_route_with_trailer_title_can_be_item_without_media_url():
    decision = classify_surface_type(
        url="https://example.org/video/becoming-kim-2026",
        root_url="https://example.org/videos",
        title="Becoming Kim (2026) - Trailer",
        text="Becoming Kim (2026) - Trailer. Duration: 02:04 min.",
        media_urls=(),
    )
    assert decision.surface_type == "audiovisual_item"
    assert decision.is_item_level is True
    assert "path:explicit-audiovisual-detail" in decision.evidence


def test_explicit_av_route_without_item_marker_remains_conservative():
    decision = classify_surface_type(
        url="https://example.org/video/about",
        root_url="https://example.org/videos",
        title="About our video programme",
        media_urls=(),
    )
    assert decision.is_item_level is False


def test_strong_listing_signals_can_identify_search_index_without_search_path():
    text = (
        "Advanced search. Filter results. 6814 videos. "
        "Page 1 Page 2 Page 3 More results."
    )
    decision = classify_surface_type(
        url="https://example.org/videos",
        root_url="https://example.org/videos",
        title="Videos",
        text=text,
    )
    assert decision.surface_type == "search_or_index"
    assert decision.is_item_level is False


def test_schema_itemlist_can_identify_browse_surface():
    decision = classify_surface_type(
        url="https://example.org/watch",
        root_url="https://example.org/watch",
        title="Watch online",
        structured_text='{"@type":"ItemList","itemListElement":[]}',
    )
    assert decision.surface_type == "search_or_index"
    assert decision.is_item_level is False


def test_research_word_alone_does_not_mean_search_index():
    decision = classify_surface_type(
        url="https://example.org/research/",
        root_url="https://example.org/collections/",
        title="Research",
        text="Our researchers work with audiovisual heritage collections.",
    )
    assert decision.surface_type != "search_or_index"


def test_ajax_theme_or_format_endpoint_preserves_index_semantics():
    for url in (
        "https://example.org/js/ajax/plugins/905/ajax/add/mots_cles_theme/4518",
        "https://example.org/js/ajax/plugins/905/ajax/add/format_origine_id/4",
    ):
        decision = classify_surface_type(
            url=url,
            root_url="https://example.org/exploration",
            fetch_status="blocked_by_robots",
        )
        assert decision.surface_type == "search_or_index"
        assert decision.is_item_level is False
        assert decision.access_state == "collector_blocked"


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


def test_completed_independent_v2_sample_is_only_post_validation_development_regression():
    """The former independent sample may be reused only as development evidence now."""
    review = json.loads(POST_VALIDATION_REVIEW.read_text(encoding="utf-8"))
    queue = json.loads(POST_VALIDATION_QUEUE.read_text(encoding="utf-8"))

    assert review["review_status"] == "completed"
    assert review["reviewed_units_total"] == 33
    assert review["model_prediction_blinded"] is True
    assert queue["model_prediction_blinded"] is True

    queue_by_id = {unit["review_unit_id"]: unit for unit in queue["units"]}
    source_pages: dict[str, dict[str, dict[str, object]]] = {}
    entities = {unit["entity_id"] for unit in review["reviewed_units"]}
    for entity_id in entities:
        report_path = POST_VALIDATION_SOURCES / f"{entity_id}_surface_discovery_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        source_pages[entity_id] = {
            str(page.get("url") or ""): page for page in report.get("pages", [])
        }

    mismatches = []
    for human in review["reviewed_units"]:
        queue_unit = queue_by_id[human["review_unit_id"]]
        page = source_pages.get(human["entity_id"], {}).get(human["page_url"], {})
        media_urls = page.get("media_urls", queue_unit.get("media_urls", []))
        if not isinstance(media_urls, (list, tuple)):
            media_urls = []

        decision = classify_surface_type(
            url=human["page_url"],
            root_url=queue_unit["root_url"],
            title=page.get("title", queue_unit.get("title")),
            text=str(page.get("text") or ""),
            metadata_text=str(page.get("metadata_text") or ""),
            structured_text=str(page.get("structured_text") or ""),
            media_urls=tuple(str(value) for value in media_urls),
            fetch_status=str(
                page.get("fetch_status")
                or queue_unit.get("fetch_status")
                or "fetched"
            ),
        )
        observed = (decision.surface_type, decision.is_item_level, decision.access_state)
        expected = (
            human["human_surface_type"],
            human["human_is_item_level"],
            human["human_access_state"],
        )
        if observed != expected:
            mismatches.append(
                (
                    human["review_unit_id"],
                    observed,
                    expected,
                    decision.evidence,
                    decision.access_evidence,
                )
            )

    assert mismatches == []



def test_completed_independent_v21_sample_is_development_only_and_improves_safe_item_recall():
    """VAL-005 becomes development evidence only after its frozen evaluation is closed."""
    review = json.loads(POST_VALIDATION_V21_REVIEW.read_text(encoding="utf-8"))
    queue = json.loads(POST_VALIDATION_V21_QUEUE.read_text(encoding="utf-8"))

    assert review["review_status"] == "completed"
    assert review["reviewed_units_total"] == 36
    assert review["model_prediction_blinded"] is True
    assert queue["model_prediction_blinded"] is True

    queue_by_id = {unit["review_unit_id"]: unit for unit in queue["units"]}
    source_pages: dict[str, dict[str, dict[str, object]]] = {}
    entities = {unit["entity_id"] for unit in review["reviewed_units"]}
    for entity_id in entities:
        report_path = POST_VALIDATION_V21_SOURCES / f"{entity_id}_surface_discovery_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        source_pages[entity_id] = {
            str(page.get("url") or ""): page for page in report.get("pages", [])
        }

    tp = tn = fp = fn = 0
    dff_item_mismatches = []
    for human in review["reviewed_units"]:
        queue_unit = queue_by_id[human["review_unit_id"]]
        page = source_pages.get(human["entity_id"], {}).get(human["page_url"], {})
        media_urls = page.get("media_urls", queue_unit.get("media_urls", []))
        if not isinstance(media_urls, (list, tuple)):
            media_urls = []

        decision = classify_surface_type(
            url=human["page_url"],
            root_url=queue_unit["root_url"],
            title=page.get("title", queue_unit.get("title")),
            text=str(page.get("text") or ""),
            metadata_text=str(page.get("metadata_text") or ""),
            structured_text=str(page.get("structured_text") or ""),
            media_urls=tuple(str(value) for value in media_urls),
            fetch_status=str(
                page.get("fetch_status")
                or queue_unit.get("fetch_status")
                or "fetched"
            ),
        )

        expected_item = human["human_is_item_level"] is True
        predicted_item = decision.is_item_level
        if expected_item and predicted_item:
            tp += 1
        elif not expected_item and not predicted_item:
            tn += 1
        elif not expected_item and predicted_item:
            fp += 1
        else:
            fn += 1

        if (
            human["entity_id"] == "dff"
            and human["human_surface_type"] == "audiovisual_item"
            and decision.surface_type != "audiovisual_item"
        ):
            dff_item_mismatches.append(
                (human["review_unit_id"], decision.surface_type, decision.evidence)
            )

    # These are development/regression constraints, not independent performance claims.
    assert dff_item_mismatches == []
    assert fp == 0
    assert tn == 22
    assert tp >= 10
    assert fn <= 4
