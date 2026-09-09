import json
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.surface_typing_v23_candidate import (
    SURFACE_TYPING_CANDIDATE_VERSION,
    classify_surface_type_candidate,
)

CALIBRATION_FIXTURE = Path("tests/fixtures/m3_surface_typing_calibration_v1.json")
AI_EXPERIMENTS = Path("data/digital_infrastructure/ai_experiments")


def _review_paths(version: str):
    return (
        AI_EXPERIMENTS / f"m3_surface_type_independent_human_review_{version}.json",
        AI_EXPERIMENTS / f"m3_surface_type_independent_review_queue_{version}.json",
        AI_EXPERIMENTS / f"m3_surface_type_independent_sources_{version}",
    )


def _load_review_cases(version: str):
    review_path, queue_path, sources_path = _review_paths(version)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    queue_by_id = {unit["review_unit_id"]: unit for unit in queue["units"]}

    source_pages: dict[str, dict[str, dict[str, object]]] = {}
    for entity_id in {unit["entity_id"] for unit in review["reviewed_units"]}:
        report_path = sources_path / f"{entity_id}_surface_discovery_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        source_pages[entity_id] = {
            str(page.get("url") or ""): page for page in report.get("pages", [])
        }

    cases = []
    for human in review["reviewed_units"]:
        queue_unit = queue_by_id[human["review_unit_id"]]
        page = source_pages.get(human["entity_id"], {}).get(human["page_url"], {})
        media_urls = page.get("media_urls", queue_unit.get("media_urls", []))
        if not isinstance(media_urls, (list, tuple)):
            media_urls = []
        decision = classify_surface_type_candidate(
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
        cases.append((human, decision))
    return review, cases


def test_candidate_version_is_explicitly_development_only():
    assert SURFACE_TYPING_CANDIDATE_VERSION == "2.3.0-dev"


def test_trailing_slash_film_detail_can_be_audiovisual_without_direct_media():
    decision = classify_surface_type_candidate(
        url="https://example.org/henri/film/122080-the-skywalk-is-gone-2002/",
        root_url="https://example.org/henri/",
        title="The Skywalk Is Gone (2002)",
    )
    assert decision.surface_type == "audiovisual_item"
    assert decision.is_item_level is True


def test_fiche_query_value_can_declare_audiovisual_type():
    decision = classify_surface_type_candidate(
        url="https://example.org/digital/Ficha.aspx?obraid=13015&type=Video",
        root_url="https://example.org/digital/video.aspx",
        title="Ficha",
        media_urls=("https://player.example.org/13015",),
    )
    assert decision.surface_type == "audiovisual_item"
    assert decision.is_item_level is True


def test_clip_detail_with_direct_media_is_audiovisual_item():
    decision = classify_surface_type_candidate(
        url="https://example.org/en/clips/6782_family-market",
        root_url="https://example.org/en/archive",
        title="Family market",
        media_urls=("https://cdn.example.org/6782.mp4",),
    )
    assert decision.surface_type == "audiovisual_item"
    assert decision.is_item_level is True


def test_non_root_observation_archive_is_not_automatically_homepage():
    decision = classify_surface_type_candidate(
        url="https://example.org/en/archive",
        root_url="https://example.org/en/archive",
        title="Archive",
    )
    assert decision.surface_type == "search_or_index"
    assert decision.is_item_level is False


def test_author_filtered_archive_is_search_index():
    decision = classify_surface_type_candidate(
        url="https://example.org/en/archive/?authors=Carretta%2C+Giacomo",
        root_url="https://example.org/en/archive",
        title="Archive",
    )
    assert decision.surface_type == "search_or_index"
    assert decision.is_item_level is False


def test_multilingual_collection_route_can_be_archive_landing_page():
    decision = classify_surface_type_candidate(
        url="https://example.org/Colecoes/Filme-e-Video.aspx",
        root_url="https://example.org/digital/video.aspx",
        title="Filme e Vídeo",
    )
    assert decision.surface_type == "archive_landing_page"
    assert decision.is_item_level is False


def test_configured_institutional_entry_without_index_signals_keeps_v22_semantics():
    decision = classify_surface_type_candidate(
        url="https://example.org/institut-national-audiovisuel",
        root_url="https://example.org/institut-national-audiovisuel",
        title="Institut national de l'audiovisuel",
        text="Conserve et valorise le patrimoine audiovisuel.",
    )
    assert decision.surface_type == "homepage"
    assert decision.is_item_level is False


def test_editorial_page_with_embedded_media_is_not_upgraded_without_av_detail_route():
    decision = classify_surface_type_candidate(
        url="https://example.org/news/archive-project",
        root_url="https://example.org/archive",
        title="Archive project news",
        structured_text='{"@type":"NewsArticle"}',
        media_urls=("https://cdn.example.org/news-video.mp4",),
    )
    assert decision.surface_type == "news_or_editorial"
    assert decision.is_item_level is False


def test_protocol_20_calibration_fixture_remains_exact_regression():
    fixture = json.loads(CALIBRATION_FIXTURE.read_text(encoding="utf-8"))
    mismatches = []
    for unit in fixture["units"]:
        decision = classify_surface_type_candidate(
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


def test_val003_development_regression_remains_exact():
    review, cases = _load_review_cases("v2")
    assert review["reviewed_units_total"] == 33
    mismatches = []
    for human, decision in cases:
        observed = (decision.surface_type, decision.is_item_level, decision.access_state)
        expected = (
            human["human_surface_type"],
            human["human_is_item_level"],
            human["human_access_state"],
        )
        if observed != expected:
            mismatches.append((human["review_unit_id"], observed, expected, decision.evidence))
    assert mismatches == []


def test_val005_is_development_only_and_keeps_safe_binary_floor():
    review, cases = _load_review_cases("v2_1")
    assert review["reviewed_units_total"] == 36
    tp = tn = fp = fn = 0
    for human, decision in cases:
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
    assert fp == 0
    assert tn == 22
    assert tp >= 10
    assert fn <= 4


def test_val007_is_development_only_and_candidate_recovers_generic_failure_families():
    review, cases = _load_review_cases("v2_2")
    assert review["reviewed_units_total"] == 31
    assert review["review_status"] == "completed"

    exact = 0
    tp = tn = fp = fn = 0
    class_support = {"archive_landing_page": 0, "search_or_index": 0, "audiovisual_item": 0}
    class_correct = {"archive_landing_page": 0, "search_or_index": 0, "audiovisual_item": 0}

    for human, decision in cases:
        if decision.surface_type == human["human_surface_type"]:
            exact += 1
        if human["human_surface_type"] in class_support:
            class_support[human["human_surface_type"]] += 1
            if decision.surface_type == human["human_surface_type"]:
                class_correct[human["human_surface_type"]] += 1

        human_item = human["human_is_item_level"]
        if human_item is None:
            continue
        predicted_item = decision.is_item_level
        if human_item is True and predicted_item:
            tp += 1
        elif human_item is False and not predicted_item:
            tn += 1
        elif human_item is False and predicted_item:
            fp += 1
        else:
            fn += 1

    recalls = {
        label: class_correct[label] / class_support[label]
        for label in class_support
    }

    # Development gates only. Passing these does not validate 2.3.0.
    assert exact >= 24
    assert tp >= 13
    assert tn == 16
    assert fp == 0
    assert fn <= 1
    assert recalls["archive_landing_page"] >= 0.50
    assert recalls["search_or_index"] >= 0.70
    assert recalls["audiovisual_item"] >= 0.90
