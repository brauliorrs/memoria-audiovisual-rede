"""Falha se requirements.txt omitir dependências diretas do pyproject.toml."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY_NAME = re.compile(r"^[A-Za-z0-9_.-]+")


def normalized_name(specifier: str) -> str:
    match = DEPENDENCY_NAME.match(specifier.strip())
    if match is None:
        raise ValueError(f"dependência inválida: {specifier!r}")
    return match.group(0).lower().replace("_", "-").replace(".", "-")


def main() -> int:
    pyproject = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    direct = {
        normalized_name(item)
        for item in pyproject.get("project", {}).get("dependencies", [])
    }
    runtime = {
        normalized_name(line)
        for raw_line in (REPOSITORY_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if (line := raw_line.partition("#")[0].strip()) and not line.startswith(("-", "--"))
    }
    missing = sorted(direct - runtime)
    if missing:
        print(
            "requirements.txt omite dependências diretas de pyproject.toml: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    print("Manifestos de dependências alinhados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
