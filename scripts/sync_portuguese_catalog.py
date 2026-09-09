from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app" / "streamlit_app.py"
CATALOG_PATH = ROOT / "src" / "memoria_audiovisual" / "locales" / "pt.json"

PUBLIC_CALLS = {
    "title", "header", "subheader", "markdown", "caption", "info", "warning",
    "error", "success", "write", "button", "download_button", "link_button",
    "checkbox", "toggle", "radio", "selectbox", "multiselect", "text_input",
    "text_area", "number_input", "date_input", "time_input", "slider",
    "select_slider", "file_uploader", "metric", "expander", "tabs",
}
PUBLIC_KEYWORDS = {"label", "help", "placeholder"}
SLUG_RE = re.compile(r"[^a-z0-9]+")


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def template_from_node(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        variable_index = 0
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("{" + f"value_{variable_index}" + "}")
                variable_index += 1
        return ["".join(parts)]
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values: list[str] = []
        for element in node.elts:
            values.extend(template_from_node(element))
        return values
    return []


def normalize(text: str) -> str:
    return " ".join(text.strip().split())


def make_key(text: str, call: str) -> str:
    normalized = normalize(text)
    slug = SLUG_RE.sub("_", normalized.lower()).strip("_")[:52] or "text"
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"app.catalog.{call}.{slug}.{digest}"


def extract_entries() -> dict[str, str]:
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8-sig"), filename=str(APP_PATH))
    entries: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call = call_name(node.func)
        if call not in PUBLIC_CALLS:
            continue
        candidates: list[str] = []
        if node.args:
            candidates.extend(template_from_node(node.args[0]))
        for keyword in node.keywords:
            if keyword.arg in PUBLIC_KEYWORDS:
                candidates.extend(template_from_node(keyword.value))
        for text in candidates:
            normalized = normalize(text)
            if len(normalized) < 2:
                continue
            # Existing semantic keys are references, not public Portuguese text.
            if normalized.startswith(("home.", "overview.", "research.", "navigation.")) and " " not in normalized:
                continue
            entries[make_key(normalized, call)] = normalized
    return dict(sorted(entries.items()))


def load_catalog() -> dict[str, str]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    catalog = load_catalog()
    extracted = extract_entries()
    missing = {key: value for key, value in extracted.items() if catalog.get(key) != value}

    if args.check:
        if missing:
            print(f"Portuguese catalogue is missing or differs for {len(missing)} visible entries.")
            for key in list(missing)[:25]:
                print(f"- {key}: {missing[key]}")
            return 1
        print(f"Portuguese catalogue covers all {len(extracted)} visible literal entries.")
        return 0

    if missing:
        catalog.update(missing)
        CATALOG_PATH.write_text(
            json.dumps(dict(sorted(catalog.items())), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"Portuguese catalogue synchronized: {len(extracted)} visible entries; {len(missing)} added or updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
