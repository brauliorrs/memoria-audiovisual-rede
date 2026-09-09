from __future__ import annotations

import ast
import json
from pathlib import Path

APP_PATH = Path("app/streamlit_app.py")
LOCALE_PATH = Path("src/memoria_audiovisual/locales/pt.json")
TEXT_METHODS = {
    "title", "header", "subheader", "markdown", "caption", "info", "warning",
    "error", "success", "write", "button", "download_button", "link_button",
    "text_input", "checkbox", "radio", "selectbox", "multiselect", "expander", "metric",
}


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def is_public_literal(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and bool(node.value.strip())
    ) or isinstance(node, ast.JoinedStr)


def main() -> None:
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    catalogue = json.loads(LOCALE_PATH.read_text(encoding="utf-8"))
    overview = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "render_observatory_overview_tab"
    )

    findings: list[str] = []
    used_keys: set[str] = set()

    for node in ast.walk(overview):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)

        if name == "tr_key" and node.args:
            key_node = node.args[0]
            if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                used_keys.add(key_node.value)
            else:
                findings.append(f"line {node.lineno}: tr_key must use a static semantic key")

        if name in TEXT_METHODS and node.args and is_public_literal(node.args[0]):
            findings.append(f"line {node.lineno}: public {name} text remains literal")

        if name in {"render_csv_download", "render_json_download"}:
            for index, label in ((0, "label"), (3, "help")):
                if len(node.args) > index and is_public_literal(node.args[index]):
                    findings.append(f"line {node.lineno}: download {label} remains literal")

        if name == "tabs" and node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
            for element in node.args[0].elts:
                if is_public_literal(element):
                    findings.append(f"line {element.lineno}: tab label remains literal")

        if name == "rename":
            for keyword in node.keywords:
                if keyword.arg == "columns" and isinstance(keyword.value, ast.Dict):
                    for value in keyword.value.values:
                        if is_public_literal(value):
                            findings.append(f"line {value.lineno}: visible table-column label remains literal")

    missing = sorted(key for key in used_keys if key not in catalogue)
    findings.extend(f"missing Portuguese catalogue key: {key}" for key in missing)

    if findings:
        raise SystemExit("Overview semantic-catalogue audit failed:\n- " + "\n- ".join(findings[:100]))

    print(
        f"Overview semantic-catalogue audit passed: {len(used_keys)} keys resolved, "
        "with no public literals in audited UI components."
    )


if __name__ == "__main__":
    main()
