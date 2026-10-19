"""Offline Finna-to-MAR link-only preview; never requests API or activates corpus."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "src"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from memoria_audiovisual.kavi_finna_mar_index import project_staged_catalog
from memoria_audiovisual.metadata_staging import StageRejected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Project an existing audited Finna metadata staging into a link-only MAR REVIEW preview"
    )
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--evidence-sha256", required=True)
    parser.add_argument("--expected-total", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        result = project_staged_catalog(
            args.directory, args.output_directory,
            evidence_sha256=args.evidence_sha256,
            expected_total=args.expected_total,
        )
    except (OSError, ValueError, StageRejected) as exc:
        # Do not log exception strings because files could contain raw URLs
        # or opaque API tokens. Use a stable redacted failure category.
        print(json.dumps({
            "status": "rejected",
            "error_class": type(exc).__name__,
            "promotion_authorized": False,
            "media_downloaded": False,
        }))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
