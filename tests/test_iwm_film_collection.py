import unittest

from memoria_audiovisual.analysis import infer_video_theme
from memoria_audiovisual.iwm_film import (
    collect_iwm_film_dataset,
    parse_iwm_detail_page,
    parse_iwm_record_sitemap,
    parse_iwm_sitemap_index,
)
from memoria_audiovisual.iwm_film_probe import ProbeResponse


BASE = "https://film.iwmcollections.org.uk"
INDEX_URL = f"{BASE}/instance/sitemaps/sitemap-index.xml"
PART_1 = f"{BASE}/instance/sitemaps/sitemap-records-1.xml"
PART_2 = f"{BASE}/instance/sitemaps/sitemap-records-2.xml"

INDEX_XML = f"""<sitemapindex>
<sitemap><loc>{BASE}/instance/sitemaps/sitemap-news-1.xml</loc></sitemap>
<sitemap><loc>{PART_1}</loc></sitemap>
<sitemap><loc>{PART_2}</loc></sitemap>
<sitemap><loc>{BASE}/instance/sitemaps/sitemap-pages-1.xml</loc></sitemap>
</sitemapindex>"""

SHARD_1 = f"""<urlset>
<url><loc>{BASE}/record/100</loc></url>
<url><loc>{BASE}/record/101</loc></url>
</urlset>"""

SHARD_2 = f"""<urlset>
<url><loc>{BASE}/record/102</loc></url>
</urlset>"""

DETAIL = """<html><body>
<h1>TEST FILM [Allocated Title]</h1>
<div>Film Number: IWM 100</div>
<div>Digitised: No</div>
<div>Production Date: 1942</div>
<div>Production Country: GB</div>
<div>Sound: Silent</div>
<div>Physical Characteristics: B&amp;W</div>
<div>Technical Details: 35mm</div>
<div>Media not currently available</div>
</body></html>"""


def response(url, text="", status_code=200, error=None):
    return ProbeResponse(
        requested_url=url,
        final_url=url,
        status_code=status_code,
        content_type="text/html",
        text=text,
        error=error,
    )


