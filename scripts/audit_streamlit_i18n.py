from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


STREAMLIT_TEXT_CALLS = {
    "title", "header", "subheader", "markdown", "caption", "info", "warning",
    "error", "success", "write", "button", "download_button", "link_button",
    "checkbox", "toggle", "radio", "selectbox", "multiselect", "text_input",
    "text_area", "number_input", "date_input", "time_input", "slider",
    "select_slider", "file_uploader", "metric", "expander", "tabs",
}
I18N_SAFE_CALLS = {"tr", "t", "localize_ui", "localize_dataframe_columns"}

LANGUAGE_MARKERS = {
    "pt": {
        "aberta", "para", "observação", "comparativa", "visibilidade", "acesso",
        "circulação", "acervos", "audiovisuais", "pergunta", "científica", "provisória",
        "condições", "institucionais", "técnicas", "culturais", "próximos", "ajustes",
        "implementado", "adaptação", "desenvolver", "evidência", "estado", "plataforma",
    },
    "en": {
        "open", "platform", "observation", "comparative", "visibility", "access",
        "circulation", "archives", "audiovisual", "research", "question", "scientific",
        "provisional", "conditions", "institutional", "technical", "cultural", "next",
        "adjustments", "implemented", "adapted", "developed", "evidence", "status",
    },
    "es": {
        "abierta", "para", "observación", "comparativa", "visibilidad", "acceso",
        "circulación", "archivos", "audiovisuales", "pregunta", "científica", "provisional",
        "condiciones", "institucionales", "técnicas", "culturales", "próximos", "ajustes",
        "implementado", "adaptación", "desarrollar", "evidencia", "estado", "plataforma",
    },
}
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", re.UNICODE)


@dataclass(frozen=True)
class Finding:
    path: str
    page: str
    line: int
    kind: str
    severity: str
    call: str
    text: str
    languages: tuple[str, ...] = ()


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _is_i18n_wrapped(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _call_name(node.func) in I18N_SAFE_CALLS


def _literal_strings(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        return [part.value for part in node.values if isinstance(part, ast.Constant) and isinstance(part.value, str)]
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values: list[str] = []
        for element in node.elts:
            values.extend(_literal_strings(element))
        return values
    if isinstance(node, ast.Dict):
        values: list[str] = []
        for value in node.values:
            values.extend(_literal_strings(value))
        return values
    return []


def _page_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    if relative.parts[:1] == ("app",):
        return relative.stem.replace("streamlit_", "").replace("_", " ").title()
    return relative.stem.replace("_", " ").title()


def _detect_languages(text: str) -> tuple[str, ...]:
    tokens = {token.lower() for token in TOKEN_RE.findall(text)}
    scores = {language: len(tokens & markers) for language, markers in LANGUAGE_MARKERS.items()}
    detected = tuple(sorted(language for language, score in scores.items() if score >= 2))
    return detected


def _compact(text: str) -> str:
    return " ".join(text.split())[:300]


def audit_file(path: Path, root: Path) -> list[Finding]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    relative = str(path.relative_to(root)).replace("\\", "/")
    page = _page_name(path, root)
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call = _call_name(node.func)
            if call in STREAMLIT_TEXT_CALLS and node.args:
                first_arg = node.args[0]
                if not _is_i18n_wrapped(first_arg):
                    literals = _literal_strings(first_arg)
                    if literals:
                        for text in literals:
                            compact = _compact(text)
                            if compact:
                                findings.append(Finding(relative, page, node.lineno, "unwrapped_public_text", "high", call, compact))
                    elif isinstance(first_arg, (ast.Name, ast.Attribute, ast.JoinedStr, ast.BinOp)):
                        findings.append(Finding(relative, page, node.lineno, "dynamic_public_text", "medium", call, ast.unparse(first_arg)[:300]))

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            compact = _compact(node.value)
            if len(compact.split()) < 4:
                continue
            languages = _detect_languages(compact)
            if len(languages) >= 2:
                findings.append(Finding(relative, page, node.lineno, "hybrid_language", "high", "string", compact, languages))

    unique: dict[tuple, Finding] = {}
    for finding in findings:
        key = (finding.path, finding.line, finding.kind, finding.call, finding.text)
        unique[key] = finding
    return list(unique.values())


def run(root: Path) -> list[Finding]:
    targets = [
        root / "app",
        root / "src" / "memoria_audiovisual" / "research_profile.py",
    ]
    findings: list[Finding] = []
    for target in targets:
        if target.is_file():
            findings.extend(audit_file(target, root))
        elif target.exists():
            for path in sorted(target.rglob("*.py")):
                findings.extend(audit_file(path, root))
    return sorted(findings, key=lambda item: (item.page, item.path, item.line, item.kind))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = run(root)
    print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
