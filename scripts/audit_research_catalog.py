from __future__ import annotations

import ast
import json
from pathlib import Path

APP_PATH = Path("app/streamlit_app.py")
PROFILE_PATH = Path("src/memoria_audiovisual/research_profile.py")
LOCALE_PATH = Path("src/memoria_audiovisual/locales/pt.json")

PUBLIC_METHODS = {
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
    "text_input",
    "checkbox",
    "radio",
    "selectbox",
    "multiselect",
    "expander",
    "metric",
}

REQUIRED_COLUMNS = {
    "research.columns.dimension",
    "research.columns.definition",
    "research.columns.parameter",
    "research.columns.platform_translation",
    "research.columns.current_evidence",
    "research.columns.status",
    "research.columns.priority",
    "research.columns.adjustment",
    "research.columns.expected_result",
}

REQUIRED_STATUS_KEYS = {
    "research.status.implemented",
    "research.status.adapting",
    "research.status.to_develop",
}

ALLOWED_INTERNAL_STATUSES = {"implemented", "adapting", "to_develop"}
LEGACY_NAMES = {
    "PHRASE_TRANSLATIONS",
    "translate_ui_text",
    "language_code_from_label",
    "_PROFILE_TRANSLATIONS",
    "_register_profile_translations",
    "_active_language",
    "_localize_rows",
}


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def assigned_value(tree: ast.Module, name: str) -> ast.AST:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.value
    raise AssertionError(f"Required assignment not found: {name}")


def collect_strings(node: ast.AST) -> list[str]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    ]


def main() -> None:
    app_source = APP_PATH.read_text(encoding="utf-8")
    profile_source = PROFILE_PATH.read_text(encoding="utf-8")
    catalogue = json.loads(LOCALE_PATH.read_text(encoding="utf-8"))
    app_tree = ast.parse(app_source)
    profile_tree = ast.parse(profile_source)

    errors: list[str] = []

    # The scientific profile must no longer depend on the legacy replacement engine.
    profile_names = {node.id for node in ast.walk(profile_tree) if isinstance(node, ast.Name)}
    legacy_found = sorted(LEGACY_NAMES & profile_names)
    if legacy_found:
        errors.append(f"Legacy internationalization names remain in research_profile.py: {legacy_found}")

    # Public research constants and structured rows must contain semantic keys, not Portuguese UI text.
    semantic_assignments = (
        "RESEARCH_WORKING_TITLE",
        "RESEARCH_SUBTITLE",
        "RESEARCH_MAIN_QUESTION",
        "RESEARCH_PLATFORM_POSITIONING",
        "RESEARCH_PARAMETER_ROWS",
        "RESEARCH_NEXT_ADJUSTMENT_ROWS",
    )
    profile_keys: set[str] = set()
    for assignment in semantic_assignments:
        value = assigned_value(profile_tree, assignment)
        for text in collect_strings(value):
            if assignment in {"RESEARCH_PARAMETER_ROWS", "RESEARCH_NEXT_ADJUSTMENT_ROWS"} and text in ALLOWED_INTERNAL_STATUSES:
                continue
            if assignment == "RESEARCH_NEXT_ADJUSTMENT_ROWS" and text.isdigit():
                continue
            if not text.startswith("research."):
                errors.append(f"Non-semantic public value in {assignment}: {text!r}")
            else:
                profile_keys.add(text)

    # Internal state codes must remain stable and independent from displayed language.
    parameter_rows = assigned_value(profile_tree, "RESEARCH_PARAMETER_ROWS")
    internal_statuses = {
        child.value
        for child in ast.walk(parameter_rows)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, str)
        and child.value in ALLOWED_INTERNAL_STATUSES
    }
    if internal_statuses != ALLOWED_INTERNAL_STATUSES:
        errors.append(
            "Research parameter internal statuses must be exactly "
            f"{sorted(ALLOWED_INTERNAL_STATUSES)}; found {sorted(internal_statuses)}"
        )

    # The renderer may expose only catalogue lookups, never literal public text.
    renderer = next(
        (
            node
            for node in app_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "render_scientific_parameters_section"
        ),
        None,
    )
    if renderer is None:
        errors.append("render_scientific_parameters_section() was not found")
        renderer_keys: set[str] = set()
    else:
        renderer_keys = set()
        for node in ast.walk(renderer):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node)
            if name == "tr_key" and node.args:
                key = literal_string(node.args[0])
                if key:
                    renderer_keys.add(key)
            if name in PUBLIC_METHODS and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    errors.append(
                        f"Literal public text remains in scientific parameters at line {node.lineno}: {first.value!r}"
                    )
            if name == "tabs" and node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
                for element in node.args[0].elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, str):
                        errors.append(
                            f"Literal tab label remains in scientific parameters at line {node.lineno}: {element.value!r}"
                        )

    required_keys = profile_keys | renderer_keys | REQUIRED_COLUMNS | REQUIRED_STATUS_KEYS
    missing_keys = sorted(key for key in required_keys if key not in catalogue)
    if missing_keys:
        errors.append(f"Missing Portuguese catalogue keys: {missing_keys}")

    empty_keys = sorted(
        key for key in required_keys if key in catalogue and not str(catalogue[key]).strip()
    )
    if empty_keys:
        errors.append(f"Empty Portuguese catalogue values: {empty_keys}")

    # Builders must receive the catalogue resolver, preventing a return to implicit translation.
    required_calls = {
        "build_research_parameter_rows": False,
        "build_research_next_adjustment_rows": False,
        "build_research_positioning_rows": False,
    }
    if renderer is not None:
        for node in ast.walk(renderer):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id in required_calls:
                required_calls[node.func.id] = bool(
                    node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "tr_key"
                )
    invalid_builders = sorted(name for name, valid in required_calls.items() if not valid)
    if invalid_builders:
        errors.append(f"Research builders are not explicitly using tr_key: {invalid_builders}")

    if errors:
        raise SystemExit("Scientific parameters catalogue audit failed:\n- " + "\n- ".join(errors))

    print(
        "Scientific parameters catalogue audit passed: "
        f"{len(required_keys)} required keys verified, no legacy translation path, "
        "no literal public UI text, and stable internal status codes."
    )


if __name__ == "__main__":
    main()
