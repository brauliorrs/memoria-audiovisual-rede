"""Offline regression tests for MAR KAVI approved metadata-catalog navigation."""
import unittest

from memoria_audiovisual.kavi_finna_catalog_navigation import (
    CatalogNavigationRejected, available_facets, navigate_approved_records,
)


def record(rid, title, *, year="1936", languages="fi; sv", classification="film_candidate"):
    return {
        "source_record_id": rid,
        "source_record_url": "https://www.finna.fi/Record/" + rid,
        "video_link": "https://www.finna.fi/Record/" + rid,
        "video_title": title, "year": year, "authors": "Artist",
        "subjects": "História", "genres": "documentary", "languages": languages,
        "film_semantics": classification, "media_access_status": "unverified",
        "link_status": "item_link_verified_by_source",
    }


class PublishedNavigationTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            record("id-3", "Zebra", year="1940", languages="en"),
            record("id-2", "Árvore", year="1936"),
            record("id-1", "Árvore", year="1936", classification="unverified_audiovisual_record"),
        ]

    def test_unicode_casefold_and_literal_query(self):
        result = navigate_approved_records(self.rows, query="ARVORE")
        self.assertEqual([x["source_record_id"] for x in result["rows"]], ["id-1", "id-2"])
        self.assertEqual(navigate_approved_records(self.rows, query=".*")["total"], 0)

    def test_year_language_classification_conjunction(self):
        result = navigate_approved_records(
            self.rows, year="1936", language="SV", classification="film_candidate"
        )
        self.assertEqual([x["source_record_id"] for x in result["rows"]], ["id-2"])

    def test_facets_are_documentary_values_only(self):
        f = available_facets(self.rows)
        self.assertEqual(f["years"], ["1936", "1940"])
        self.assertEqual(f["languages"], ["en", "fi", "sv"])
        self.assertEqual(f["classifications"], sorted([
            "film_candidate", "unverified_audiovisual_record",
        ]))

    def test_pagination_stable_and_total_not_page_count(self):
        rows = [record("id-" + str(n), "Film") for n in range(27, -1, -1)]
        p1 = navigate_approved_records(rows, page=1)
        p2 = navigate_approved_records(rows, page=2)
        self.assertEqual((p1["total"], p1["pages"], len(p1["rows"])), (28, 2, 25))
        self.assertEqual(len(p2["rows"]), 3)
        self.assertFalse(set(x["source_record_id"] for x in p1["rows"])
                         & set(x["source_record_id"] for x in p2["rows"]))
        self.assertEqual(navigate_approved_records(rows, page=1)["rows"], p1["rows"])

    def test_invalid_navigation_fails_closed(self):
        for kwargs in ({"page": 0}, {"page": 3}, {"page_size": 7},
                       {"page": True}, {"query": 3}, {"classification": "verified_film"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(CatalogNavigationRejected):
                navigate_approved_records(self.rows, **kwargs)

    def test_reject_duplicate_ids_and_missing_approved_link(self):
        for rows in ([self.rows[0], dict(self.rows[0])],
                     [dict(self.rows[0], video_link="https://example.org/video.mp4")],
                     [dict(self.rows[0], link_status="missing_source_item_link")]):
            with self.assertRaises(CatalogNavigationRejected):
                navigate_approved_records(rows)

    def test_never_mutates_approved_source(self):
        before = [dict(x) for x in self.rows]
        result = navigate_approved_records(self.rows, page_size=25)
        result["rows"][0]["video_title"] = "changed locally"
        self.assertEqual(self.rows, before)

    def test_search_on_metadata_not_playback(self):
        match = navigate_approved_records(self.rows, query="HISTORIA")
        self.assertEqual(match["total"], 3)
        self.assertTrue(all(x["media_access_status"] == "unverified" for x in match["rows"]))


if __name__ == "__main__":
    unittest.main()
