"""Offline admission tests: no corpus publishes solely because a crawler exists."""
from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.approved_corpus_admission import (
    AdmissionRejected, FIELDS, VERSION, load_all_approved_corpora,
    load_one_approved_corpus, load_admissions_with_individual_holds,
)

RUN = "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/12345"


def example_row(corpus="eye"):
    urls = {
        "eye": "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/item",
        "czech-television": "https://www.ceskatelevize.cz/porady/10000000000-program/",
        "ciclic": "https://memoire.ciclic.fr/films/1234",
        "asim": "https://www.europeanfilmgateway.eu/detail/1234",
        "bnfa": "https://www.europeanfilmgateway.eu/detail/5678",
    }
    return {
        "source_record_id": "unit:1",
        "source_record_url": urls[corpus],
        "video_title": "Fiche documentaire",
        "year": "1938", "authors": "", "subjects": "history",
        "languages": "", "genres": "", "video_description": "",
        "media_access_status": "unverified",
        "media_rights_status": "not_verified",
        "record_review_status": "approved_metadata_only",
    }


def write_pair(root, corpus="eye", *, row=None, manifest_change=None):
    dest = Path(root) / "mar_admitted"
    dest.mkdir(exist_ok=True)
    csv_path = dest / (corpus + ".csv")
    row = row or example_row(corpus)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)
    manifest = {
        "schema_version": VERSION, "corpus_code": corpus,
        "status": "approved_public_metadata",
        "approved_for_publication": True, "reviewer": "curator-1",
        "source_run_url": RUN, "observed_on": "2026-11-16",
        "record_count": 1, "catalog_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "media_downloaded": False, "viewing_at_origin_only": True,
        "corpus_activation": False,
    }
    manifest.update(manifest_change or {})
    (dest / (corpus + ".manifest.json")).write_text(json.dumps(manifest), encoding="utf-8")
    return csv_path


class IndividualCorpusAdmissionTests(unittest.TestCase):
    def test_no_automatic_publication_of_incomplete_sources(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(load_all_approved_corpora(root), {
                "eye": [], "czech-television": [], "ciclic": [], "asim": [], "bnfa": [],
            })
            with self.assertRaises(AdmissionRejected):
                load_one_approved_corpus(root, "ape")

    def test_valid_approved_origin_fiche(self):
        with tempfile.TemporaryDirectory() as root:
            write_pair(root)
            rows = load_one_approved_corpus(root, "eye")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["video_link"], example_row()["source_record_url"])
            self.assertEqual(rows[0]["media_access_status"], "unverified")
            self.assertEqual(rows[0]["source_service"], "mar_admitted_metadata")

    def test_all_supported_corpora_are_independently_gated(self):
        for code in ("eye", "czech-television", "ciclic", "asim", "bnfa"):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as root:
                write_pair(root, code)
                self.assertEqual(len(load_one_approved_corpus(root, code)), 1)

    def test_reject_unapproved_or_dishonest_manifest(self):
        for change in (
            {"approved_for_publication": False}, {"record_count": 2},
            {"reviewer": ""}, {"media_downloaded": True},
            {"corpus_activation": True}, {"catalog_sha256": "0" * 64},
            {"source_run_url": "https://example.com/claims/1"},
            {"observed_on": "not-a-date"},
        ):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as root:
                write_pair(root, manifest_change=change)
                with self.assertRaises(AdmissionRejected):
                    load_one_approved_corpus(root, "eye")

    def test_reject_media_and_other_domains(self):
        for url in (
            "https://www.evil.example/Record/1",
            "https://filmdatabase.eyefilm.nl/video/movie.mp4",
            "https://filmdatabase.eyefilm.nl/stream/playlist.m3u8",
            "https://filmdatabase.eyefilm.nl/record/1?download=1",
            "https://filmdatabase.eyefilm.nl/record/1#play",
            "http://filmdatabase.eyefilm.nl/record/1",
        ):
            with self.subTest(url=url), tempfile.TemporaryDirectory() as root:
                write_pair(root, row={**example_row(), "source_record_url": url})
                with self.assertRaises(AdmissionRejected):
                    load_one_approved_corpus(root, "eye")

    def test_manifest_missing_pair_or_corrupted_bytes_is_hold(self):
        with tempfile.TemporaryDirectory() as root:
            p = write_pair(root)
            p.write_bytes(p.read_bytes() + b"invalid")
            with self.assertRaises(AdmissionRejected):
                load_one_approved_corpus(root, "eye")
        with tempfile.TemporaryDirectory() as root:
            p = write_pair(root)
            p.unlink()
            with self.assertRaises(AdmissionRejected):
                load_one_approved_corpus(root, "eye")

    def test_cannot_publish_falsely_playable_or_reviewed_record(self):
        for key, value in (("media_access_status", "verified_public_playback"),
                           ("media_rights_status", "public_domain"),
                           ("record_review_status", "unreviewed")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as root:
                write_pair(root, row={**example_row(), key: value})
                with self.assertRaises(AdmissionRejected):
                    load_one_approved_corpus(root, "eye")

    def test_invalid_corpus_is_held_without_suppressing_healthy_corpora(self):
        with tempfile.TemporaryDirectory() as root:
            bad = write_pair(root, "eye")
            write_pair(root, "czech-television")
            bad.write_bytes(bad.read_bytes() + b"tampered")
            admitted, holds = load_admissions_with_individual_holds(root)
            self.assertEqual(admitted["eye"], [])
            self.assertEqual(len(admitted["czech-television"]), 1)
            self.assertIn("eye", holds)
            self.assertNotIn("czech-television", holds)
            self.assertEqual(admitted["asim"], [])

    def test_no_fallback_to_unvalidated_legacy_csv(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "eye_catalogo_videos_analitico.csv").write_text("malicious")
            self.assertEqual(load_one_approved_corpus(root, "eye"), [])


if __name__ == "__main__":
    unittest.main()
