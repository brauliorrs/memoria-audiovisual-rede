from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "digital-infrastructure-alignment"


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    severity: str
    rule: str
    excerpt: str


BLOCKING_PATTERNS = {
    "deprecated_indicator_catalog_path": re.compile(
        r"data/templates/analytics/indicator_catalog\.json", re.IGNORECASE
    ),
    "translated_detection_as_fact": re.compile(
        r"(?:ausência de detecção|não detectad[oa]).{0,80}(?:comprova|confirma|demonstra) ausência",
        re.IGNORECASE,
    ),
    "ai_non_detection_as_absence": re.compile(
        r"(?:não foi detectad[oa]|nenhuma evidência foi encontrada).{0,80}(?:não usa|não utiliza|ausência de) (?:IA|inteligência artificial)",
        re.IGNORECASE,
    ),
}

WARNING_PATTERNS = {
    "provisional_branch_reference": re.compile(
        r"(?:presentation/rpv-1|feature/fase)", re.IGNORECASE
    ),
    "pull_request_reference": re.compile(r"\bPR\s*#?\d+\b", re.IGNORECASE),
    "future_module_language": re.compile(r"\bmódulos? futuros?\b", re.IGNORECASE),
    "legacy_state_technology_term": re.compile(r"Estado[–-]tecnologia", re.IGNORECASE),
}

REQUIRED_SECTIONS = {
    "README.md": ("## Limite interpretativo", "## Estado atual"),
    "technical_implementation_roadmap.md": ("## Fase 5 — indicadores", "## Próximo portão técnico"),
    "indicator_catalog.md": ("## Status deste documento", "## Regra de ativação"),
    "ai_systems_protocol.md": ("## Estados avaliativos", "## Relação com indicadores"),
    "module_mapping.md": ("## Fluxo arquitetural", "## Regras permanentes"),
}


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def compact(value: str) -> str:
    return " ".join(value.split())[:240]


def audit_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(ROOT).as_posix()
    findings: list[Finding] = []

    for rule, pattern in BLOCKING_PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(
                Finding(relative, line_number(text, match.start()), "error", rule, compact(match.group(0)))
            )

    for rule, pattern in WARNING_PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(
                Finding(relative, line_number(text, match.start()), "warning", rule, compact(match.group(0)))
            )

    required = REQUIRED_SECTIONS.get(path.name, ())
    for heading in required:
        if heading not in text:
            findings.append(Finding(relative, 1, "error", "missing_required_section", heading))

    return findings


def run() -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        findings.extend(audit_file(path))
    return findings


def main() -> int:
    findings = run()
    print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    print(f"\nDigital-infrastructure documentation audit: {len(errors)} errors, {len(warnings)} warnings.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
