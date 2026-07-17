import unittest

from memoria_audiovisual.eafa import (
    collect_eafa_institutions,
    extract_eafa_search_totals,
    parse_eafa_search_page,
    parse_eafa_work_page,
)


SEARCH_HTML = """
<div class="statistics">Showing results 1 - 12 of 1,627</div>
<input class="pageNumber" max="136" />
<ul id="search-result-items">
  <li>
    <a href="/work/?id=W463994" aria-label="Open work"></a>
    <h2 class="item-title">A Village Film</h2>
    <div class="item-tile-meta">
      <span>1974</span>
      <span class="catno">Cat no. EAFA 123</span>
    </div>
    <div class="item-main">
      <p>Norfolk</p>
    </div>
    <p class="override-summary">Local life and streets.</p>
    <div class="canHide">
      <p>ignored</p>
      <p>00:12:00</p>
      <p>Colour / Sound</p>
    </div>
  </li>
</ul>
"""

WORK_HTML = """
<h1>A Village Film</h1>
<h2>Norfolk, 1974</h2>
<p class="date">Cat no. EAFA 123</p>
<div class="work-media">
  <iframe src="https://player.vimeo.com/video/1087146822"></iframe>
</div>
<ul class="work-details">
  <li><span>Category:</span> Amateur</li>
  <li><span>Genre:</span> Documentary</li>
  <li><span>Work Type:</span> Film</li>
  <li><span>Locations:</span> Norfolk</li>
</ul>
<div id="overview">
  <p class="lead">A short record of village life.</p>
  <p>People, streets and local events.</p>
  <h2>Keywords</h2>
  <p>village, Norfolk, everyday life</p>
</div>
"""


class EafaCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_single_archive(self):
        institutions = collect_eafa_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "East Anglian Film Archive")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_extract_search_totals(self):
        pages, total = extract_eafa_search_totals(SEARCH_HTML)

        self.assertEqual(pages, 136)
        self.assertEqual(total, 1627)

    def test_parse_search_page_extracts_work_card(self):
        records = parse_eafa_search_page(SEARCH_HTML, "https://eafa.org.uk/search/?hasVideo=on")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "W463994")
        self.assertEqual(records[0]["title"], "A Village Film")
        self.assertEqual(records[0]["date"], "1974")
        self.assertEqual(records[0]["duration"], "00:12:00")

    def test_parse_work_page_requires_public_player(self):
        search_record = parse_eafa_search_page(SEARCH_HTML, "https://eafa.org.uk/search/?hasVideo=on")[0]
        record = parse_eafa_work_page(WORK_HTML, search_record["detail_url"], search_record)

        self.assertEqual(record["platform"], "East Anglian Film Archive")
        self.assertEqual(record["record_id"], "W463994")
        self.assertEqual(record["date"], "1974")
        self.assertTrue(record["embedded"])
        self.assertIn("https://player.vimeo.com/video/1087146822", record["media_sources"])
        self.assertIn("Documentary", record["subject"])

    def test_parse_work_page_rejects_records_without_player(self):
        self.assertIsNone(parse_eafa_work_page("<h1>No player</h1>", "https://eafa.org.uk/work/?id=W0"))


if __name__ == "__main__":
    unittest.main()
