"""Pass the active localized scientific-infrastructure label to navigation."""
from pathlib import Path

path = Path("app/streamlit_app.py")
text = path.read_text(encoding="utf-8")
old = '''navigation_labels, navigation_slices = build_navigation_contract(
    tr_key=tr_key,
    category_definitions=category_definitions,
    corpus_definitions=corpus_definitions,
    protocolled_units=protocolled_excluded_units,
)'''
new = '''navigation_labels, navigation_slices = build_navigation_contract(
    tr_key=tr_key,
    category_definitions=category_definitions,
    corpus_definitions=corpus_definitions,
    protocolled_units=protocolled_excluded_units,
    scientific_infrastructure_label=localize_ui("Infraestrutura científica"),
)'''
if old not in text:
    if new in text:
        raise SystemExit(0)
    raise SystemExit("navigation contract call not found")
path.write_text(text.replace(old, new), encoding="utf-8")
