"""Dry-run contracts for Eye then Czech TV; existing datasets remain read-only."""
import csv
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/import_mar_multicorpus.py"
spec = importlib.util.spec_from_file_location("mar_multicorpus_staging", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MulticorpusStagingTests(unittest.TestCase):
    def make_source(self, root, corpus, rows):
        path = root / module.CORPORA[corpus]["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = ["institution", "video_link", "video_title", "video_title_display",
                  "video_date_display", "video_theme", "video_subject", "platform"]
        with path.open("w", newline="", encoding="utf-8") as out:
            writer = csv.DictWriter(out, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def example(self, corpus):
        if corpus == "eye":
            return dict(institution="Eye Filmmuseum",
                        video_link="https://filmdatabase.eyefilm.nl/en/collection/film-history/film/example",
                        video_title="Eye pilot", video_date_display="1922")
        return dict(institution="Czech Television",
                    video_link="https://www.ceskatelevize.cz/porady/12345/67890/",
                    video_title="Czech pilot", video_date_display="2026-07-07")

    def test_eye_then_czech_technical_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for corpus in ("eye", "czech"):
                source = self.make_source(root, corpus, [self.example(corpus)])
                result = module.stage(corpus, root=root)
                self.assertEqual(result["sourceSha256"], hashlib.sha256(source.read_bytes()).hexdigest())
                self.assertEqual(result["stagedRows"], 1)
                self.assertTrue(result["publicationBlocked"])
                self.assertFalse(result["approvedMetadataPublication"])
                self.assertFalse(result["mediaRightsVerified"])
                self.assertFalse(result["mediaPlaybackVerified"])
                record = result["records"][0]
                self.assertTrue(record["id"].startswith(corpus + "."))
                self.assertFalse(record["publicationApproved"])
                self.assertEqual(record["year"], "1922" if corpus == "eye" else "2026")
                self.assertEqual(record["mediaAccess"], "Não verificado pelo MAR")

    def test_reject_unsafe_hosts_and_wrong_institution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for corpus in ("eye", "czech"):
                row = self.example(corpus)
                row["video_link"] = "https://example.org/malicious"
                self.make_source(root, corpus, [row])
                with self.assertRaisesRegex(ValueError, "origin URL not allowed"):
                    module.stage(corpus, root=root)
                row = self.example(corpus)
                row["institution"] = "Other institution"
                self.make_source(root, corpus, [row])
                with self.assertRaisesRegex(ValueError, "institution mismatch"):
                    module.stage(corpus, root=root)

    def test_reject_duplicates_and_blank_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = self.example("eye")
            self.make_source(root, "eye", [row, row])
            with self.assertRaisesRegex(ValueError, "duplicate"):
                module.stage("eye", root=root)
            row["video_title"] = ""
            self.make_source(root, "eye", [row])
            with self.assertRaisesRegex(ValueError, "title missing"):
                module.stage("eye", root=root)

    def test_source_is_never_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root, "czech", [self.example("czech")])
            before = source.read_bytes()
            module.stage("czech", root=root)
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
