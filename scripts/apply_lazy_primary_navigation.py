"""Replace eager Streamlit tabs with a single selected primary section."""
from pathlib import Path

path = Path("app/streamlit_app.py")
text = path.read_text(encoding="utf-8")
old = '''top_level_tabs = st.tabs(navigation_labels)

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

for category_tab, category_def in zip(category_tabs, CORPUS_CATEGORIES.values()):
    with category_tab:
        render_category_tab(category_def)

for corpus_tab, corpus_def in zip(corpus_tabs, CORPORA.values()):
    with corpus_tab:
        render_corpus_tab(corpus_def)

for protocolled_tab, unit_record in zip(protocolled_tabs, protocolled_excluded_units):
    with protocolled_tab:
        render_protocolled_excluded_unit_tab(unit_record)
'''
new = '''selected_primary_section = st.radio(
    tr_key("navigation.primary_section"),
    options=navigation_labels,
    horizontal=True,
    label_visibility="collapsed",
    key="primary-navigation-section",
)

if selected_primary_section == navigation_labels[navigation_slices.overview_index]:
    render_observatory_overview_tab()
elif selected_primary_section == navigation_labels[navigation_slices.scientific_infrastructure_index]:
    render_scientific_infrastructure(BASE_DIR, language=APP_LANGUAGE)
else:
    selected_category_index = navigation_labels.index(selected_primary_section)
    category_offset = selected_category_index - navigation_slices.category_start
    if 0 <= category_offset < len(category_definitions):
        render_category_tab(category_definitions[category_offset])
'''
if old not in text:
    if new in text:
        raise SystemExit(0)
    raise SystemExit("target navigation block not found")
path.write_text(text.replace(old, new), encoding="utf-8")
