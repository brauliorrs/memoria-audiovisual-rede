import unittest

from memoria_audiovisual.deutsche_kinemathek import (
    collect_deutsche_kinemathek_institutions,
    parse_deutsche_kinemathek_detail_page,
    parse_deutsche_kinemathek_streaming_page,
)


class DeutscheKinemathekCollectionTests(unittest.TestCase):
    def test_collect_deutsche_kinemathek_institutions_declares_single_archive(self):
        institutions = collect_deutsche_kinemathek_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["country"], "Germany")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_streaming_page_detects_selects_card_and_player_signal(self):
        html = """
        <html>
          <body>
            <h1>Selects #16 | 15 May-30 Sep 26</h1>
            <div class="view__item basic-grid__item">
              <video>
                <source src="https://player.vimeo.com/progressive_redirect/playback/123/file.mp4">
              </video>
              <a href="/en/online/streaming/talk-straight-world-rural-queers">
                Talk Straight: The World of Rural Queers
              </a>
              GER 2003, directed by: Jochen Hick, 99 min, with English subtitles, rating: 12
            </div>
          </body>
        </html>
        """

        records = parse_deutsche_kinemathek_streaming_page(html)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "Talk Straight: The World of Rural Queers")
        self.assertEqual(records[0]["date"], "2003")
        self.assertEqual(records[0]["duration"], "99 min")
        self.assertTrue(records[0]["embedded"])
        self.assertIn("Jochen Hick", records[0]["subject"])

    def test_parse_detail_page_prefers_own_description_before_continue_watching(self):
        html = """
        <main>
          Back to the streaming start page
          <h1>Me</h1>
          FRG 1988, directed by: Bettina Flitner, 17 min, age rating: 0
          A filmic self-observation in urban space.
          Weiterschauen
          <a href="/en/online/streaming/other">Other film</a>
        </main>
        """

        record = parse_deutsche_kinemathek_detail_page(
            html,
            "https://www.deutsche-kinemathek.de/en/online/streaming/me",
            {"media_url": "https://player.vimeo.com/progressive_redirect/playback/456/file.mp4"},
        )

        self.assertEqual(record["title"], "Me")
        self.assertEqual(record["date"], "1988")
        self.assertIn("Bettina Flitner", record["subject"])
        self.assertIn("self-observation", record["description"])
        self.assertNotIn("Other film", record["description"])


if __name__ == "__main__":
    unittest.main()
