from __future__ import annotations

import ast
import json
import re
import unicodedata
from pathlib import Path

APP_PATH = Path("app/streamlit_app.py")
LOCALE_PATH = Path("src/memoria_audiovisual/locales/pt.json")
TEXT_METHODS = {
    "title", "header", "subheader", "markdown", "caption", "info", "warning",
    "error", "success", "write", "button", "download_button", "link_button",
    "text_input", "checkbox", "radio", "selectbox", "multiselect", "expander", "metric",
}


def slugify(text: str) -> str:
    value = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")[:52] or "text"


def char_column(line: str, byte_column: int) -> int:
    return len(line.encode("utf-8")[:byte_column].decode("utf-8"))


def migrate() -> int:
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    def position(node: ast.AST) -> tuple[int, int]:
        start_line = lines[node.lineno - 1]
        end_line = lines[node.end_lineno - 1]
        start = offsets[node.lineno - 1] + char_column(start_line, node.col_offset)
        end = offsets[node.end_lineno - 1] + char_column(end_line, node.end_col_offset)
        return start, end

    target = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "render_observatory_overview_tab"
    )
    catalogue = json.loads(LOCALE_PATH.read_text(encoding="utf-8"))
    replacements: list[tuple[int, int, str]] = []
    used = set(catalogue)

    def register(text: str, prefix: str) -> str:
        base = f"overview.{prefix}.{slugify(text)}"
        key = base
        index = 2
        while key in used and catalogue.get(key) != text:
            key = f"{base}_{index}"
            index += 1
        used.add(key)
        catalogue[key] = text
        return key

    def add_text_node(node: ast.AST, prefix: str) -> None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip():
            key = register(node.value, prefix)
            start, end = position(node)
            replacements.append((start, end, f"tr_key({key!r})"))
            return

        if isinstance(node, ast.JoinedStr):
            template_parts: list[str] = []
            arguments: list[str] = []
            placeholder_index = 0
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    template_parts.append(value.value.replace("{", "{{").replace("}", "}}"))
                elif isinstance(value, ast.FormattedValue):
                    name = f"value_{placeholder_index}"
                    placeholder_index += 1
                    conversion = f"!{chr(value.conversion)}" if value.conversion != -1 else ""
                    format_spec = ""
                    if value.format_spec is not None:
                        segment = ast.get_source_segment(source, value.format_spec)
                        if segment:
                            format_spec = f":{segment.strip('f').strip(chr(34)).strip(chr(39))}"
                    template_parts.append(f"{{{name}{conversion}{format_spec}}}")
                    expression = ast.get_source_segment(source, value.value) or ast.unparse(value.value)
                    arguments.append(f"{name}={expression}")
            template = "".join(template_parts)
            if template.strip():
                key = register(template, prefix)
                call = f"tr_key({key!r}"
                if arguments:
                    call += ", " + ", ".join(arguments)
                call += ")"
                start, end = position(node)
                replacements.append((start, end, call))

    for node in ast.walk(target):
        if not isinstance(node, ast.Call):
            continue
        name = (
            node.func.attr if isinstance(node.func, ast.Attribute)
            else node.func.id if isinstance(node.func, ast.Name)
            else None
        )

        if name in TEXT_METHODS and node.args:
            add_text_node(node.args[0], f"ui.{name}")
            for keyword in node.keywords:
                if keyword.arg in {"label", "help", "placeholder"}:
                    add_text_node(keyword.value, f"ui.{name}.{keyword.arg}")

        if name in {"render_csv_download", "render_json_download"}:
            if len(node.args) > 0:
                add_text_node(node.args[0], "download.label")
            if len(node.args) > 3:
                add_text_node(node.args[3], "download.help")

        if name == "tabs" and node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
            for element in node.args[0].elts:
                add_text_node(element, "tabs")

        if name == "rename":
            for keyword in node.keywords:
                if keyword.arg == "columns" and isinstance(keyword.value, ast.Dict):
                    for value in keyword.value.values:
                        add_text_node(value, "table.column")

    unique = {(start, end): replacement for start, end, replacement in replacements}
    for start, end, replacement in sorted(
        ((start, end, replacement) for (start, end), replacement in unique.items()),
        reverse=True,
    ):
        source = source[:start] + replacement + source[end:]

    compile(source, str(APP_PATH), "exec")
    APP_PATH.write_text(source, encoding="utf-8")
    LOCALE_PATH.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audited = ast.parse(source)
    overview = next(
        node for node in audited.body
        if isinstance(node, ast.FunctionDef) and node.name == "render_observatory_overview_tab"
    )
    remaining = []
    for node in ast.walk(overview):
        if not isinstance(node, ast.Call):
            continue
        name = (
            node.func.attr if isinstance(node.func, ast.Attribute)
            else node.func.id if isinstance(node.func, ast.Name)
            else None
        )
        if name in TEXT_METHODS and node.args and isinstance(node.args[0], (ast.Constant, ast.JoinedStr)):
            remaining.append((node.lineno, name, ast.get_source_segment(source, node.args[0]) or ""))
        if name in {"render_csv_download", "render_json_download"}:
            for index in (0, 3):
                if len(node.args) > index and isinstance(node.args[index], (ast.Constant, ast.JoinedStr)):
                    remaining.append((node.lineno, name, ast.get_source_segment(source, node.args[index]) or ""))
        if name == "rename":
            for keyword in node.keywords:
                if keyword.arg == "columns" and isinstance(keyword.value, ast.Dict):
                    for value in keyword.value.values:
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            remaining.append((value.lineno, "table.column", value.value))
    if remaining:
        raise SystemExit(f"Remaining Overview UI literals: {remaining[:20]}")
    return len(unique)


if __name__ == "__main__":
    print(f"Migrated {migrate()} Overview strings and table labels.")
