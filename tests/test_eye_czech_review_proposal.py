"""Review proposal contract: deterministic, non-publishable, read-only source inputs."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.eye_czech_reconciliation import ReconciliationRejected
from scripts.build_eye_czech_review_proposal import (
    ADMISSION_FIELDS, PENDING_REVIEW, build_review_proposal, write_review_proposal,
)

EYE1 = "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/alpha"
EYE2 = "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/beta"
EYE3 = "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/gamma"
CZECH = "https://www.ceskatelevize.cz/porady/151-kultura/226411033400703/"


def eye_record(url, rid, title, description):
    return {
        "record_id": rid, "page_url": url, "title": title,
        "subject": "history", "description": description, "date": "1936",
    }


def write_eye_source(root):
    root = Path(root)
    baseline = root / "baseline.csv"
    with baseline.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "video_link", "video_title", "video_subject",
            "video_description", "video_published_at",
        ])
        writer.writeheader()
        writer.writerow({
            "video_link": EYE1, "video_title": "Alpha",
            "video_subject": "history", "video_description": "old",
            "video_published_at": "1936",
        })
        writer.writerow({
            "video_link": EYE2, "video_title": "Beta",
            "video_subject": "history", "video_description": "old",
            "video_published_at": "1936",
        })
    evidence = root / "eye.json"
    evidence.write_text(json.dumps({
        "corpus": "eye", "sample_complete": False,
        "records": [
            eye_record(EYE1, "alpha", "Alpha", "old"),
            eye_record(EYE2, "beta", "Beta", "changed"),
            eye_record(EYE3, "gamma", "Gamma", "fresh"),
        ],
    }), encoding="utf-8")
    return baseline, evidence, hashlib.sha256(evidence.read_bytes()).hexdigest()


class CandidatePackagingTests(unittest.TestCase):
    def test_eye_new_only_and_changed_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            baseline, evidence, sha = write_eye_source(folder)
            content, proposal = build_review_proposal(
                "eye", evidence, sha, eye_catalog=baseline,
            )
            rows = list(csv.DictReader(io.StringIO(content.decode())))
            self.assertEqual(len(rows), 1)
            self.assertEqual(tuple(rows[0]), ADMISSION_FIELDS)
            self.assertEqual(rows[0]["source_record_url"], EYE3)
            self.assertEqual(rows[0]["record_review_status"], PENDING_REVIEW)
            self.assertEqual(rows[0]["media_access_status"], "unverified")
            self.assertEqual(rows[0]["media_rights_status"], "not_verified")
            self.assertEqual(proposal["candidate_count"], 1)
            self.assertEqual(proposal["legacy_updates_requiring_separate_review"], 1)
            self.assertFalse(proposal["publication_authorized"])
            self.assertFalse(proposal["corpus_activation"])
            self.assertNotIn("approved_for_publication", proposal)
            self.assertEqual(proposal["candidate_csv_sha256"],
                             hashlib.sha256(content).hexdigest())
            self.assertEqual(build_review_proposal(
                "eye", evidence, sha, eye_catalog=baseline,
            ), (content, proposal))

    def test_eye_no_new_cannot_be_silently_promoted(self):
        with tempfile.TemporaryDirectory() as folder:
            baseline, evidence, sha = write_eye_source(folder)
            evidence.write_text(json.dumps({
                "corpus": "eye",
                "records": [eye_record(EYE1, "alpha", "Alpha", "old")],
            }), encoding="utf-8")
            sha = hashlib.sha256(evidence.read_bytes()).hexdigest()
            content, proposal = build_review_proposal(
                "eye", evidence, sha, eye_catalog=baseline,
            )
            self.assertEqual(len(list(csv.DictReader(io.StringIO(content.decode())))), 0)
            self.assertEqual(proposal["status"], "HOLD_no_new_admission")

    def test_czech_one_episode_only_with_approval_pending(self):
        with tempfile.TemporaryDirectory() as folder:
            evidence = Path(folder) / "czech.json"
            evidence.write_text(json.dumps({
                "corpus": "czech",
                "episode": {
                    "record_id": "226411033400703", "page_url": CZECH,
                    "title": "Festival", "description": "culture",
                    "subject": "film", "date": "2026-07-07",
                    "embedded": True,
                },
            }), encoding="utf-8")
            sha = hashlib.sha256(evidence.read_bytes()).hexdigest()
            content, proposal = build_review_proposal("czech", evidence, sha)
            rows = list(csv.DictReader(io.StringIO(content.decode())))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source_record_url"], CZECH)
            self.assertEqual(rows[0]["record_review_status"], PENDING_REVIEW)
            self.assertEqual(proposal["corpus"], "czech-television")
            self.assertEqual(proposal["production_gate"], "HOLD")
            evidence.write_text(json.dumps({"corpus": "czech", "episode": {}}))
            newsha = hashlib.sha256(evidence.read_bytes()).hexdigest()
            content2, p2 = build_review_proposal("czech", evidence, newsha)
            self.assertEqual(p2["candidate_count"], 0)
            self.assertEqual(p2["status"], "HOLD_no_new_admission")

    def test_evidence_digest_and_identity_must_match(self):
        with tempfile.TemporaryDirectory() as folder:
            baseline, evidence, sha = write_eye_source(folder)
            with self.assertRaises(ReconciliationRejected):
                build_review_proposal("eye", evidence, "f" * 64, eye_catalog=baseline)
            with self.assertRaises(ReconciliationRejected):
                build_review_proposal("czech", evidence, sha)

    def test_no_writes_inside_active_repo_data_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            baseline, evidence, sha = write_eye_source(folder)
            output = Path(folder) / "review-output"
            proposal = write_review_proposal(
                "eye", evidence, sha, output, eye_catalog=baseline,
            )
            self.assertEqual(proposal["candidate_count"], 1)
            self.assertTrue((output / "eye.candidate.csv").is_file())
            self.assertTrue((output / "eye.proposal.json").is_file())
            with self.assertRaises(ReconciliationRejected):
                write_review_proposal("eye", evidence, sha, output, eye_catalog=baseline)
            data_dir = Path(__file__).resolve().parents[1] / "data" / "output" / "mar_admitted" / "proposals-test"
            with self.assertRaises(ReconciliationRejected):
                write_review_proposal("eye", evidence, sha, data_dir, eye_catalog=baseline)

    def test_invalid_media_origin_never_enters_pending_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            baseline, evidence, sha = write_eye_source(folder)
            evidence.write_text(json.dumps({
                "corpus": "eye",
                "records": [eye_record(
                    "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/video.mp4",
                    "movie", "Movie", "stream",
                )],
            }))
            sha = hashlib.sha256(evidence.read_bytes()).hexdigest()
            with self.assertRaises(ReconciliationRejected):
                build_review_proposal("eye", evidence, sha, eye_catalog=baseline)


if __name__ == "__main__":
    unittest.main()
