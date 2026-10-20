"""P0 offline encrypted KAVI checkpoint archive; explicit execute only.

No network access, no media files, no raw cursor in stdout and no permission to
resume Finna, publish a new index or alter institutional corpus membership.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for root in (ROOT, ROOT / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from memoria_audiovisual.kavi_finna_secure_backup import (
    BackupRejected, backup_verified_epoch, load_backup_key_from_environment,
    restore_verified_epoch,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline encrypted checkpoint backup or recovery.")
    parser.add_argument("operation", choices=("backup", "restore"))
    parser.add_argument("--source", type=Path, required=True,
                        help="Private staging epoch directory for backup; encrypted file for restore")
    parser.add_argument("--destination", type=Path, required=True,
                        help="Encrypted file for backup; NEW staging epoch directory for restore")
    parser.add_argument("--evidence-sha256", required=True)
    parser.add_argument("--expected-total", type=int, required=True)
    parser.add_argument("--epoch-id", required=True)
    parser.add_argument("--execute", action="store_true",
                        help="Required for any filesystem writes; never executes API access")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({
            "status": "dry_run",
            "operation": args.operation,
            "network_requests": 0,
            "media_downloaded": False,
            "promotion_authorized": False,
            "durability_verified": False,
        }, sort_keys=True))
        return 0
    try:
        key = load_backup_key_from_environment()
        if args.operation == "backup":
            result = backup_verified_epoch(
                args.source, args.destination,
                evidence_sha256=args.evidence_sha256,
                expected_total=args.expected_total,
                epoch_id=args.epoch_id, key=key,
            )
        else:
            result = restore_verified_epoch(
                args.source, args.destination,
                evidence_sha256=args.evidence_sha256,
                expected_total=args.expected_total,
                epoch_id=args.epoch_id, key=key,
            )
    except (BackupRejected, OSError, ValueError) as exc:
        # Never publish provider-controlled exception text, source paths,
        # filenames, key bytes, record IDs or opaque resumption tokens.
        print(json.dumps({
            "status": "rejected", "reason_class": type(exc).__name__,
            "network_requests": 0, "media_downloaded": False,
            "promotion_authorized": False, "durability_verified": False,
        }, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
