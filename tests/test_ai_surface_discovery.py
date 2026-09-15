import base64
import hashlib
import json
from pathlib import Path

import pytest
import requests

from memoria_audiovisual.digital_infrastructure import ai_surface_discovery as discovery
from memoria_audiovisual.digital_infrastructure.ai_surface_discovery import (
    SurfaceDiscoveryPolicy,
    canonicalize_public_url,
    discover_public_surfaces,
    is_url_in_institutional_scope,
    materialize_surface_discovery,
)


class FakeResponse:
    def __init__(
        self,
        url,
        body,
        *,
        status_code=200,
        content_type="text/html",
    ):
        self.url = url
        self.status_code = status_code
        self.ok = 200 <= status_code < 400
        self.content = body if isinstance(body, bytes) else body.encode("utf-8")
        self.encoding = "utf-8"
        self.headers = {"Content-Type": content_type}
        self.text = self.content.decode("utf-8", errors="replace")


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url, **_kwargs):
        self.calls.append(url)
        response = self.responses.get(url)
        if isinstance(response, Exception):
            raise response
        if response is None:
            return FakeResponse(url, "", status_code=404, content_type="text/plain")
        return response

    def close(self):
        return None


def _materialized_snapshot(output_dir: Path, report_path: Path, index: int = 0):
    materialized = json.loads(report_path.read_text(encoding="utf-8"))
    page = materialized["pages"][index]
    snapshot_path = output_dir / page["snapshot_reference"]
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    return materialized, page, snapshot


def test_public_url_normalization_and_scope():
    assert canonicalize_public_url("https://www.ina.fr/page?b=2&a=1#top") == (
        "https://www.ina.fr/page?a=1&b=2"
    )
    assert canonicalize_public_url("https://user:secret@www.ina.fr/") is None
    assert is_url_in_institutional_scope(
        "https://data.ina.fr/traitements-ia",
        "https://www.ina.fr/institut-national-audiovisuel",
    )
    assert not is_url_in_institutional_scope(
        "https://example.org/ai",
        "https://www.ina.fr/institut-national-audiovisuel",
    )


def test_surface_discovery_prioritizes_relevant_internal_subdomain(tmp_path):
    root = "https://www.ina.fr/"
    ai_page = "https://data.ina.fr/traitements-ia"
    generic_page = "https://www.ina.fr/contact"
    session = FakeSession(
        {
            "https://www.ina.fr/robots.txt": FakeResponse(
                "https://www.ina.fr/robots.txt",
                "User-agent: *\nAllow: /",
                content_type="text/plain",
            ),
            "https://data.ina.fr/robots.txt": FakeResponse(
                "https://data.ina.fr/robots.txt",
                "User-agent: *\nAllow: /",
                content_type="text/plain",
            ),
            root: FakeResponse(
                root,
                (
                    '<html><head><title>INA</title></head><body>'
                    '<a href="/contact">Contact</a>'
                    '<a href="https://data.ina.fr/traitements-ia">'
                    "Traitements IA des archives audiovisuelles</a>"
                    "</body></html>"
                ),
            ),
            ai_page: FakeResponse(
                ai_page,
                (
                    '<html><head><meta name="description" '
                    'content="Intelligence artificielle et archives audiovisuelles">'
                    "</head><body>Intelligence artificielle pour la transcription "
                    "et la segmentation des archives audiovisuelles.</body></html>"
                ),
            ),
            generic_page: FakeResponse(
                generic_page,
                "<html><body>Contact</body></html>",
            ),
        }
    )
    report = discover_public_surfaces(
        root,
        policy=SurfaceDiscoveryPolicy(max_depth=1, max_pages=2),
        session=session,
    )
    assert report.fetched_pages == 2
    assert [page.url for page in report.pages] == [root, ai_page]
    assert "Intelligence artificielle" in report.pages[1].text
    assert [capture.requested_url for capture in report.captures] == [root, ai_page]
    assert [capture.final_url for capture in report.captures] == [root, ai_page]

    report_path, classifier_path = materialize_surface_discovery(
        report,
        output_dir=tmp_path,
        run_id="run-1",
        entity_id="ina",
    )
    assert report_path.exists()
    assert classifier_path.exists()
    classifier_text = classifier_path.read_text(encoding="utf-8")
    assert ai_page in classifier_text
    assert "transcription" in classifier_text

    _materialized, page, snapshot = _materialized_snapshot(tmp_path, report_path)
    assert page["requested_url"] == root
    assert page["final_url"] == root
    assert page["url"] == root
    assert snapshot["requested_url"] == root
    assert snapshot["final_url"] == root
    assert snapshot["fetch_status"] == "fetched"
    body = base64.b64decode(snapshot["response"]["body_base64"])
    assert hashlib.sha256(body).hexdigest() == snapshot["response"]["captured_sha256"]


