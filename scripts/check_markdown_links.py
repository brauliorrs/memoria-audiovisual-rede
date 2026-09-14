from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#")


def markdown_files() -> list[Path]:
    excluded = {".git", ".venv", "venv", "node_modules"}
    return [
        path
        for path in ROOT.rglob("*.md")
        if not any(part in excluded for part in path.parts)
    ]


def clean_target(raw_target: str) -> str:
    target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
    return unquote(target)


def target_exists(source: Path, target: str) -> bool:
    if not target or target.startswith(SKIP_PREFIXES):
        return True

    parsed = urlparse(target)
    path_part = parsed.path
    if not path_part:
        return True

    candidate = (source.parent / path_part).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return False

    return candidate.exists()


def main() -> int:
    failures: list[tuple[Path, str]] = []

    for source in markdown_files():
        text = source.read_text(encoding="utf-8-sig")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = clean_target(match.group(1))
            if not target_exists(source, target):
                failures.append((source.relative_to(ROOT), target))

    if failures:
        print("Broken internal Markdown links found:")
        for source, target in failures:
            print(f"- {source}: {target}")
        return 1

    print(f"Internal Markdown links valid across {len(markdown_files())} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
