import unittest

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.forum_des_images import (
    collect_forum_des_images_institutions,
    parse_forum_des_images_browse_page,
    parse_forum_des_images_detail_page,
)


BROWSE_HTML = """
<html><body>
<div class="result">
  <span>Image visible en Salle des Collections et sur internet</span>
  <a href="/CogniTellUI/faces/details.xhtml?id=FDI100">Film public</a>
  <span>de Alice Martin</span>
  <span>documentaire, 2019, couleur, 52min</span>
  <span>Collection Productions Forum des images</span>
</div>
<div class="result">
  <span>Image non visible en Salle des Collections</span>
  <a href="/CogniTellUI/faces/details.xhtml?id=FDI101">Film local</a>
  <span>fiction, 1989, couleur, 20min</span>
</div>
<a href="/CogniTellUI/faces/details.xhtml?id=FDI100">duplicate</a>
</body></html>
"""

DETAIL_HTML = """
<html><body>
<h1>Film public</h1>
<div>Notice</div>
<table>
<tr><th>réalisation</th><td>Alice Martin</td></tr>
<tr><th>production</th><td>Forum des images 2019</td></tr>
</table>
<p>Collection Productions Forum des images</p>
<p>visible en Salle des Collections et sur internet</p>
<iframe src="https://player.example.org/video/100"></iframe>
</body></html>
"""


class ForumDesImagesCollectionTests(unittest.TestCase):
    def test_institution_contract(self):
        row = collect_forum_des_images_institutions()[0]
        self.assertEqual(row["institution"], "Forum des images")
        self.assertEqual(row["country"], "France")
        self.assertTrue(row["content_available_in_source"])
        self.assertIn("collections.forumdesimages.fr", row["external_url"])

    def test_browse_parser_materializes_unique_public_records(self):
        rows = parse_forum_des_images_browse_page(
            BROWSE_HTML,
            "https://collections.forumdesimages.fr/CogniTellUI/faces/browse.xhtml?query=test",
        )
        self.assertEqual([row["record_id"] for row in rows], ["FDI100", "FDI101"])
        self.assertEqual(rows[0]["title"], "Film public")
        self.assertEqual(rows[0]["date"], "2019")
        self.assertEqual(rows[0]["availability"], "visible_sur_internet")
        self.assertEqual(rows[1]["availability"], "non_visible_en_ligne")

    def test_detail_parser_preserves_permalink_and_access_state(self):
        row = parse_forum_des_images_detail_page(
            DETAIL_HTML,
            "https://collections.forumdesimages.fr/CogniTellUI/faces/details.xhtml?id=FDI100",
        )
        self.assertEqual(row["record_id"], "FDI100")
        self.assertEqual(row["title"], "Film public")
        self.assertEqual(row["date"], "2019")
        self.assertEqual(row["availability"], "visible_sur_internet")
        self.assertTrue(row["embedded"])
        self.assertEqual(row["video_link"], "https://player.example.org/video/100")
        self.assertIn("Alice Martin", row["subject"])

    def test_corpus_registry_records_bounded_non_exhaustive_scope(self):
        corpus = CORPORA["forum-des-images"]
        self.assertTrue(corpus["organism_active"])
        self.assertTrue(corpus["monthly_refresh_enabled"])
        self.assertEqual(corpus["code"], "forum_des_images")
        self.assertIn("30 fichas", corpus["selection_limit"])
        self.assertIn("Não representa", corpus["completeness_note"])
        self.assertEqual(
            corpus["check_script"],
            "python scripts/check_forum_des_images_outputs.py",
        )


if __name__ == "__main__":
    unittest.main()
