"""Read-only check for the published KAVI metadata-only index. No API calls."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from memoria_audiovisual.kavi_finna_public_catalog import PublicationRejected
from memoria_audiovisual.kavi_finna_registry import load_kavi_metadata_index_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a previously published KAVI/Kuvi metadata index, offline.")
    parser.add_argument("--directory", type=Path, default=ROOT / "data" / "output")
    args = parser.parse_args(argv)
    try:
        summary = load_kavi_metadata_index_summary(args.directory)
        if not summary:
            raise PublicationRejected("metadata_index_not_published")
    except (PublicationRejected, AssertionError, OSError, ValueError) as exc:
        print(json.dumps({"status": "rejected", "error_class": type(exc).__name__,
                          "media_downloaded": False, "corpus_activation": False}, sort_keys=True))
        return 2
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
