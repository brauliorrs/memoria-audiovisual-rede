#!/usr/bin/env python3
"""Fail-closed check that the web index is exactly the 200 approved KAVI fiches.

Checks SHA256 of the original CSV, publication status and each projected
source id/title/origin link. No network, API calls, media or DB required.
"""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/output/kavi_mar_metadata_links.csv"
MANIFEST = ROOT / "data/output/kavi_mar_metadata_links_manifest.json"
PUBLIC = ROOT / "site/data/kavi-public.json"


def run():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source_bytes = SOURCE.read_bytes()
    public = json.loads(PUBLIC.read_text(encoding="utf-8"))
    assert hashlib.sha256(source_bytes).hexdigest() == manifest["catalog_sha256"], "source_sha256"
    assert manifest["status"] == "published_partial_metadata", "unapproved_status"
    assert manifest["metadata_publication_approved"] is True, "unapproved_publication"
    assert manifest["coverage_status"] == "partial", "wrong_coverage"
    assert manifest["corpus_activation"] is False, "unsafe_corpus_activation"
    assert manifest["media_downloaded"] is False, "unsafe_media_download"
    assert manifest["viewing_at_origin_only"] is True, "unsafe_viewer"
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    records = public["records"]
    assert len(rows) == manifest["record_count"] == len(records) == public["total"] == 200, "count_mismatch"
    assert public["sourceCatalogSha256"] == manifest["catalog_sha256"], "site_digest_mismatch"
    assert public["scope"] == "partial_metadata_only", "scope_mismatch"
    assert public["approvedMetadataPublication"] is True, "no_metadata_approval"
    assert public["individualReview"] is False, "false_review_claim"
    assert public["mediaPlaybackVerified"] is False, "false_playback_claim"
    assert public["mediaRightsVerified"] is False, "false_rights_claim"
    ids, urls = set(), set()
    for original, shown in zip(rows, records):
        assert original["corpus"] == "fiaf-kavi", "unexpected_corpus"
        assert original["metadata_provider"] == "0/KAVI/", "unexpected_provider"
        assert original["source_service"] == "finna_api", "unexpected_source"
        assert original["record_review_status"] == "unreviewed", "false_record_review"
        assert original["media_access_status"] == "unverified", "false_media_access"
        assert original["media_rights_status"] == "not_verified", "false_media_rights"
        assert original["source_record_id"] == shown["id"], "id_change"
        assert original["video_title"].strip() == shown["title"], "title_change"
        assert (original["year"].strip() or None) == shown["year"], "year_change"
        assert original["source_record_url"] == shown["sourceUrl"] == original["video_link"], "url_change"
        assert original["genres"].strip() == shown["genres"], "genre_change"
        assert original["subjects"].strip() == shown["subjects"], "subject_change"
        url = urlparse(shown["sourceUrl"])
        assert url.scheme == "https" and url.netloc == "www.finna.fi", "non_source_link"
        assert url.path == "/Record/" + shown["id"], "forged_origin_path"
        assert shown["id"] not in ids and shown["sourceUrl"] not in urls, "duplicate"
        ids.add(shown["id"])
        urls.add(shown["sourceUrl"])
        assert shown["mediaAccess"] == "Não verificado", "false_playability"
    print("MAR site: 200 approved KAVI metadata fiches + source SHA-256 verified; 0 media claimed.")


if __name__ == "__main__":
    run()
