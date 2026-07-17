import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.luce import (
    collect_luce_institutions,
    extract_luce_declared_pages,
    extract_luce_video_files,
    parse_luce_detail_page,
    parse_luce_search_page,
)


SEARCH_HTML = """
<html><body>
<select class="pageChange"><option>1</option></select><span>di 14968</span>
<div class="singolo-risultato">
  <a href="/luce-web/detail/IL3000095511/34/-122199.html?startPage=0">
    Cineteca del Friuli Boxeurs en tonneaux data: 1895 00:00:39 b/n muto
  </a>
  <script>file: "https://videocinecitta.bytewise.it/vod/archivioluce/MpegCF300/CF00913.mp4/playlist.m3u8"</script>
</div>
<div class="singolo-risultato">
  <a href="/luce-web/detail/IL3000094233/1/${resultBean.titleUrl_indexed_no}.html?startPage=20">template</a>
</div>
</body></html>
"""


DETAIL_HTML = """
<html><head>
<title>Boxeurs en tonneaux - Archivio storico Istituto Luce</title>
<meta property="og:title" content="Boxeurs en tonneaux" />
<meta property="og:description" content="Due pugili si affrontano stando in piedi in due grandi botti." />
</head><body>
<p>data: 1895 durata: 00:00:39 colore: b/n sonoro: muto codice filmato: CF00913
regia di: Lumière, Auguste Lumière, Louis edizione lingua: francese nazionalità: francese
sequenze un uomo con i guantoni è in piedi all'interno di un botte keywords film storia del cinema</p>
<script>
jwplayer("IL3000095511").setup({playlist: [{sources: [
{file: "rtmp://videocinecitta.bytewise.it:80/vod/mp4:MpegCF300/CF00913.mp4"},
{file: "https://videocinecitta.bytewise.it/vod/archivioluce/MpegCF300/CF00913.mp4/playlist.m3u8"}
]}]});
</script>
</body></html>
"""


class LuceCollectionTests(unittest.TestCase):
    def test_collect_luce_institutions_declares_italian_archive(self):
        institutions = collect_luce_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "IT-CINECITTA-LUCE")
        self.assertEqual(institutions[0]["country"], "Italy")

    def test_parse_luce_search_page_keeps_real_detail_links(self):
        records = parse_luce_search_page(SEARCH_HTML, "https://patrimonio.archivioluce.com/luce-web/")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "IL3000095511")
        self.assertIn("/luce-web/detail/IL3000095511/", records[0]["page_url"])
        self.assertTrue(records[0]["embedded"])
        self.assertEqual(extract_luce_declared_pages(SEARCH_HTML), 14968)

    def test_parse_luce_detail_page_extracts_metadata_and_hls(self):
        parsed = parse_luce_detail_page(
            DETAIL_HTML,
            "https://patrimonio.archivioluce.com/luce-web/detail/IL3000095511/34/-122199.html",
        )

        self.assertEqual(parsed["title"], "Boxeurs en tonneaux")
        self.assertEqual(parsed["date"], "1895")
        self.assertIn("playlist.m3u8", parsed["video_link"])
        self.assertTrue(parsed["embedded"])
        self.assertIn("CF00913", parsed["description"])
        self.assertIn("storia del cinema", parsed["subject"])
        self.assertEqual(len(extract_luce_video_files(DETAIL_HTML)), 2)

        analytic_row = {
            "platform": "Archivio Luce",
            "video_link": parsed["video_link"],
            "video_title": parsed["title"],
            "video_subject": parsed["subject"],
            "video_description": parsed["description"],
        }
        self.assertEqual(infer_video_theme(analytic_row), "Ficção cinematográfica")
        self.assertEqual(classify_access_surface(analytic_row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
