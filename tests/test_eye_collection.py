import unittest

from memoria_audiovisual.eye import (
    extract_eye_declared_fragment_total,
    extract_eye_max_page,
    parse_eye_fragment_list_page,
)


EYE_LIST_HTML = """
<html>
  <body>
    <div class="block-facetapi">
      <a>(-) Remove with film fragment filter with film fragment 630</a>
    </div>
    <div class="view-content">
      <ul class="list packery-container">
        <li class="packery-item first">
          <div about="/en/collection/film-history/film/als-het-verleden-spreekt"
               class="node node-collection-movie">
            <a href="/en/collection/film-history/film/als-het-verleden-spreekt">
              <img src="https://filmdatabase.eyefilm.nl/files/thumb.jpg" />
            </a>
            <div class="icon icon-movie"><strong>Film</strong></div>
            <h2>
              <a href="/en/collection/film-history/film/als-het-verleden-spreekt">
                ... Als het verleden spreekt
              </a>
            </h2>
          </div>
        </li>
        <li class="packery-item">
          <div about="/en/collection/film-history/film/and-a-table"
               class="node node-collection-movie">
            <h2><a href="/en/collection/film-history/film/and-a-table">...And a Table</a></h2>
          </div>
        </li>
        <li class="packery-item">
          <div about="/en/node/123470" class="node node-collection-movie">
            <h2><a href="/en/node/123470">Bleeke Bet (1923)</a></h2>
          </div>
        </li>
      </ul>
    </div>
    <ul class="pager">
      <li><a href="/en/collection/film-history/film/all/all?f%5B0%5D=field_cm_media_filter%3Awith%20film%20fragment&page=1">2</a></li>
      <li><a href="/en/collection/film-history/film/all/all?f%5B0%5D=field_cm_media_filter%3Awith%20film%20fragment&page=62">last</a></li>
    </ul>
  </body>
</html>
"""


class EyeCollectionTests(unittest.TestCase):
    def test_extract_declared_fragment_total_and_max_page(self):
        self.assertEqual(extract_eye_declared_fragment_total(EYE_LIST_HTML), 630)
        self.assertEqual(extract_eye_max_page(EYE_LIST_HTML), 62)

    def test_parse_eye_fragment_list_page_materializes_public_records(self):
        records = parse_eye_fragment_list_page(
            EYE_LIST_HTML,
            "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/all/all",
        )

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["record_id"], "als-het-verleden-spreekt")
        self.assertEqual(records[0]["platform"], "Eye Filmdatabase")
        self.assertIn("filmdatabase.eyefilm.nl", records[0]["video_link"])
        self.assertIn("fragmento de filme", records[0]["description"])
        self.assertEqual(records[2]["record_id"], "node-123470")


if __name__ == "__main__":
    unittest.main()
