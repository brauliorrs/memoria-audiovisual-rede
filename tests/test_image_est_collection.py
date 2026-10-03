import unittest

from memoria_audiovisual.image_est import (
    IMAGE_EST_SITEMAP_URL,
    collect_image_est_dataset,
    parse_image_est_sitemap,
)


class FakeResponse:
    def __init__(self, url, *, text="", status_code=200, error=None):
        self.requested_url = url
        self.final_url = url
        self.status_code = status_code
        self.content_type = "text/html"
        self.text = text
        self.error = error


def film_html(title="Film"):
    return f"""
    <html><body>
      <h1>{title}</h1>
      <dl>
        <dt>Année</dt><dd>1985</dd>
        <dt>Durée</dt><dd>00:03:18:00</dd>
        <dt>Format</dt><dd>Film 16 mm</dd>
        <dt>Son</dt><dd>Muet</dd>
        <dt>Fonds</dt><dd>Fonds test</dd>
      </dl>
    </body></html>
    """


def photo_html(title="Photo"):
    return f"""
    <html><body>
      <h1>{title}</h1>
      <dl>
        <dt>Année</dt><dd>1950</dd>
        <dt>Format</dt><dd>Négatif</dd>
        <dt>Fonds</dt><dd>Fonds photo</dd>
      </dl>
    </body></html>
    """


def sitemap_xml(extra=""):
    return f"""
    <urlset>
      <url><loc>https://www.image-est.fr/fiche-documentaire-film-a-1284-101-1-0.html</loc></url>
      <url><loc>https://www.image-est.fr/fiche-documentaire-film-b-1284-102-1-0.html</loc></url>
      <url><loc>https://www.image-est.fr/fiche-documentaire-photo-a-1284-201-2-0.html</loc></url>
      <url><loc>https://www.image-est.fr/fiche-documentaire-photo-b-1284-202-2-0.html</loc></url>
      <url><loc>https://www.image-est.fr/fiche-documentaire-film-c-1284-301-3-0.html</loc></url>
      <url><loc>https://www.image-est.fr/fiche-documentaire-film-d-1284-302-3-0.html</loc></url>
      {extra}
    </urlset>
    """


class ImageEstCollectionTests(unittest.TestCase):
    def test_sitemap_parser_groups_typed_records_without_guessing_ids(self):
        parsed = parse_image_est_sitemap(sitemap_xml())
        self.assertEqual(parsed["typed_counts"], {"1": 2, "2": 2, "3": 2})
        self.assertEqual(parsed["untyped_details"], [])
        self.assertEqual(parsed["duplicates"], [])
        self.assertEqual(parsed["detail_total"], 6)

    def test_collector_materializes_only_validated_audiovisual_types(self):
        calls = []

        def robots_loader(_session):
            return (
                True,
                "robots_evaluated_rfc9309",
                "User-agent: *\nAllow: /\n"
                f"Sitemap: {IMAGE_EST_SITEMAP_URL}\n",
            )

        def fetch_allowed(_session, url, _robots_text):
            calls.append(url)
            if url == IMAGE_EST_SITEMAP_URL:
                return FakeResponse(url, text=sitemap_xml(), status_code=200)
            if "-2-0.html" in url:
                return FakeResponse(url, text=photo_html(), status_code=200)
            return FakeResponse(url, text=film_html(), status_code=200)

        _institutions, summary, links, internal = collect_image_est_dataset(
            session=object(),
            robots_loader=robots_loader,
            fetch_allowed=fetch_allowed,
        )
        self.assertEqual(summary[0]["integrity_status"], "integro")
        self.assertEqual(len(links), 4)
        self.assertTrue(
            all(
                link["video_link"].endswith(("-1-0.html", "-3-0.html"))
                for link in links
            )
        )
        self.assertFalse(any("-2-0.html" in row["video_link"] for row in links))
        self.assertFalse(any("/js/" in url for url in calls))
        self.assertFalse(any("diazie" in url for url in calls))
        self.assertEqual(len(calls), 7)
        self.assertEqual(len(calls), len(set(calls)))
        audited_detail_urls = [
            row["internal_page"]
            for row in internal
            if "fiche-documentaire-" in row["internal_page"]
        ]
        self.assertEqual(
            len(audited_detail_urls),
            len(set(audited_detail_urls)),
        )
        type_rows = {
            row["internal_page"]: row["video_links_found"]
            for row in internal
            if "#type=" in row["internal_page"]
        }
        self.assertEqual(type_rows[f"{IMAGE_EST_SITEMAP_URL}#type=1"], 2)
        self.assertEqual(type_rows[f"{IMAGE_EST_SITEMAP_URL}#type=2"], 2)
        self.assertEqual(type_rows[f"{IMAGE_EST_SITEMAP_URL}#type=3"], 2)

    def test_new_type_code_fails_closed(self):
        extra = (
            "<url><loc>https://www.image-est.fr/"
            "fiche-documentaire-unknown-1284-401-4-0.html</loc></url>"
        )

        def robots_loader(_session):
            return True, "ok", "User-agent: *\nAllow: /\n"

        def fetch_allowed(_session, url, _robots_text):
            if url == IMAGE_EST_SITEMAP_URL:
                return FakeResponse(url, text=sitemap_xml(extra), status_code=200)
            if "-2-0.html" in url or "-4-0.html" in url:
                return FakeResponse(url, text=photo_html(), status_code=200)
            return FakeResponse(url, text=film_html(), status_code=200)

        _institutions, summary, _links, _internal = collect_image_est_dataset(
            session=object(),
            robots_loader=robots_loader,
            fetch_allowed=fetch_allowed,
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertIn("unexpected_type_codes=4", summary[0]["error"])

    def test_untyped_documentary_permalink_fails_closed(self):
        extra = (
            "<url><loc>https://www.image-est.fr/"
            "fiche-documentaire-untyped-1284-999.html</loc></url>"
        )

        def robots_loader(_session):
            return True, "ok", "User-agent: *\nAllow: /\n"

        def fetch_allowed(_session, url, _robots_text):
            if url == IMAGE_EST_SITEMAP_URL:
                return FakeResponse(url, text=sitemap_xml(extra), status_code=200)
            if "-2-0.html" in url:
                return FakeResponse(url, text=photo_html(), status_code=200)
            return FakeResponse(url, text=film_html(), status_code=200)

        _institutions, summary, _links, _internal = collect_image_est_dataset(
            session=object(),
            robots_loader=robots_loader,
            fetch_allowed=fetch_allowed,
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertIn("untyped_details=1", summary[0]["error"])

    def test_robots_failure_aborts_before_sitemap_fetch(self):
        calls = []

        def robots_loader(_session):
            return False, "robots_unreachable", ""

        def fetch_allowed(_session, url, _robots_text):
            calls.append(url)
            raise AssertionError("sitemap must not be fetched")

        _institutions, summary, links, _internal = collect_image_est_dataset(
            session=object(),
            robots_loader=robots_loader,
            fetch_allowed=fetch_allowed,
        )
        self.assertEqual(links, [])
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
