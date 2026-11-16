"""No-network tests for Eye/Czech incremental preview and release HOLD."""
from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.eye_czech_reconciliation import (
    ReconciliationRejected, reconcile_eye, screen_czech_episode,
)
from scripts.preview_eye_czech_reconciliation import preview, DEFAULT_EYE_CSV

SHA = "a" * 64
URL1 = "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/alpha"
URL2 = "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/beta"
URL3 = "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/gamma"
CZ = "https://www.ceskatelevize.cz/porady/151-kultura/226411033400703/"


def legacy(url, title="Álpha", desc="old"):
    return {
        "video_link": url, "video_title": title,
        "video_subject": "history", "video_description": desc,
        "video_published_at": "1936",
    }


def observed(url, rid, title="Álpha", desc="old"):
    return {
        "record_id": rid, "page_url": url, "title": title,
        "subject": "history", "description": desc, "date": "1936",
    }


class EyeCzechReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.baseline = [legacy(URL1), legacy(URL2, "Other")]

    def test_eye_new_changed_unchanged_and_not_observed(self):
        result = reconcile_eye(
            self.baseline, [
                observed(URL1, "alpha"),
                observed(URL2, "beta", title="Other", desc="revised"),
                observed(URL3, "gamma", title="Other"),
            ],
            evidence_sha256=SHA, evidence_verified=True,
        )
        self.assertEqual(result["counts"], {"new": 1, "changed": 1, "unchanged": 1})
        changed = next(x for x in result["changes"] if x["status"] == "changed")
        self.assertEqual(changed["changed_fields"], ["description"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["media_downloaded"])

    def test_partial_sample_cannot_delete_existing_records(self):
        result = reconcile_eye(
            self.baseline, [observed(URL1, "alpha")],
            evidence_sha256=SHA, evidence_verified=True,
            sample_complete=True,
        )
        self.assertEqual(result["not_observed_count"], 1)
        self.assertEqual(result["not_observed_meaning"], "absence_not_deletion")
        self.assertEqual(result["counts"]["unchanged"], 1)

    def test_identical_title_different_source_url_is_new(self):
        result = reconcile_eye(
            self.baseline, [observed(URL3, "gamma", "Álpha")],
            evidence_sha256=SHA, evidence_verified=True,
        )
        self.assertEqual(result["counts"]["new"], 1)

    def test_duplicate_record_ids_or_urls_rejected(self):
        cases = [
            [observed(URL1, "alpha"), observed(URL2, "alpha")],
            [observed(URL1, "alpha"), observed(URL1, "beta")],
        ]
        for items in cases:
            with self.subTest(items=items), self.assertRaises(ReconciliationRejected):
                reconcile_eye(self.baseline, items, evidence_sha256=SHA, evidence_verified=True)

    def test_bad_links_or_unverified_evidence_rejected(self):
        bad = [
            "http://filmdatabase.eyefilm.nl/en/collection/film-history/film/a",
            "https://example.org/en/collection/film-history/film/a",
            "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/a?download=1",
            "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/a#watch",
            "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/a.m3u8",
        ]
        for url in bad:
            with self.subTest(url=url), self.assertRaises(ReconciliationRejected):
                reconcile_eye(self.baseline, [observed(url, "a")],
                              evidence_sha256=SHA, evidence_verified=True)
        with self.assertRaises(ReconciliationRejected):
            reconcile_eye(self.baseline, [observed(URL1, "a")],
                          evidence_sha256=SHA, evidence_verified=False)

    def test_bounded_probe_and_unchanged_original(self):
        original = [dict(x) for x in self.baseline]
        reconcile_eye(self.baseline, [observed(URL1, "alpha")],
                      evidence_sha256=SHA, evidence_verified=True)
        self.assertEqual(self.baseline, original)
        with self.assertRaises(ReconciliationRejected):
            reconcile_eye(self.baseline, [observed(URL1, str(i)) for i in range(101)],
                          evidence_sha256=SHA, evidence_verified=True)

    def test_czech_one_episode_is_review_candidate_not_publication(self):
        rec = {
            "record_id": "226411033400703", "page_url": CZ,
            "title": "Festival", "description": "text", "subject": "culture",
            "date": "2026-07-07", "embedded": True,
        }
        result = screen_czech_episode(rec, evidence_sha256=SHA, evidence_verified=True)
        self.assertEqual(result["status"], "candidate_for_review")
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["playback_currently_verified"])
        self.assertFalse(result["media_rights_verified"])
        self.assertEqual(screen_czech_episode({}, evidence_sha256=SHA,
                                              evidence_verified=True)["status"], "HOLD")
        with self.assertRaises(ReconciliationRejected):
            screen_czech_episode(dict(rec, embedded=False),
                                 evidence_sha256=SHA, evidence_verified=True)

    def test_cli_pins_evidence_sha_without_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            baseline = folder / "eye.csv"
            with baseline.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(self.baseline[0]))
                writer.writeheader()
                writer.writerows(self.baseline)
            evidence = folder / "evidence.json"
            evidence.write_text(json.dumps({
                "corpus": "eye", "sample_complete": False,
                "records": [observed(URL1, "alpha")],
            }), encoding="utf-8")
            digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
            prior = baseline.read_bytes()
            result = preview("eye", evidence, digest, eye_catalog=baseline)
            self.assertEqual(result["counts"]["unchanged"], 1)
            self.assertEqual(prior, baseline.read_bytes())
            with self.assertRaises(ReconciliationRejected):
                preview("eye", evidence, "b" * 64, eye_catalog=baseline)

    def test_historical_eye_baseline_is_available_read_only(self):
        self.assertTrue(DEFAULT_EYE_CSV.is_file())
        with DEFAULT_EYE_CSV.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 630)


if __name__ == "__main__":
    unittest.main()
