"""Offline, fail-closed audit of a local KAVI/Finna metadata checkpoint.

No HTTP requests, media fetching, or writes to the corpus. The only temporary
write is the cooperative run.lock, shared with the staged metadata collector.
Inputs must include an independently supplied scope evidence digest and total.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from memoria_audiovisual.digital_infrastructure.locking import FileWriteLock
from memoria_audiovisual.kavi_finna_adapter import FinnaScope
from memoria_audiovisual.metadata_staging import (
    StageRejected, _digest, _restore, public_stage_summary,
)
from scripts.probe_kavi_finna_two_page_resume import _audit_normalized_rows


def audit_finna_staging(
    directory: str | Path,
    *,
    evidence_sha256: str,
    expected_total: int,
) -> dict[str, Any]:
    """Verify locally staged pages and source-to-normalized provenance.

    The count and fingerprint come from the caller, not from the checkpoint.
    Complete means cursor exhaustion with matching counts, NOT custody, rights
    verification, record admission, or an independently frozen API snapshot.
    """
    if (
        not isinstance(expected_total, int)
        or isinstance(expected_total, bool)
        or expected_total < 0
    ):
        raise ValueError("expected_total_must_be_nonnegative_integer")

    scope = FinnaScope(
        building_code="0/KAVI/",
        format_code="0/Video/",
        evidence_sha256=evidence_sha256,
    ).to_dict()
    directory = Path(directory)
    if not directory.is_dir() or not (directory / "checkpoint.json").is_file():
        raise StageRejected("offline_checkpoint_missing")

    with FileWriteLock(directory / "run", timeout=10):
        try:
            checkpoint = json.loads(
                (directory / "checkpoint.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            raise StageRejected("offline_checkpoint_invalid") from exc
        if not isinstance(checkpoint, dict):
            raise StageRejected("offline_checkpoint_not_object")

        # Full replay of every SHA-256 addressed raw artifact, cursor-chain,
        # count, scope, and the mandatory false promotion/media flags.
        _restore(directory, checkpoint, _digest(scope), expected_total)

        # Reuse the reviewed, two-page-live-proven normalized/source audit.
        # No source.fetch_page() or source.preflight() is invoked here.
        provenance = _audit_normalized_rows(
            directory, checkpoint, SimpleNamespace(scope=scope)
        )

    return {
        **public_stage_summary(checkpoint),
        "offline_integrity_verified": True,
        "api_snapshot_freshness_verified": False,
        "provenance_audit": provenance,
        "promotion_authorized": False,
        "media_downloaded": False,
        "note": (
            "Local checkpoint only; neither full catalogue enumeration nor "
            "custody, licence, or snapshot freshness is established."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit already staged KAVI metadata OFFLINE, without network"
    )
    parser.add_argument(
        "--directory", type=Path,
        default=ROOT / "data" / "staging" / "kavi-finna",
    )
    parser.add_argument("--evidence-sha256", required=True)
    parser.add_argument(
        "--expected-total", type=int, required=True,
        help="Count independently captured in the authorized preflight",
    )
    args = parser.parse_args(argv)
    try:
        report = audit_finna_staging(
            args.directory,
            evidence_sha256=args.evidence_sha256,
            expected_total=args.expected_total,
        )
    except (ValueError, StageRejected) as exc:
        # Errors contain only stable rejection codes, never cursor values.
        print(json.dumps({
            "audit_status": "rejected",
            "reason": str(exc),
            "promotion_authorized": False,
            "media_downloaded": False,
        }, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
