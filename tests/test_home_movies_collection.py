import unittest

from memoria_audiovisual.home_movies import (
    MemoryscapesFetchResult,
    collect_home_movies_dataset,
    parse_home_movies_record,
)


class HomeMoviesCollectionTests(unittest.TestCase):
    def test_parse_record_uses_public_vimeo_player_and_metadata(self):
        parsed = parse_home_movies_record(
            {
                "id": 6832,
                "title": {"en": "1956 Winter Olympics: Speed Skating", "it": "Olimpiadi"},
                "description": {"en": "Speed skating trial in Cortina.", "it": "Pattinaggio."},
                "date": "1956-01-01",
                "date_from": "1956-01-01",
                "archive": "HMGRASLUI-0004",
                "format": "8mm",
                "url_content": "https://player.vimeo.com/video/1160131904?h=fa9f8673b8",
                "author_data": {"name": "Grassi, Luigi"},
                "keywords_data": [{"value": {"en": "sport", "it": "sport"}}],
                "city": "Cortina d'Ampezzo(Belluno)",
                "position": {"coordinates": [12.13, 46.54]},
                "content_metadata": {"width": 1920, "height": 1080},
            }
        )

        self.assertEqual(parsed["record_id"], "6832")
        self.assertIn("player.vimeo.com/video/1160131904", parsed["video_link"])
        self.assertIn("sport", parsed["subject"])
        self.assertIn("ficha pública: https://www.memoryscapes.it/en/clips/6832", parsed["description"])

    def test_parse_record_requires_public_player_url(self):
        parsed = parse_home_movies_record(
            {
                "id": 9,
                "title": {"en": "Technical file only"},
                "file_url_vimeo": "https://player.vimeo.com/progressive_redirect/playback/9/file.mp4",
            }
        )

        self.assertEqual(parsed["video_link"], "")
        self.assertFalse(parsed["has_public_player"])
    def test_collect_dataset_paginates_and_details_public_clips(self):
        def fake_fetch(url, params=None):
            params = params or {}
            if url.endswith("/api/clips/"):
                page = int(params.get("page", 1))
                if page == 1:
                    return MemoryscapesFetchResult(
                        {
                            "count": 2,
                            "total_count": 2,
                            "next": "https://www.memoryscapes.it/api/clips/?page=2",
                            "results": [{"id": 1}],
                        },
                        200,
                        "https://www.memoryscapes.it/api/clips/?page=1",
                    )
                return MemoryscapesFetchResult(
                    {"count": 2, "total_count": 2, "next": None, "results": [{"id": 2}]},
                    200,
                    "https://www.memoryscapes.it/api/clips/?page=2",
                )
            record_id = url.rstrip("/").split("/")[-1]
            return MemoryscapesFetchResult(
                {
                    "id": int(record_id),
                    "title": {"en": f"Clip {record_id}"},
                    "description": {"en": "Public clip."},
                    "date": "1950-01-01",
                    "url_content": f"https://player.vimeo.com/video/{record_id}",
                    "author_data": {"name": "Author"},
                    "keywords_data": [{"value": {"en": "family"}}],
                    "format": "8mm",
                },
                200,
                url,
            )

        institutions, summary, links, internal_pages = collect_home_movies_dataset(fake_fetch, page_size=1)

        self.assertEqual(len(institutions), 1)
        self.assertEqual(summary[0]["video_links_found_total"], 2)
        self.assertEqual(len(links), 2)
        self.assertTrue(all(row["platform"] == "Memoryscapes" for row in links))
        self.assertEqual(len(internal_pages), 3)



    def test_collect_dataset_deduplicates_public_player_urls(self):
        def fake_fetch(url, params=None):
            params = params or {}
            if url.endswith("/api/clips/"):
                return MemoryscapesFetchResult(
                    {"count": 2, "total_count": 2, "next": None, "results": [{"id": 1}, {"id": 2}]},
                    200,
                    "https://www.memoryscapes.it/api/clips/?page=1",
                )
            record_id = url.rstrip("/").split("/")[-1]
            return MemoryscapesFetchResult(
                {
                    "id": int(record_id),
                    "title": {"en": f"Clip {record_id}"},
                    "url_content": "https://player.vimeo.com/video/duplicate",
                },
                200,
                url,
            )

        _, summary, links, _ = collect_home_movies_dataset(fake_fetch, page_size=2)

        self.assertEqual(summary[0]["video_links_found_total"], 1)
        self.assertEqual(len(links), 1)
if __name__ == "__main__":
    unittest.main()
