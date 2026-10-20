"""Generate or verify KAVI/Kuvi metadata reports from an approved offline snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "src"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from memoria_audiovisual.kavi_finna_metadata_reports import (
    build_kavi_metadata_reports,
    serialize_kavi_metadata_reports,
    write_kavi_metadata_reports,
)
from memoria_audiovisual.kavi_finna_public_catalog import (
    PublicationRejected, load_published_kavi_rows,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline, metadata-only KAVI reporting; never downloads media."
    )
    parser.add_argument("--source-directory", type=Path, default=ROOT / "data" / "output")
    parser.add_argument("--output-directory", type=Path, default=ROOT / "data" / "output")
    parser.add_argument(
        "--check", action="store_true",
        help="Compare derived files byte-for-byte with approved source (read-only).",
    )
    args = parser.parse_args(argv)
    try:
        if args.check:
            rows, manifest = load_published_kavi_rows(args.source_directory)
            report = build_kavi_metadata_reports(rows, manifest)
            expected = serialize_kavi_metadata_reports(report)
            for name, expected_bytes in expected.items():
                actual = args.output_directory / name
                if not actual.is_file() or actual.read_bytes() != expected_bytes:
                    raise PublicationRejected("metadata_report_missing_or_stale")
        else:
            report = write_kavi_metadata_reports(
                args.source_directory, args.output_directory,
            )
            expected = serialize_kavi_metadata_reports(report)
    except (PublicationRejected, OSError, ValueError) as exc:
        print(json.dumps({
            "status": "rejected",
            "error_class": type(exc).__name__,
            "media_downloaded": False, "corpus_activation": False,
        }, sort_keys=True))
        return 2
    print(json.dumps({
        "status": "verified" if args.check else "generated",
        "reports": {
            name: hashlib.sha256(contents).hexdigest()
            for name, contents in expected.items()
        },
        "records": report["summary"]["indexed_metadata_records"],
        "source_item_links": report["summary"]["source_record_links"],
        "coverage_status": report["summary"]["coverage_status"],
        "media_downloaded": False, "corpus_activation": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
