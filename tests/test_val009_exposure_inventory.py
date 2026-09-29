"""Offline, synthetic tests of the VAL-009 development exposure inventory.

No real site requests, classifier calls, frozen prediction changes, or seals.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location(
    "audit_val009_exposure", BASE / "scripts" / "audit_val009_exposure.py"
)
assert MODULE and MODULE.loader
audit = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(audit)
INVENTORY = json.loads(
    (BASE / "data" / "digital_infrastructure" / "ai_experiments"
     / "m3_surface_type_exposure_inventory_v2_3_draft.json").read_text()
)


def dump(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def make_synthetic_checkout(root, doc):
    """Fabricate 117 reviewed + 20 extra URLs with hashes matching THIS test."""
    known_urls = [f"https://example.org/known/{i}" for i in range(117)]
    base = doc["original_exclusion_manifest"]
    base_bytes = dump({
        "status": "draft_not_frozen", "units_total": 117,
        "urls_total": 117, "urls": known_urls,
    })
    old_path = root / base["path"]
    old_path.parent.mkdir(parents=True, exist_ok=True)
    old_path.write_bytes(base_bytes)
    base["sha256"] = audit.sha256(base_bytes)
    offset = 0
    for source in base["source_files"]:
        urls = known_urls[offset:offset + source["units"]]
        offset += source["units"]
        key = "url" if source["path"].startswith("tests/") else "page_url"
        payload = dump({
            "units" if key == "url" else "reviewed_units":
                [{key: url} for url in urls],
        })
        file = root / source["path"]
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(payload)
        source["sha256"] = audit.sha256(payload)
    by_index = {
        (x["source_report_path"], x["source_page_index"]): x
        for x in doc["additional_confirmed_historical_pages"]
    }
    known_cursor = 0
    for report in doc["historical_discovery_reports"]:
        pages = []
        for index in range(report["pages_total"]):
            row = by_index.get((report["path"], index))
            if row is not None:
                url = row["url"]
                stamp = row["observed_at"]
                parent = row["parent_url"]
                body_hash = row["reported_page_content_sha256"]
            else:
                url = known_urls[known_cursor]
                known_cursor += 1
                stamp = "2026-08-25T10:00:00Z"
                parent = None
                body_hash = audit.sha256(url.encode())
            pages.append({
                "url": url, "fetched_at": stamp, "parent_url": parent,
                "content_sha256": body_hash, "fetch_status": "fetched",
            })
        payload = dump({"pages": pages})
        path = root / report["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        report["sha256"] = audit.sha256(payload)
        for index in range(len(pages)):
            row = by_index.get((report["path"], index))
            if row is not None:
                row["source_report_sha256"] = report["sha256"]
    assert known_cursor == 102
    groups = {}
    for fixture in doc["nonvalidated_fixture_literals"]:
        groups.setdefault(fixture["source_path"], []).append(fixture)
    for path, rows in groups.items():
        payload = ("\n".join(item["url"] for item in rows) + "\n").encode("utf-8")
        f = root / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(payload)
        digest = audit.sha256(payload)
        blob_sha = hashlib.sha1(
            b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
        ).hexdigest()
        for item in rows:
            item["source_sha256"] = digest
            item["source_git_blob_sha"] = blob_sha


class ExposureInventoryTests(unittest.TestCase):
    def test_draft_structure_is_never_mistaken_for_scientific_seal(self):
        result = audit.validate_inventory(INVENTORY)
        self.assertEqual(result["baseline_reviewed_units"], 117)
        self.assertEqual(result["additional_observed_pages"], 20)
        self.assertEqual(result["fixture_literals_require_review"], 22)
        self.assertEqual(result["status"], "draft_verified_not_sealed")

    def test_url_identity_does_not_conflate_distinct_paths_or_queries(self):
        self.assertEqual(
            audit.url_identity("HTTPS://EXAMPLE.ORG:443/Film?b=2&a=1#fragment"),
            "https://example.org/Film?b=2&a=1",
        )
        self.assertNotEqual(audit.url_identity("https://example.org/Film"),
                            audit.url_identity("https://example.org/film"))
        self.assertNotEqual(audit.url_identity("https://example.org/?a=1&b=2"),
                            audit.url_identity("https://example.org/?b=2&a=1"))
        for bad in ("ftp://example.org/", "https://u:p@example.org/",
                    "https://example.org:bad/"):
            with self.subTest(url=bad), self.assertRaises(audit.AuditError):
                audit.url_identity(bad)

    def test_manifest_mutations_and_fixture_promotions_abort(self):
        changes = (
            lambda x: x["historical_discovery_reports"][0].update(sha256="bad"),
            lambda x: x["additional_confirmed_historical_pages"].pop(),
            lambda x: x["nonvalidated_fixture_literals"][0].update(auto_exclusion=True),
            lambda x: x.update(status="sealed"),
            lambda x: x["additional_confirmed_historical_pages"][0].update(
                final_url="https://example.org/assumed"
            ),
            lambda x: x["historical_discovery_reports"].append(
                x["historical_discovery_reports"][0].copy()
            ),
        )
        for edit in changes:
            candidate = copy.deepcopy(INVENTORY)
            edit(candidate)
            with self.assertRaises(audit.AuditError):
                audit.validate_inventory(candidate)

    def test_full_offline_synthetic_checkout_and_draft_preview(self):
        doc = copy.deepcopy(INVENTORY)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_synthetic_checkout(root, doc)
            with self.assertRaises(audit.AuditError):
                audit.audit_historical_checkout(doc, root)
            result = audit.audit_historical_checkout(
                doc, root, allow_unversioned_synthetic=True,
            )
            self.assertEqual(result["distinct_exact_exclusions"], 137)
            self.assertFalse(result["old_reports_raw_http_bytes_verified"])
            # Production preview requires a pinned Git checkout; it must NOT
            # accept an unversioned synthetic folder as a scientific source.
            with self.assertRaises(audit.AuditError):
                audit.build_draft_exclusions(doc, root)
            first = doc["historical_discovery_reports"][0]
            f = root / first["path"]
            f.write_bytes(f.read_bytes() + b"\n")
            with self.assertRaises(audit.AuditError):
                audit.audit_historical_checkout(
                    doc, root, allow_unversioned_synthetic=True,
                )

    def test_missing_real_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(audit.AuditError):
                audit.audit_historical_checkout(INVENTORY, Path(tmp))


if __name__ == "__main__":
    unittest.main()
