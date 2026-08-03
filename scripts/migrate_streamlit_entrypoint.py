"""Migração idempotente do entrypoint Streamlit para a navegação modular.

Este utilitário aplica uma transformação estrutural verificável no arquivo
monolítico legado. Ele não é chamado pela aplicação nem por workflows e nunca
faz deploy. A transformação falha se os contratos esperados não estiverem
presentes, evitando substituições parciais ou silenciosas.
"""

from __future__ import annotations

import argparse
from pathlib import Path


NAVIGATION_IMPORT = "from memoria_audiovisual.ui.navigation import build_navigation_contract\n"
INFRASTRUCTURE_IMPORT = (
    "from memoria_audiovisual.ui.scientific_infrastructure import "
    "render_scientific_infrastructure\n"
)
IMPORT_ANCHOR = "from memoria_audiovisual.output_files import list_output_filenames\n"

LEGACY_NAVIGATION_BLOCK = '''protocolled_excluded_units = load_protocolled_excluded_units()
top_level_tabs = st.tabs(
    [tr_key("navigation.overview")]
    + [tr_key("navigation.category", label=category_def["short_label"]) for category_def in CORPUS_CATEGORIES.values()]
    + [tr_key("navigation.unit", label=definition["short_label"]) for definition in CORPORA.values()]
    + [tr_key("navigation.documented_case", label=unit["unit_label"]) for unit in protocolled_excluded_units]
)

with top_level_tabs[0]:
    render_observatory_overview_tab()

category_start = 1
category_tabs = top_level_tabs[category_start : category_start + len(CORPUS_CATEGORIES)]
corpus_start = category_start + len(CORPUS_CATEGORIES)
corpus_tabs = top_level_tabs[corpus_start : corpus_start + len(CORPORA)]
protocolled_tabs = top_level_tabs[corpus_start + len(CORPORA) :]
'''

MODULAR_NAVIGATION_BLOCK = '''protocolled_excluded_units = load_protocolled_excluded_units()
category_definitions = list(CORPUS_CATEGORIES.values())
corpus_definitions = list(CORPORA.values())
navigation_labels, navigation_slices = build_navigation_contract(
    tr_key=tr_key,
    category_definitions=category_definitions,
    corpus_definitions=corpus_definitions,
    protocolled_units=protocolled_excluded_units,
)
top_level_tabs = st.tabs(navigation_labels)

with top_level_tabs[navigation_slices.overview_index]:
    render_observatory_overview_tab()

with top_level_tabs[navigation_slices.scientific_infrastructure_index]:
    render_scientific_infrastructure(BASE_DIR)

category_tabs = top_level_tabs[
    navigation_slices.category_start : navigation_slices.category_stop
]
corpus_tabs = top_level_tabs[
    navigation_slices.corpus_start : navigation_slices.corpus_stop
]
protocolled_tabs = top_level_tabs[navigation_slices.protocolled_start :]
'''


def transform_entrypoint(source: str) -> str:
    """Aplica a integração permanente ou confirma que ela já está aplicada."""
    transformed = source

    if NAVIGATION_IMPORT not in transformed or INFRASTRUCTURE_IMPORT not in transformed:
        if IMPORT_ANCHOR not in transformed:
            raise RuntimeError("Âncora de imports do entrypoint não localizada")
        imports = ""
        if NAVIGATION_IMPORT not in transformed:
            imports += NAVIGATION_IMPORT
        if INFRASTRUCTURE_IMPORT not in transformed:
            imports += INFRASTRUCTURE_IMPORT
        transformed = transformed.replace(IMPORT_ANCHOR, imports + IMPORT_ANCHOR, 1)

    if MODULAR_NAVIGATION_BLOCK in transformed:
        return transformed
    if LEGACY_NAVIGATION_BLOCK not in transformed:
        raise RuntimeError("Bloco legado de navegação não localizado integralmente")
    return transformed.replace(LEGACY_NAVIGATION_BLOCK, MODULAR_NAVIGATION_BLOCK, 1)


def validate_transformed_source(source: str) -> None:
    required_fragments = (
        NAVIGATION_IMPORT.strip(),
        INFRASTRUCTURE_IMPORT.strip(),
        "navigation_labels, navigation_slices = build_navigation_contract(",
        "render_scientific_infrastructure(BASE_DIR)",
        "navigation_slices.category_start : navigation_slices.category_stop",
        "navigation_slices.corpus_start : navigation_slices.corpus_stop",
        "top_level_tabs[navigation_slices.protocolled_start :]",
    )
    missing = [fragment for fragment in required_fragments if fragment not in source]
    if missing:
        raise RuntimeError(f"Integração incompleta; fragmentos ausentes: {missing}")
    if LEGACY_NAVIGATION_BLOCK in source:
        raise RuntimeError("O bloco legado permaneceu no entrypoint")


def migrate(path: Path, *, check: bool = False) -> bool:
    source = path.read_text(encoding="utf-8")
    transformed = transform_entrypoint(source)
    validate_transformed_source(transformed)
    changed = transformed != source
    if check:
        if changed:
            raise RuntimeError(f"{path} ainda requer a migração modular")
        return False
    if changed:
        path.write_text(transformed, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path("app/streamlit_app.py"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = migrate(args.path, check=args.check)
    print("entrypoint atualizado" if changed else "entrypoint já estava atualizado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