def test_binary_downloads_are_not_candidates():
    assert canonicalize_public_url("https://www.ina.fr/document.pdf") is None
    assert canonicalize_public_url("https://www.ina.fr/video.mp4") is None


def test_redirect_outside_scope_preserves_requested_final_and_response(tmp_path):
    root = "https://archive.example.org/"
    outside = "https://cdn.other.example/item?id=2&id=1"
    body = b"redirected evidence"
    session = FakeSession(
        {
            "https://archive.example.org/robots.txt": FakeResponse(
                "https://archive.example.org/robots.txt",
                "User-agent: *\nAllow: /",
                content_type="text/plain",
            ),
            root: FakeResponse(
                outside,
                body,
                status_code=200,
                content_type="text/plain",
            ),
        }
    )

    report = discover_public_surfaces(
        root,
        policy=SurfaceDiscoveryPolicy(max_pages=1),
        session=session,
    )
    assert report.pages[0].fetch_status == "redirect_outside_scope"
    assert report.captures[0].requested_url == root
    assert report.captures[0].final_url == outside

    report_path, _ = materialize_surface_discovery(
        report,
        output_dir=tmp_path,
        run_id="redirect",
        entity_id="synthetic",
    )
    _materialized, page, snapshot = _materialized_snapshot(tmp_path, report_path)
    assert page["requested_url"] == root
    assert page["url"] == outside
    assert page["final_url"] == outside
    assert base64.b64decode(snapshot["response"]["body_base64"]) == body


def test_http_error_preserves_response_body(tmp_path):
    root = "https://archive.example.org/"
    body = b"server failure evidence"
    session = FakeSession(
        {
            "https://archive.example.org/robots.txt": FakeResponse(
                "https://archive.example.org/robots.txt",
                "",
                status_code=404,
                content_type="text/plain",
            ),
            root: FakeResponse(
                root,
                body,
                status_code=500,
                content_type="text/plain",
            ),
        }
    )

    report = discover_public_surfaces(
        root,
        policy=SurfaceDiscoveryPolicy(max_pages=1),
        session=session,
    )
    assert report.pages[0].fetch_status == "http_error"

    report_path, _ = materialize_surface_discovery(
        report,
        output_dir=tmp_path,
        run_id="http500",
        entity_id="synthetic",
    )
    _materialized, _page, snapshot = _materialized_snapshot(tmp_path, report_path)
    assert snapshot["response"]["status_code"] == 500
    assert base64.b64decode(snapshot["response"]["body_base64"]) == body


