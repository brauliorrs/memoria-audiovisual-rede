import unittest

from memoria_audiovisual.estonian_film_archive import (
    collect_estonian_film_archive_dataset,
    parse_arkaader_broadcasts_payload,
    parse_arkaader_movies_payload,
)


MOVIES_PAYLOAD = [
    {
        "_ref": "record-1",
        "data": {
            "fields": {
                "name": {"value": "Test Newsreel"},
                "description": {"value": "A public archive film."},
                "year": {"value": 1960},
                "duration": {"value": 120},
                "filmType": {"value": ["Newsreel"]},
                "genre": {"value": ["Historical"]},
                "director": {"value": ["Test Director"]},
                "links": {"value": [{"name": "Meediateek", "link": "https://www.meediateek.ee/film/view?id=1"}]},
            }
        },
    }
]

BROADCASTS_PAYLOAD = [
    {
        "vl2id": "record-1",
        "token": "abc123",
        "metadata": '{"director":"Test Director","year":1960,"duration":120}',
        "ticketRestricted": True,
        "price": [2.6],
        "geoRestricted": False,
        "image": "https://example.test/poster.jpg",
    }
]


class EstonianFilmArchiveCollectionTests(unittest.TestCase):
    def test_parse_arkaader_payloads_materializes_broadcast_records(self):
        movie_fields = parse_arkaader_movies_payload(MOVIES_PAYLOAD)
        records = parse_arkaader_broadcasts_payload(BROADCASTS_PAYLOAD, movie_fields)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "record-1")
        self.assertEqual(records[0]["platform"], "Arkaader")
        self.assertIn("arkaader.ee/landing/bc", records[0]["video_link"])
        self.assertIn("Newsreel", records[0]["subject"])
        self.assertIn("acesso pago", records[0]["description"])
        self.assertFalse(records[0]["is_free"])

    def test_collect_dataset_uses_injected_fetchers(self):
        def fetch_movies():
            return MOVIES_PAYLOAD, "https://example.test/movies.json", 200

        def fetch_broadcasts():
            return BROADCASTS_PAYLOAD, "https://example.test/api/broadcasts", 200

        institutions, summary, links, internal_pages = collect_estonian_film_archive_dataset(fetch_movies, fetch_broadcasts)

        self.assertEqual(len(institutions), 1)
        self.assertEqual(len(summary), 1)
        self.assertEqual(len(links), 1)
        self.assertEqual(len(internal_pages), 2)
        self.assertEqual(institutions[0]["archive_type"], "National film archive with public audiovisual streaming catalogue")
        self.assertEqual(summary[0]["video_links_found_total"], 1)
        self.assertEqual(links[0]["platform"], "Arkaader")


if __name__ == "__main__":
    unittest.main()
