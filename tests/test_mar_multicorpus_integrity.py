"""Tests of the complete, offline MAR historical dataset integrity scanner."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mar_full_integrity", ROOT / "scripts/audit_mar_multicorpus_integrity.py")
import sys
sys.path.insert(0, str(ROOT / "scripts"))
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


class FullAuditTests(unittest.TestCase):
    def test_detects_duplicates_bad_origin_and_titles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csvpath = root / audit_module.CORPORA["eye"]["path"]
            csvpath.parent.mkdir(parents=True, exist_ok=True)
            base = "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/a"
            rows = [
                ("Eye Filmmuseum", base, "Film A"),
                ("Eye Filmmuseum", base, "Film A revised"),
                ("Eye Filmmuseum", base + "/", "Film A"),
                ("Eye Filmmuseum", "https://example.com/not-official", "Film X"),
                ("Other", "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/b", ""),
            ]
            with csvpath.open("w", newline="", encoding="utf-8") as out:
                writer = csv.writer(out)
                writer.writerow(["institution", "video_link", "video_title"])
                writer.writerows(rows)
            original = csvpath.read_bytes()
            report = audit_module.audit("eye", root=root)
            self.assertEqual(original, csvpath.read_bytes())
            self.assertEqual(report["sourceRows"], 5)
            self.assertEqual(report["issues"]["duplicate_exact_url"], 1)
            self.assertEqual(report["issues"]["duplicate_canonical_url"], 2)
            self.assertEqual(report["issues"]["duplicate_generated_identifier"], 1)
            self.assertEqual(report["issues"]["conflicting_titles_same_url"], 1)
            self.assertEqual(report["issues"]["invalid_or_nonofficial_url"], 1)
            self.assertEqual(report["issues"]["blank_title"], 1)
            self.assertEqual(report["issues"]["institution_mismatch"], 1)
            self.assertFalse(report["publicationAllowed"])

    def test_distinguishes_czech_episode_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csvpath = root / audit_module.CORPORA["czech"]["path"]
            csvpath.parent.mkdir(parents=True, exist_ok=True)
            with csvpath.open("w", newline="", encoding="utf-8") as out:
                writer = csv.writer(out)
                writer.writerow(["institution", "video_link", "video_title"])
                writer.writerow(["Czech Television", "https://www.ceskatelevize.cz/porady/1/episode1/", "One"])
                writer.writerow(["Czech Television", "https://www.ceskatelevize.cz/porady/1/episode2/", "Two"])
            report = audit_module.audit("czech", root=root)
            self.assertEqual(report["sourceRows"], 2)
            self.assertEqual(report["validOfficialUrlRows"], 2)
            self.assertEqual(report["issues"], {})
            self.assertEqual(report["uniqueGeneratedIdentifiers"], 2)


if __name__ == "__main__":
    unittest.main()
