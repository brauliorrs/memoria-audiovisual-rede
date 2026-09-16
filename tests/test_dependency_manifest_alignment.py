from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY_NAME = re.compile(r"^[A-Za-z0-9_.-]+")


def _normalized_name(specifier: str) -> str:
    match = DEPENDENCY_NAME.match(specifier.strip())
    if match is None:
        raise ValueError(f"dependência inválida: {specifier!r}")
    return match.group(0).lower().replace("_", "-").replace(".", "-")


class DependencyManifestAlignmentTests(unittest.TestCase):
    def test_requirements_declares_every_direct_project_dependency(self) -> None:
        pyproject = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        project_dependencies = {
            _normalized_name(item)
            for item in pyproject.get("project", {}).get("dependencies", [])
        }

        requirement_dependencies = {
            _normalized_name(line)
            for raw_line in (REPOSITORY_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if (line := raw_line.partition("#")[0].strip()) and not line.startswith(("-", "--"))
        }

        missing = sorted(project_dependencies - requirement_dependencies)
        self.assertEqual(
            missing,
            [],
            "requirements.txt omite dependências diretas declaradas em pyproject.toml: "
            + ", ".join(missing),
        )


if __name__ == "__main__":
    unittest.main()
