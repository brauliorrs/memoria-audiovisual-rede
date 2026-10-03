import unittest

from memoria_audiovisual.analysis_progress import build_analysis_progress


class AnalysisProgressTests(unittest.TestCase):
    def test_current_engine_has_77_completed_corpus_analyses(self):
        progress = build_analysis_progress()
        self.assertEqual(progress["corpora_defined_total"], 61)
        self.assertEqual(progress["active_corpora_total"], 58)
        self.assertEqual(progress["inactive_corpora_total"], 3)
        self.assertEqual(progress["protocolled_units_total"], 19)
        self.assertEqual(progress["protocolled_already_in_corpora_total"], 3)
        self.assertEqual(progress["protocolled_outside_corpora_total"], 16)
        self.assertEqual(progress["analyzed_corpora_total"], 77)
        self.assertEqual(progress["next_analysis_number"], 78)

    def test_active_and_hold_units_are_deduplicated_by_canonical_identity(self):
        progress = build_analysis_progress()
        codes = set(progress["analyzed_corpus_codes"])
        self.assertIn("ifi_archive_player", codes)
        self.assertIn("murnau_stiftung", codes)
        self.assertIn("gosfilmofond", codes)
        self.assertIn("eafa", codes)
        self.assertIn("cnc-aff", codes)
        self.assertIn("cinematheque-suisse", codes)
        self.assertIn("inedits-forum-des-images", codes)
        self.assertIn("fiaf-croatian-cinematheque", codes)
        self.assertNotIn("fiaf-ifi-irish-film-archive", codes)
        self.assertNotIn("fiat-east-anglian-film-archive", codes)
        self.assertNotIn("fiaf-cnc-aff", codes)
        self.assertNotIn("inedits-image-est", codes)


if __name__ == "__main__":
    unittest.main()
