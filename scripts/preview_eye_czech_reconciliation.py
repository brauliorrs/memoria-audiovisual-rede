"""Run bounded OFFLINE Eye reconciliation or Czech episode triage.

Input is an operator-supplied JSON evidence file from a separately authorized
probe. The SHA pin must be supplied independently. This script never fetches
websites, writes output files, publishes records, or executes collectors.

Usage:
 python scripts/preview_eye_czech_reconciliation.py eye \
   --evidence-file /private/eye-sample.json --evidence-sha256 SHA64
 python scripts/preview_eye_czech_reconciliation.py czech \
   --evidence-file /private/czech-one-episode.json --evidence-sha256 SHA64
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from memoria_audiovisual.eye_czech_reconciliation import (
    ReconciliationRejected, reconcile_eye, screen_czech_episode,
)

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EYE_CSV = BASE_DIR / "data/output/eye_catalogo_videos_analitico.csv"
MAX_JSON = 2 * 1024 * 1024
MAX_CSV = 2 * 1024 * 1024


def preview(corpus: str, evidence_file: Path, expected_sha: str,
            *, eye_catalog: Path = DEFAULT_EYE_CSV) -> dict:
    if corpus not in ("eye", "czech"):
        raise ReconciliationRejected("unsupported_corpus")
    if (not evidence_file.is_file() or evidence_file.is_symlink()
            or evidence_file.stat().st_size > MAX_JSON):
        raise ReconciliationRejected("evidence_unavailable_or_oversized")
    raw = evidence_file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ReconciliationRejected("external_evidence_digest_mismatch")
    try:
        evidence = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ReconciliationRejected("evidence_json_invalid") from exc
    if not isinstance(evidence, dict) or evidence.get("corpus") != corpus:
        raise ReconciliationRejected("evidence_corpus_mismatch")
    if corpus == "czech":
        return screen_czech_episode(
            evidence.get("episode"), evidence_sha256=expected_sha,
            evidence_verified=True,
        )
    if (not eye_catalog.is_file() or eye_catalog.is_symlink()
            or eye_catalog.stat().st_size > MAX_CSV):
        raise ReconciliationRejected("eye_baseline_unavailable_or_oversized")
    try:
        with eye_catalog.open("r", encoding="utf-8-sig", newline="") as handle:
            original = list(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ReconciliationRejected("eye_baseline_invalid") from exc
    return reconcile_eye(
        original, evidence.get("records"),
        evidence_sha256=expected_sha, evidence_verified=True,
        sample_complete=evidence.get("sample_complete", False),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", choices=["eye", "czech"])
    parser.add_argument("--evidence-file", type=Path, required=True)
    parser.add_argument("--evidence-sha256", required=True)
    parser.add_argument("--eye-catalog", type=Path, default=DEFAULT_EYE_CSV)
    args = parser.parse_args(argv)
    try:
        report = preview(
            args.corpus, args.evidence_file, args.evidence_sha256,
            eye_catalog=args.eye_catalog,
        )
    except (ReconciliationRejected, OSError, TypeError, ValueError):
        print(json.dumps({
            "status": "HOLD", "publication_authorized": False,
            "production_gate": "HOLD",
        }))
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
