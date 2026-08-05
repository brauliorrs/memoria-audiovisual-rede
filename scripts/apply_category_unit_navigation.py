"""Apply the category-level unit selector to the Streamlit entrypoint.

This migration is intentionally idempotent. It inserts the selector once and
exits successfully when the target block has already been updated.
"""

from pathlib import Path


APP_PATH = Path("app/streamlit_app.py")
MARKER = "category-unit-detail-selector-"
ANCHOR = "\n\ndef format_institution_label(summary_df, slug):\n"
INSERTION = '''

    st.divider()
    st.markdown("### Unidades desta categoria")
    st.caption(
        "Selecione uma unidade para abrir seu conteúdo completo nesta mesma aba, "
        "sem criar uma aba principal adicional."
    )
    if not corpora_in_category:
        st.info("Ainda não há unidades disponíveis nesta categoria.")
        return

    unit_labels = {
        corpus_def["short_label"]: corpus_def
        for corpus_def in corpora_in_category
    }
    selected_unit_label = st.selectbox(
        "Abrir unidade",
        options=list(unit_labels),
        key=f"category-unit-detail-selector-{category_code}",
    )
    selected_unit = unit_labels[selected_unit_label]
    with st.container(border=True):
        render_corpus_tab(selected_unit)
'''


def main() -> int:
    text = APP_PATH.read_text(encoding="utf-8")
    if MARKER in text:
        print("Category unit selector already present.")
        return 0
    if ANCHOR not in text:
        raise SystemExit("Could not locate category-tab insertion anchor.")
    updated = text.replace(ANCHOR, INSERTION + ANCHOR, 1)
    APP_PATH.write_text(updated, encoding="utf-8")
    print("Category unit selector inserted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
