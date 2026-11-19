#!/usr/bin/env python3
"""Pin the exact reviewed Git SHA of scientific sources used by static MAR slices."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "site/lib/research-snapshot.ts"
DECLARATION = re.compile(
    r'export const researchSnapshotCommit = "[0-9a-f]{40}" as const;'
)


def pin(source_sha: str, path: Path = DESTINATION) -> bool:
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("source revision must be a full 40-character Git SHA")
    original = path.read_text(encoding="utf-8")
    replacement = f'export const researchSnapshotCommit = "{source_sha}" as const;'
    content, changed = DECLARATION.subn(replacement, original)
    if changed != 1:
        raise ValueError("research-snapshot.ts has an unknown provenance contract")
    if original == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True, help="the reviewed main commit containing the CSV source revision")
    args = parser.parse_args()
    try:
        changed = pin(args.source_sha)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"MAR provenance HOLD: {exc}\n")
    print(f"MAR scientific source revision: {args.source_sha}; modified={changed}")


if __name__ == "__main__":
    main()
