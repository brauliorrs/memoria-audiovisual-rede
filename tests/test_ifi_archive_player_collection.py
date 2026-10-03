import unittest

from memoria_audiovisual.ifi_archive_player import (
    collect_ifi_archive_player_dataset,
    parse_ifi_detail_page,
    parse_ifi_post_sitemap,
    parse_ifi_sitemap_index,
)


INDEX_XML = """<sitemapindex>
<sitemap><loc>https://ifiarchiveplayer.ie/post-sitemap.xml</loc></sitemap>
<sitemap><loc>https://ifiarchiveplayer.ie/post-sitemap2.xml</loc></sitemap>
<sitemap><loc>https://ifiarchiveplayer.ie/page-sitemap.xml</loc></sitemap>
</sitemapindex>"""

SHARD_1 = """<urlset>
<url><loc>https://ifiarchiveplayer.ie/film-a/</loc></url>
<url><loc>https://ifiarchiveplayer.ie/film-b/</loc></url>
</urlset>"""

SHARD_2 = """<urlset>
<url><loc>https://ifiarchiveplayer.ie/film-c/</loc></url>
</urlset>"""

DETAIL = """<html><body>
<h1>Film A</h1>
<p>Category: Documentary</p>
<p>Directed by: Jane Doe</p>
<p>Produced by: IFI</p>
<p>Year: 1975</p>
<p>Duration: 10 mins</p>
<p>Language: English</p>
</body></html>"""


class FakeResponse:
    def __init__(self, text, url, status_code=200):
        self.text = text
        self.url = url
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class IfiArchivePlayerCollectionTests(unittest.TestCase):
    def test_index_parser_selects_only_post_sitemap_partitions(self):
        self.assertEqual(
            parse_ifi_sitemap_index(INDEX_XML),
            [
                "https://ifiarchiveplayer.ie/post-sitemap.xml",
                "https://ifiarchiveplayer.ie/post-sitemap2.xml",
            ],
        )

    def test_post_sitemap_parser_filters_editorial_and_xml_urls(self):
        xml = """<urlset>
        <url><loc>https://ifiarchiveplayer.ie/film-a/</loc></url>
        <url><loc>https://ifiarchiveplayer.ie/legal/</loc></url>
        <url><loc>https://ifiarchiveplayer.ie/post-sitemap.xml</loc></url>
        </urlset>"""
        self.assertEqual(
            parse_ifi_post_sitemap(xml),
            ["https://ifiarchiveplayer.ie/film-a/"],
        )

    def test_detail_parser_extracts_public_film_metadata(self):
        row = parse_ifi_detail_page(
            DETAIL,
            "https://ifiarchiveplayer.ie/film-a/",
        )
        self.assertEqual(row["title"], "Film A")
        self.assertIn("Documentary", row["category"])
        self.assertIn("Jane Doe", row["director"])
        self.assertIn("1975", row["date"])
        self.assertIn("10 mins", row["duration"])

    def test_collector_materializes_all_announced_partitions(self):
        def robots_checker(_url):
            return True, "robots_evaluated_rfc9309"

        def fetch(url):
            if url.endswith("/sitemap_index.xml"):
                return FakeResponse(INDEX_XML, url)
            if url.endswith("/post-sitemap.xml"):
                return FakeResponse(SHARD_1, url)
            if url.endswith("/post-sitemap2.xml"):
                return FakeResponse(SHARD_2, url)
            if "/film-" in url:
                return FakeResponse(DETAIL, url)
            raise AssertionError(url)

        institutions, summary, links, internal = collect_ifi_archive_player_dataset(
            fetch=fetch,
            robots_checker=robots_checker,
        )
        self.assertEqual(len(institutions), 1)
        self.assertEqual(summary[0]["integrity_status"], "integro")
        self.assertEqual(summary[0]["video_links_found_total"], 3)
        self.assertEqual(len(links), 3)
        self.assertEqual(len({row["video_link"] for row in links}), 3)
        self.assertEqual(
            sum("post-sitemap" in row["internal_page"] for row in internal),
            2,
        )
        self.assertTrue(
            all(row["platform"] == "IFI Archive Player" for row in links)
        )

    def test_cross_partition_duplicate_fails_integrity(self):
        duplicate_shard = """<urlset>
        <url><loc>https://ifiarchiveplayer.ie/film-a/</loc></url>
        </urlset>"""

        def fetch(url):
            if url.endswith("/sitemap_index.xml"):
                return FakeResponse(INDEX_XML, url)
            if url.endswith("/post-sitemap.xml"):
                return FakeResponse(SHARD_1, url)
            if url.endswith("/post-sitemap2.xml"):
                return FakeResponse(duplicate_shard, url)
            if "/film-" in url:
                return FakeResponse(DETAIL, url)
            raise AssertionError(url)

        _, summary, _, _ = collect_ifi_archive_player_dataset(
            fetch=fetch,
            robots_checker=lambda _url: (True, "robots_evaluated_rfc9309"),
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertIn("cross_partition_duplicates=1", summary[0]["error"])

    def test_missing_partition_fails_integrity(self):
        def fetch(url):
            if url.endswith("/sitemap_index.xml"):
                return FakeResponse(INDEX_XML, url)
            if url.endswith("/post-sitemap.xml"):
                return FakeResponse(SHARD_1, url)
            if url.endswith("/post-sitemap2.xml"):
                raise RuntimeError("synthetic failure")
            if "/film-" in url:
                return FakeResponse(DETAIL, url)
            raise AssertionError(url)

        _, summary, _, internal = collect_ifi_archive_player_dataset(
            fetch=fetch,
            robots_checker=lambda _url: (True, "robots_evaluated_rfc9309"),
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertTrue(any(row["status"] == "erro" for row in internal))

    def test_robots_failure_stops_before_enumeration(self):
        institutions, summary, links, internal = collect_ifi_archive_player_dataset(
            fetch=lambda _url: self.fail("fetch must not run"),
            robots_checker=lambda _url: (False, "robots_unreachable"),
        )
        self.assertEqual(len(institutions), 1)
        self.assertEqual(links, [])
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertEqual(internal[0]["status"], "bloqueado_robots")


if __name__ == "__main__":
    unittest.main()
