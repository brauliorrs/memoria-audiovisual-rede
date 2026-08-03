from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


STREAMLIT_TEXT_CALLS = {
    "title", "header", "subheader", "markdown", "caption", "info", "warning",
    "error", "success", "write", "button", "download_button", "link_button",
    "checkbox", "toggle", "radio", "selectbox", "multiselect", "text_input",
    "text_area", "number_input", "date_input", "time_input", "slider",
    "select_slider", "file_uploader", "metric", "expander", "tabs",
}

# Only language-distinctive markers are used. Shared Romance-language words such as
# "plataforma", "comparativa" and "acesso/acceso" are deliberately excluded.
DISTINCTIVE_MARKERS = {
    "pt": {
        "aberta", "observação", "circulação", "acervos", "condições", "técnicas",
        "próximos", "desenvolver", "evidência", "pergunta", "provisória", "não",
        "ainda", "instituições", "visibilidade", "restrito", "arquivos", "ajustes",
        "pesquisa", "dados", "públicos", "rodada", "unidades", "relatório",
    },
    "en": {
        "open", "observation", "circulation", "archives", "conditions", "technical",
        "next", "developed", "evidence", "question", "provisional", "not", "yet",
        "institutions", "visibility", "restricted", "files", "adjustments", "research",
        "data", "public", "round", "units", "report", "platform", "scientific",
    },
    "es": {
        "abierta", "observación", "circulación", "archivos", "condiciones", "técnicas",
        "siguientes", "desarrollar", "evidencia", "pregunta", "provisional", "todavía",
        "instituciones", "visibilidad", "restringido", "ajustes", "investigación",
        "datos", "públicos", "ronda", "unidades", "informe", "científica",
    },
}

TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", re.UNICODE)
HTML_RE = re.compile(r"<[^>]+>")


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


def _literal_strings(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        return [
            part.value
            for part in node.values
            if isinstance(part, ast.Constant) and isinstance(part.value, str)
        ]
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values: list[str] = []
        for element in node.elts:
            values.extend(_literal_strings(element))
        return values
    return []


def _compact(text: str) -> str:
    return " ".join(HTML_RE.sub(" ", text).split())[:500]


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text)}


def _marker_hits(text: str, language: str) -> set[str]:
    return _tokens(text) & DISTINCTIVE_MARKERS[language]


def _page_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    if relative.parts[:1] == ("app",):
        return relative.stem.replace("streamlit_", "").replace("_", " ").title()
    return relative.stem.replace("_", " ").title()


def collect_visible_literals(path: Path, root: Path) -> list[tuple[int, str, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    values: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        call = _call_name(node.func)
        if call not in STREAMLIT_TEXT_CALLS:
            continue
        for text in _literal_strings(node.args[0]):
            compact = _compact(text)
            if compact and len(compact) >= 4:
                values.append((getattr(node, "lineno", 0), call, compact))
    return values


def load_runtime_samples(root: Path) -> tuple[object, list[tuple[str, int, str, str]]]:
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from memoria_audiovisual.i18n import translate_ui_text
    from memoria_audiovisual import research_profile

    samples: list[tuple[str, int, str, str]] = []
    profile_path = "src/memoria_audiovisual/research_profile.py"

    for value in (
        research_profile.RESEARCH_SUBTITLE,
        research_profile.RESEARCH_MAIN_QUESTION,
        *research_profile.RESEARCH_PLATFORM_POSITIONING.keys(),
        *research_profile.RESEARCH_PLATFORM_POSITIONING.values(),
    ):
        samples.append((profile_path, 0, "research_profile", str(value)))

    for row in (
        research_profile.build_research_parameter_rows()
        + research_profile.build_research_next_adjustment_rows()
    ):
        for key, value in row.items():
            samples.append((profile_path, 0, "research_profile", str(key)))
            samples.append((profile_path, 0, "research_profile", str(value)))

    app_path = root / "app" / "streamlit_app.py"
    for line, call, text in collect_visible_literals(app_path, root):
        samples.append(("app/streamlit_app.py", line, call, text))

    return translate_ui_text, samples


def audit_rendered_translation(
    *,
    path: str,
    line: int,
    call: str,
    source: str,
    target_language: str,
    rendered: str,
) -> Finding | None:
    source_compact = _compact(source)
    rendered_compact = _compact(rendered)
    if not source_compact or not rendered_compact:
        return None

    # Source records and proper names may legitimately remain unchanged. The audit is
    # limited to Portuguese-authored interface text with at least two distinctive markers.
    source_pt_hits = _marker_hits(source_compact, "pt")
    if len(source_pt_hits) < 2:
        return None

    residual_pt = _marker_hits(rendered_compact, "pt")
    target_hits = _marker_hits(rendered_compact, target_language)

    # Blocking: a translated public sentence still carries several distinctive Portuguese
    # markers, whether or not isolated target-language substitutions were also applied.
    if len(residual_pt) >= 2:
        languages = tuple(sorted({"pt", target_language} if target_hits else {"pt"}))
        return Finding(
            path=path,
            page="App" if path.startswith("app/") else "Research Profile",
            line=line,
            kind="residual_source_language",
            severity="high",
            call=call,
            text=f"[{target_language}] {rendered_compact}",
            languages=languages,
        )

    return None


def run(root: Path) -> list[Finding]:
    translate_ui_text, samples = load_runtime_samples(root)
    findings: list[Finding] = []

    for path, line, call, source in samples:
        for target_language in ("en", "es"):
            rendered = translate_ui_text(source, target_language)
            finding = audit_rendered_translation(
                path=path,
                line=line,
                call=call,
                source=source,
                target_language=target_language,
                rendered=rendered,
            )
            if finding:
                findings.append(finding)

    unique: dict[tuple, Finding] = {}
    for finding in findings:
        key = (
            finding.path,
            finding.line,
            finding.kind,
            finding.call,
            finding.text,
            finding.languages,
        )
        unique[key] = finding

    return sorted(unique.values(), key=lambda item: (item.page, item.path, item.line, item.text))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = run(root)
    print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