def test_request_error_is_a_durable_observation(tmp_path):
    root = "https://archive.example.org/"
    session = FakeSession(
        {
            "https://archive.example.org/robots.txt": FakeResponse(
                "https://archive.example.org/robots.txt",
                "",
                status_code=404,
                content_type="text/plain",
            ),
            root: requests.ConnectionError("synthetic connection failure"),
        }
    )

    report = discover_public_surfaces(
        root,
        policy=SurfaceDiscoveryPolicy(max_pages=1),
        session=session,
    )
    assert report.pages[0].fetch_status == "request_error"

    report_path, _ = materialize_surface_discovery(
        report,
        output_dir=tmp_path,
        run_id="request-error",
        entity_id="synthetic",
    )
    _materialized, page, snapshot = _materialized_snapshot(tmp_path, report_path)
    assert page["requested_url"] == root
    assert page["final_url"] is None
    assert page["url"] == root
    assert snapshot["response"] is None
    assert snapshot["error"]["type"] == "ConnectionError"
    assert "synthetic connection failure" in snapshot["error"]["message"]


def test_robots_block_is_a_durable_observation_without_fetching_target(tmp_path):
    root = "https://archive.example.org/"
    robots_body = "User-agent: *\nDisallow: /"
    session = FakeSession(
        {
            "https://archive.example.org/robots.txt": FakeResponse(
                "https://archive.example.org/robots.txt",
                robots_body,
                content_type="text/plain",
            )
        }
    )

    report = discover_public_surfaces(
        root,
        policy=SurfaceDiscoveryPolicy(max_pages=1),
        session=session,
    )
    assert report.pages[0].fetch_status == "blocked_by_robots"
    assert session.calls == ["https://archive.example.org/robots.txt"]

    report_path, _ = materialize_surface_discovery(
        report,
        output_dir=tmp_path,
        run_id="robots",
        entity_id="synthetic",
    )
    _materialized, page, snapshot = _materialized_snapshot(tmp_path, report_path)
    assert page["requested_url"] == root
    assert page["final_url"] is None
    assert snapshot["robots"]["allowed"] is False
    assert snapshot["robots"]["reason"] == "robots_rule_deny"
    assert base64.b64decode(snapshot["robots"]["response"]["body_base64"]) == (
        robots_body.encode("utf-8")
    )


def test_materialization_refuses_overwrite(tmp_path):
    root = "https://archive.example.org/"
    session = FakeSession(
        {
            "https://archive.example.org/robots.txt": FakeResponse(
                "https://archive.example.org/robots.txt",
                "",
                status_code=404,
                content_type="text/plain",
            ),
            root: FakeResponse(root, "ok", content_type="text/plain"),
        }
    )
    report = discover_public_surfaces(
        root,
        policy=SurfaceDiscoveryPolicy(max_pages=1),
        session=session,
    )
    materialize_surface_discovery(
        report,
        output_dir=tmp_path,
        run_id="immutable",
        entity_id="synthetic",
    )

    with pytest.raises(FileExistsError, match="sobrescrita recusada"):
        materialize_surface_discovery(
            report,
            output_dir=tmp_path,
            run_id="immutable",
            entity_id="synthetic",
        )


def test_persistence_failure_aborts_before_report_or_classifier(tmp_path, monkeypatch):
    root = "https://archive.example.org/"
    session = FakeSession(
        {
            "https://archive.example.org/robots.txt": FakeResponse(
                "https://archive.example.org/robots.txt",
                "",
                status_code=404,
                content_type="text/plain",
            ),
            root: FakeResponse(root, "ok", content_type="text/plain"),
        }
    )
    report = discover_public_surfaces(
        root,
        policy=SurfaceDiscoveryPolicy(max_pages=1),
        session=session,
    )

    class BrokenStore:
        def __init__(self, _root):
            pass

        def preserve(self, _value):
            raise OSError("synthetic persistence failure")

    monkeypatch.setattr(discovery, "RawArtifactStore", BrokenStore)
    with pytest.raises(OSError, match="synthetic persistence failure"):
        materialize_surface_discovery(
            report,
            output_dir=tmp_path,
            run_id="broken",
            entity_id="synthetic",
        )

    root_path = tmp_path / "_ai_surface_discovery" / "broken" / "synthetic"
    assert not (root_path / "surface_discovery_report.json").exists()
    assert not (root_path / "surface_classifier_text.jsonl").exists()
