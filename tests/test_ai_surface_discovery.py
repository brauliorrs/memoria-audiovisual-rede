from pathlib import Path

from memoria_audiovisual.digital_infrastructure.ai_surface_discovery import (
    SurfaceDiscoveryPolicy,
    canonicalize_public_url,
    discover_public_surfaces,
    is_url_in_institutional_scope,
    materialize_surface_discovery,
)


class FakeResponse:
    def __init__(self, url, body, *, status_code=200, content_type="text/html"):
        self.url = url
        self.status_code = status_code
        self.ok = 200 <= status_code < 400
        self.content = body.encode("utf-8")
        self.encoding = "utf-8"
        self.headers = {"Content-Type": content_type}
        self.text = body


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url, **_kwargs):
        self.calls.append(url)
        response = self.responses.get(url)
        if response is None:
            return FakeResponse(url, "", status_code=404, content_type="text/plain")
        return response

    def close(self):
        return None


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
                    '<a href="https://data.ina.fr/traitements-ia">Traitements IA des archives audiovisuelles</a>'
                    "</body></html>"
                ),
            ),
            ai_page: FakeResponse(
                ai_page,
                (
                    '<html><head><meta name="description" content="Intelligence artificielle et archives audiovisuelles"></head>'
                    '<body>Intelligence artificielle pour la transcription et la segmentation des archives audiovisuelles.</body></html>'
                ),
            ),
            generic_page: FakeResponse(generic_page, "<html><body>Contact</body></html>"),
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


def test_binary_downloads_are_not_candidates():
    assert canonicalize_public_url("https://www.ina.fr/document.pdf") is None
    assert canonicalize_public_url("https://www.ina.fr/video.mp4") is None