class IwmFilmCollectionTests(unittest.TestCase):
    def test_index_parser_selects_only_record_sitemap_partitions(self):
        self.assertEqual(
            parse_iwm_sitemap_index(INDEX_XML),
            [PART_1, PART_2],
        )

    def test_record_sitemap_parser_tracks_duplicates_and_filters_non_records(self):
        xml = f"""<urlset>
        <url><loc>{BASE}/record/100</loc></url>
        <url><loc>{BASE}/record/100</loc></url>
        <url><loc>{BASE}/news/100</loc></url>
        <url><loc>https://example.org/record/999</loc></url>
        </urlset>"""
        parsed = parse_iwm_record_sitemap(xml)
        self.assertEqual(parsed["record_urls"], [f"{BASE}/record/100"])
        self.assertEqual(parsed["duplicates"], [f"{BASE}/record/100"])
        self.assertEqual(
            parsed["rejected_urls"],
            ["https://example.org/record/999", f"{BASE}/news/100"],
        )
        self.assertEqual(parsed["rejected_location_count"], 2)
        self.assertEqual(parsed["record_count"], 1)

    def test_detail_parser_confirms_public_film_metadata(self):
        row = parse_iwm_detail_page(DETAIL, f"{BASE}/record/100")
        self.assertTrue(row["film_semantics_confirmed"])
        self.assertEqual(row["title"], "TEST FILM [Allocated Title]")
        self.assertEqual(row["digitised"], "no")
        self.assertIn("IWM 100", row["film_number"])
        self.assertIn("1942", row["date"])

    def test_collector_materializes_all_announced_record_partitions(self):
        def robots_loader(_session):
            return (
                True,
                "robots_evaluated_rfc9309",
                "User-agent: *\nAllow: /\n"
                f"Sitemap: {INDEX_URL}\n",
            )

        def fetch_allowed(_session, url, _robots_text):
            if url == INDEX_URL:
                return response(url, INDEX_XML)
            if url == PART_1:
                return response(url, SHARD_1)
            if url == PART_2:
                return response(url, SHARD_2)
            if "/record/" in url:
                return response(url, DETAIL)
            raise AssertionError(url)

        institutions, summary, links, internal = collect_iwm_film_dataset(
            session=object(),
            robots_loader=robots_loader,
            fetch_allowed=fetch_allowed,
        )
        self.assertEqual(len(institutions), 1)
        self.assertEqual(summary[0]["integrity_status"], "integro")
        self.assertEqual(summary[0]["video_links_found_total"], 3)
        self.assertEqual(len(links), 3)
        self.assertEqual(len({row["video_link"] for row in links}), 3)
        self.assertEqual(
            sum("sitemap-records" in row["internal_page"] for row in internal),
            2,
        )
        self.assertEqual(
            sum("/record/" in row["internal_page"] for row in internal),
            3,
        )
        self.assertTrue(all(row["platform"] == "IWM Film" for row in links))

    def test_iwm_theme_inference_ignores_collection_boilerplate(self):
        unenriched = {
            "platform": "IWM Film",
            "video_title": "",
            "video_subject": "IWM Film Archive record",
            "video_description": (
                "Public film-catalogue metadata permalink enumerated from the "
                "robots-declared IWM Film sitemap."
            ),
        }
        military = {
            **unenriched,
            "video_title": "MILITARY ACTIVITIES IN KENYA",
        }

        self.assertEqual(
            infer_video_theme(unenriched),
            "Registro filmográfico IWM — tema não identificado",
        )
        self.assertEqual(
            infer_video_theme(military),
            "Guerra, forças armadas e conflito",
        )
        self.assertNotEqual(
            infer_video_theme(unenriched),
            "Digitalização e acesso",
        )

    def test_partially_unparseable_partition_fails_integrity(self):
        mixed_shard = f"""<urlset>
        <url><loc>{BASE}/record/100</loc></url>
        <url><loc>{BASE}/news/should-not-be-silently-dropped</loc></url>
        </urlset>"""
        single_index = f"""<sitemapindex>
        <sitemap><loc>{PART_1}</loc></sitemap>
        </sitemapindex>"""

        def fetch_allowed(_session, url, _robots_text):
            if url == INDEX_URL:
                return response(url, single_index)
            if url == PART_1:
                return response(url, mixed_shard)
            if url == f"{BASE}/record/100":
                return response(url, DETAIL)
            raise AssertionError(url)

        _, summary, links, internal = collect_iwm_film_dataset(
            session=object(),
            robots_loader=lambda _session: (
                True,
                "robots_evaluated_rfc9309",
                "User-agent: *\nAllow: /\n",
            ),
            fetch_allowed=fetch_allowed,
        )

        self.assertEqual(len(links), 1)
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertIn("rejected_locations=1", summary[0]["error"])
        partition_rows = [
            row
            for row in internal
            if row["internal_page"] == PART_1
        ]
        self.assertEqual(partition_rows[0]["status"], "erro")
        self.assertIn("rejected_locations=1", partition_rows[0]["error"])

    def test_cross_partition_duplicate_fails_integrity(self):
        duplicate = f"""<urlset>
        <url><loc>{BASE}/record/100</loc></url>
        </urlset>"""

        def fetch_allowed(_session, url, _robots_text):
            if url == INDEX_URL:
                return response(url, INDEX_XML)
            if url == PART_1:
                return response(url, SHARD_1)
            if url == PART_2:
                return response(url, duplicate)
            if "/record/" in url:
                return response(url, DETAIL)
            raise AssertionError(url)

        _, summary, _, _ = collect_iwm_film_dataset(
            session=object(),
            robots_loader=lambda _session: (
                True,
                "robots_evaluated_rfc9309",
                "User-agent: *\nAllow: /\n",
            ),
            fetch_allowed=fetch_allowed,
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertIn("cross_partition_duplicates=1", summary[0]["error"])

    def test_missing_partition_fails_integrity(self):
        def fetch_allowed(_session, url, _robots_text):
            if url == INDEX_URL:
                return response(url, INDEX_XML)
            if url == PART_1:
                return response(url, SHARD_1)
            if url == PART_2:
                return response(url, status_code=503, error="synthetic")
            if "/record/" in url:
                return response(url, DETAIL)
            raise AssertionError(url)

        _, summary, _, internal = collect_iwm_film_dataset(
            session=object(),
            robots_loader=lambda _session: (
                True,
                "robots_evaluated_rfc9309",
                "User-agent: *\nAllow: /\n",
            ),
            fetch_allowed=fetch_allowed,
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertTrue(any(row["status"] == "erro" for row in internal))

    def test_semantic_drift_fails_integrity(self):
        bad_detail = "<html><body><h1>Not a film record</h1></body></html>"

        def fetch_allowed(_session, url, _robots_text):
            if url == INDEX_URL:
                single_index = f"""<sitemapindex>
                <sitemap><loc>{PART_1}</loc></sitemap>
                </sitemapindex>"""
                return response(url, single_index)
            if url == PART_1:
                return response(url, SHARD_1)
            if url.endswith("/record/100"):
                return response(url, bad_detail)
            if "/record/" in url:
                return response(url, DETAIL)
            raise AssertionError(url)

        _, summary, _, _ = collect_iwm_film_dataset(
            session=object(),
            robots_loader=lambda _session: (
                True,
                "robots_evaluated_rfc9309",
                "User-agent: *\nAllow: /\n",
            ),
            fetch_allowed=fetch_allowed,
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertIn("film_semantics_not_confirmed", summary[0]["error"])

    def test_robots_failure_stops_before_enumeration(self):
        institutions, summary, links, internal = collect_iwm_film_dataset(
            session=object(),
            robots_loader=lambda _session: (
                False,
                "robots_unreachable",
                "",
            ),
            fetch_allowed=lambda *_args: self.fail("fetch must not run"),
        )
        self.assertEqual(len(institutions), 1)
        self.assertEqual(links, [])
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertEqual(internal[0]["status"], "bloqueado_robots")


if __name__ == "__main__":
    unittest.main()
