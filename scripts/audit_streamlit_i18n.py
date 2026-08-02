from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path


STREAMLIT_TEXT_CALLS = {
    "title",
    "header",
    "subheader",
    "markdown",
    "caption",
    "info",
    "warning",
    "error",
    "success",
    "write",
    "button",
    "download_button",
    "link_button",
    "checkbox",
    "toggle",
    "radio",
    "selectbox",
    "multiselect",
    "text_input",
    "text_area",
    "number_input",
    "date_input",
    "time_input",
    "slider",
    "select_slider",
    "file_uploader",
    "metric",
    "expander",
    "tabs",
}

I18N_SAFE_CALLS = {"tr", "t", "localize_ui"}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    call: str
    text: str


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
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values: list[str] = []
        for element in node.elts:
            values.extend(_literal_strings(element))
        return values
    return []


def audit_file(path: Path, root: Path) -> list[Finding]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call = _call_name(node.func)
        if call not in STREAMLIT_TEXT_CALLS or not node.args:
            continue
        first_arg = node.args[0]
        if _is_i18n_wrapped(first_arg):
            continue
        for text in _literal_strings(first_arg):
            compact = " ".join(text.split())
            if compact:
                findings.append(
                    Finding(
                        path=str(path.relative_to(root)).replace("\\", "/"),
                        line=getattr(node, "lineno", 0),
                        call=call,
                        text=compact[:240],
                    )
                )
    return findings


def run(root: Path) -> list[Finding]:
    paths = [root / "app"]
    findings: list[Finding] = []
    for base in paths:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            findings.extend(audit_file(path, root))
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = run(root)
    print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
