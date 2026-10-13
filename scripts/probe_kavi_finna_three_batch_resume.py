"""Three explicitly bounded KAVI/Finna metadata-only resume batches.

Each of three stage executions requests at most one page. The checkpoint
survives between calls but lives only in a disposable local directory. An
explicit opt-in permits a single continuation per timezone-naive token,
with the server as authority; no automatic retry or reset.
Never publishes raw metadata, opaque cursors, individual IDs, or media URLs.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import requests

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from memoria_audiovisual.config import HEADERS
from memoria_audiovisual.kavi_elonet_probe import USER_AGENT
from memoria_audiovisual.kavi_finna_adapter import FinnaMetadataSource, FinnaScope
from memoria_audiovisual.metadata_staging import MetadataPageSource, StageRejected
from scripts.kavi_finna_batch_gate import execute_verified_batch

BATCHES = 3
DELAY_SECONDS = 1.0


def _safe_snapshot(report: dict) -> dict:
    """Keep only bounded public fields; no cursor or source metadata."""
    return {
        "page_count": report["page_count"],
        "record_count": report["record_count"],
        "expected_total": report["expected_total"],
        "status": report["status"],
        "scope_sha256": report["scope_sha256"],
        "offline_integrity_verified": report["offline_integrity_verified"],
        "api_snapshot_freshness_verified": False,
        "promotion_authorized": False,
        "media_downloaded": False,
    }


def verify_three_batches(
    source: MetadataPageSource,
    directory: str | Path,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict:
    """One initial and two resume calls, with exactly one page per call.

    Uses the result of the first *live preflight* as the independent expected
    total for subsequent runs, never reading that anchor from the checkpoint.
    Fail closed on drifting result counts, expired cursors or changed scope.
    """
    summaries: list[dict] = []
    latest: dict | None = None
    expected: int | None = None

    for batch_no in range(1, BATCHES + 1):
        report = execute_verified_batch(
            source, directory, max_pages=1,
            resume=batch_no != 1,
            expected_total=expected,
            delay_seconds=DELAY_SECONDS,
            expiry_margin_seconds=30.0,
            allow_naive_server_validation=True,
            sleep_fn=sleep_fn, now_fn=now_fn,
        )
        current = _safe_snapshot(report)
        if current["promotion_authorized"] is not False or current["media_downloaded"] is not False:
            raise StageRejected("three_batch_safety_flag_violation")
        if current["offline_integrity_verified"] is not True:
            raise StageRejected("three_batch_offline_audit_not_verified")
        if current["page_count"] != batch_no:
            raise StageRejected("three_batch_page_sequence_invalid")
        if batch_no == 1:
            expected = current["expected_total"]
            if current["status"] != "partial":
                raise StageRejected("three_batch_first_page_not_partial")
        else:
            assert latest is not None and expected is not None
            if (
                current["record_count"] <= latest["record_count"]
                or current["expected_total"] != expected
                or current["scope_sha256"] != latest["scope_sha256"]
            ):
                raise StageRejected("three_batch_continuation_inconsistent")
            if batch_no < BATCHES and current["status"] != "partial":
                raise StageRejected("three_batch_ended_before_third_page")
        summaries.append(current)
        latest = current

    assert latest is not None
    audit = report["provenance_audit"]
    return {
        "probe": "kavi_finna_three_bounded_batches",
        "verified_page_count": BATCHES,
        "batch_summaries": summaries,
        "final_record_count": latest["record_count"],
        "expected_total": latest["expected_total"],
        "record_id_sequence_sha256": audit["record_id_sequence_sha256"],
        "film_id_candidates": audit["film_id_candidates"],
        "other_video_records": audit["other_video_records"],
        "video_format_unconfirmed_records": audit["video_format_unconfirmed_records"],
        "resumption_verified_across_batches": True,
        "api_snapshot_freshness_verified": False,
        "promotion_authorized": False,
        "media_downloaded": False,
        "note": (
            "Only three bounded metadata pages in one ephemeral job; no "
            "claim of full enumeration, long-lived checkpoint durability, "
            "custody, film licensing or corpus admission."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Three one-page live Finna staging batches; never media/promotion"
    )
    parser.add_argument("--evidence-sha256", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    scope = FinnaScope("0/KAVI/", "0/Video/", args.evidence_sha256)
    if not args.execute:
        print("DRY RUN: exactly three one-page metadata staging batches; no HTTP or media.")
        return 0
    with requests.Session() as session, tempfile.TemporaryDirectory(
        prefix="kavi-three-batch-"
    ) as folder:
        session.headers.update({
            **HEADERS,
            "User-Agent": f"{USER_AGENT}/1.0 (+metadata-only-three-batch-probe)",
            "Accept": "application/json",
        })
        try:
            report = verify_three_batches(FinnaMetadataSource(session, scope), folder)
        except (StageRejected, ValueError) as exc:
            # Stable rejection codes only: no opaque token, record ID or URL.
            print(json.dumps({
                "probe": "kavi_finna_three_bounded_batches",
                "status": "HOLD",
                "reason": str(exc),
                "promotion_authorized": False,
                "media_downloaded": False,
            }, sort_keys=True))
            return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
