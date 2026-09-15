"""Readiness only: synthetic URLs, no independent pages or human labels."""
import json
from pathlib import Path

import pytest

from memoria_audiovisual.digital_infrastructure import surface_review_v23 as review


@pytest.fixture
def protocol():
    path = Path("data/digital_infrastructure/ai_experiments/m3_surface_type_independent_validation_protocol_v2_3_draft.json")
    return json.loads(path.read_text())


@pytest.fixture
def reports(protocol):
    return {
        entity["entity_id"]: {
            "root_url": entity["root_url"],
            "pages": [{
                "requested_url": f"https://example.org/{entity['entity_id']}/film/{i}",
                "url": f"https://example.org/{entity['entity_id']}/film/{i}",
                "snapshot_reference": f"raw/{entity['entity_id']}/{i}.json",
                "fetched_at": "2026-09-15T00:00:00Z",
                "media_urls": ["https://example.org/media.mp4"],
            } for i in range(8)],
        } for entity in protocol["entities"]
    }


def select(reports, protocol, urls=()):
    return review.select_review_units(reports, protocol=protocol, exclusion={"urls": urls})


@pytest.mark.parametrize(("url", "expected"), [
    ("HTTPS://EXAMPLE.ORG:443/A?a=1&b=2#x", "https://example.org/A?a=1&b=2"),
    ("http://EXAMPLE.ORG:80/A", "http://example.org/A"),
    ("https://EXAMPLE.ORG:8443/A", "https://example.org:8443/A"),
    ("https://[::1]:443/A", "https://[::1]/A"),
])
def test_url_identity(url, expected):
    assert review.url_identity(url) == expected


def test_no_over_normalization():
    urls = ["https://example.org/A?a=1&b=2", "https://example.org/a?a=1&b=2",
            "https://example.org/A?b=2&a=1", "https://example.org/A?a=2&b=2"]
    assert len({review.url_identity(url) for url in urls}) == 4


@pytest.mark.parametrize("url", ["/relative", "ftp://example.org/a", "https://u:p@example.org", "https://example.org:bad", "https://example.org/a b"])
def test_invalid_urls_rejected(url):
    with pytest.raises(ValueError):
        review.url_identity(url)


def test_order_caps_and_no_classification(reports, protocol, monkeypatch):
    def forbidden(**kwargs):
        pytest.fail("Selection must never call the classifier")
    monkeypatch.setattr(review, "classify_surface_type_candidate", forbidden)
    result = select(dict(reversed(list(reports.items()))), protocol)
    assert result["status"] == "sufficient"
    assert len(result["units"]) == 36
    assert [u["entity_id"] for u in result["units"]] == [e["entity_id"] for e in protocol["entities"] for _ in range(6)]
    assert len(result["audit"]) == 48
    assert sum(a["reason"] == "entity_cap" for a in result["audit"]) == 12


def test_requested_final_exclusions_and_global_duplicates(reports, protocol):
    a, b = [e["entity_id"] for e in protocol["entities"][:2]]
    pages = reports[a]["pages"]
    pages[0]["requested_url"] = "HTTPS://KNOWN.EXAMPLE:443/A#fragment"
    pages[1]["url"] = "https://known.example/B"
    reports[b]["pages"][0]["url"] = pages[2]["url"] + "#duplicate"
    result = select(reports, protocol, ["https://known.example/A", "https://known.example/B"])
    reasons = [r["reason"] for r in result["audit"]]
    assert reasons[:3] == ["known_url", "known_url", "selected"]
    assert reasons[8] == "duplicate"
    assert len(result["units"]) == 36


@pytest.mark.parametrize("missing", ["requested_url", "url", "snapshot_reference", "fetched_at"])
def test_missing_provenance_fails_closed(reports, protocol, missing):
    del reports[protocol["entities"][0]["entity_id"]]["pages"][0][missing]
    with pytest.raises(ValueError, match=missing):
        select(reports, protocol)


def test_report_integrity(reports, protocol):
    entity = protocol["entities"][0]["entity_id"]
    reports[entity]["root_url"] = "https://wrong.example/"
    with pytest.raises(ValueError, match="root"):
        select(reports, protocol)
    del reports[entity]
    with pytest.raises(ValueError, match="every registered entity"):
        select(reports, protocol)


def test_insufficient_never_predicts_or_releases_queue(reports, protocol, monkeypatch):
    for report in reports.values():
        report["pages"] = report["pages"][:3]
    monkeypatch.setattr(review, "classify_surface_type_candidate", lambda **_: pytest.fail("Insufficient sample classified"))
    queue, private = review.build_development_artifacts(reports, protocol=protocol, exclusion={"urls": []})
    assert queue["selection_status"] == "insufficient_sample"
    assert queue["units"] == private["units"] == []
    assert len(private["selection_audit"]) == 18


def test_entity_minimum_even_with_24_units(reports, protocol):
    for entity in protocol["entities"][4:]:
        reports[entity["entity_id"]]["pages"] = []
    result = select(reports, protocol)
    assert len(result["units"]) == 24
    assert result["status"] == "insufficient_sample"


def test_blinding_candidate_dispatch_and_failure_retention(reports, protocol):
    entity = protocol["entities"][0]["entity_id"]
    page = reports[entity]["pages"][0]
    page.update(fetch_status="request_error", collector_access_state="DO_NOT_LEAK",
                prediction_evidence=["DO_NOT_LEAK"], predicted_surface_type="DO_NOT_LEAK")
    queue, private = review.build_development_artifacts(reports, protocol=protocol, exclusion={"urls": []})
    assert len(queue["units"]) == len(private["units"]) == 36
    assert queue["candidate_version"] == "2.3.0-dev"
    assert queue["protocol_version"] == "2.3.0"
    assert queue["is_independent_validation_sample"] is False
    assert "DO_NOT_LEAK" not in json.dumps(queue)
    assert all(set(unit) == review.HUMAN_FIELDS for unit in queue["units"])
    assert private["units"][0]["predicted_access_state"] == "request_error"
    assert private["units"][1]["predicted_surface_type"] == "audiovisual_item"
    assert [u["review_unit_id"] for u in queue["units"]] == [u["review_unit_id"] for u in private["units"]]
    assert all(u["human_surface_type"] is None for u in queue["units"])


def test_version_and_blinding_contract_guards(reports, protocol):
    protocol["candidate_version"] = "2.2.0"
    with pytest.raises(ValueError, match="version"):
        review.build_development_artifacts(reports, protocol=protocol, exclusion={"urls": []})
    protocol["candidate_version"] = "2.3.0-dev"
    protocol["blinding"]["human_queue_allowed_fields"].append("collector_access_state")
    with pytest.raises(ValueError, match="contract"):
        review.build_development_artifacts(reports, protocol=protocol, exclusion={"urls": []})
