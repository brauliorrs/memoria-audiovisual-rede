"""Bounded KAVI resumption probe and normalized provenance checks (no network)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.metadata_staging import (
    MetadataPage, StageRejected,
)
from scripts.probe_kavi_finna_two_page_resume import verify_two_pages


def film(identifier: str, *, rights="not_verified", provider="0/KAVI/"):
    return {
        "id": identifier,
        "title": "Example film",
        "formats": [{"value": "0/Video/", "translated": "Video"}],
        "provider_index_code": provider,
        "custody_status": "not_established",
        "media_rights_status": rights,
        "media_downloaded": False,
        "film_semantics": (
            "film_candidate" if identifier.startswith("kavi.elonet_elokuva_")
            else "unverified_audiovisual_record"
        ),
    }


def page(records, next_token):
    return MetadataPage(
        tuple(records),
        3,
        next_token,
        {
            "status": "OK",
            "resultCount": 3,
            "records": [
                {"id": r["id"], "title": r["title"]}
                for r in records
            ],
            "resumptionToken": (
                {"token": next_token, "expires": "2030-01-01T00:00:00Z"}
                if next_token else None
            ),
        },
    )


class Source:
    def __init__(self, *, second_override=None):
        self.scope = {
            "building_code": "0/KAVI/",
            "format_code": "0/Video/",
            "evidence_sha256": "a" * 64,
        }
        self.responses = {
            None: page([film("kavi.elonet_elokuva_1"),
                        film("kavi.elonet_elokuva_2")], "next-opaque"),
            "next-opaque": second_override or page(
                [film("another_video_id")], None
            ),
        }
        self.visited = []

    def preflight(self):
        return 3

    def fetch_page(self, token):
        self.visited.append(token)
        return self.responses[token]


class KaviResumeProbeTests(unittest.TestCase):
    def test_two_page_resume_and_redacted_provenance_audit(self):
        source = Source()
        with tempfile.TemporaryDirectory() as tmp:
            result = verify_two_pages(source, Path(tmp))
        self.assertEqual(source.visited, [None, "next-opaque"])
        self.assertTrue(result["resumption_verified"])
        self.assertEqual(result["first_page"]["record_count"], 2)
        self.assertEqual(result["after_resume"]["record_count"], 3)
        self.assertEqual(result["after_resume"]["page_count"], 2)
        self.assertEqual(result["integrity_audit"]["film_id_candidates"], 2)
        self.assertEqual(result["integrity_audit"]["other_video_records"], 1)
        self.assertEqual(
            result["integrity_audit"]["video_format_unconfirmed_records"], 0
        )
        self.assertEqual(
            len(result["integrity_audit"]["record_id_sequence_sha256"]), 64
        )
        self.assertFalse(result["promotion_authorized"])
        self.assertFalse(result["media_downloaded"])
        self.assertNotIn("next-opaque", str(result))

    def test_rights_claim_from_unapproved_source_is_rejected(self):
        source = Source(
            second_override=page(
                [film("kavi.elonet_elokuva_3", rights="licensed")], None
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                StageRejected, "audit_provenance_or_rights_violation"
            ):
                verify_two_pages(source, Path(tmp))

    def test_mismatched_provider_is_rejected(self):
        source = Source(
            second_override=page(
                [film("kavi.elonet_elokuva_3", provider="0/OTHER/")], None
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                StageRejected, "audit_provenance_or_rights_violation"
            ):
                verify_two_pages(source, Path(tmp))

    def test_repeated_id_does_not_complete_stage(self):
        source = Source(second_override=page(
            [film("kavi.elonet_elokuva_1")], None
        ))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                StageRejected, "duplicate_ids_across_pages"
            ):
                verify_two_pages(source, Path(tmp))

    def test_incorrect_response_origin_id_rejected(self):
        second = page([film("kavi.elonet_elokuva_3")], None)
        second.raw["records"][0]["id"] = "spoofed-other-record"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                StageRejected, "audit_source_to_normalized_ids_mismatch"
            ):
                verify_two_pages(Source(second_override=second), Path(tmp))


if __name__ == "__main__":
    unittest.main()
