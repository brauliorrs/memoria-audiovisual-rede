"""Seletor compacto de idioma integrado à página principal."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from memoria_audiovisual.i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGE_CODES_BY_LABEL,
    LANGUAGE_OPTIONS,
)

LEGACY_LANGUAGE_SELECTOR_LABEL = "Idioma / Language / Idioma"
LANGUAGE_BUTTON_LABELS = {
    "Português": "PT",
    "Español": "ES",
    "English": "EN",
}
_ADAPTER_MARKER = "_memoria_inline_language_selector_installed"


def resolve_language_label(
    options: Sequence[str],
    *,
    index: int = 0,
    stored_label: object = None,
) -> str:
    """Resolve o idioma preservado e aplica um índice seguro como fallback."""
    labels = [str(option) for option in options]
    if not labels:
        return LANGUAGE_OPTIONS[DEFAULT_LANGUAGE]

    stored = str(stored_label or "")
    if stored in labels:
        return stored

    safe_index = min(max(int(index), 0), len(labels) - 1)
    return labels[safe_index]


def _button_code(label: str, position: int) -> str:
    return LANGUAGE_CODES_BY_LABEL.get(label, f"option-{position}")


def _is_sidebar_container(container: DeltaGenerator) -> bool:
    if container is st.sidebar:
        return True
    root = getattr(container, "_root_container", None)
    sidebar_root = getattr(st.sidebar, "_root_container", None)
    return root is not None and root == sidebar_root


def render_inline_language_buttons(
    *,
    options: Sequence[str],
    index: int = 0,
    key: str = "interface_language",
) -> str:
    """Renderiza PT, ES e EN no topo e retorna o rótulo completo selecionado."""
    labels = [str(option) for option in options]
    current = resolve_language_label(
        labels,
        index=index,
        stored_label=st.session_state.get(key),
    )
    st.session_state[key] = current

    spacer, *button_columns = st.columns(
        [6.4, 0.75, 0.75, 0.75],
        gap="small",
        vertical_alignment="center",
    )
    del spacer

    for position, (column, label) in enumerate(zip(button_columns, labels)):
        short_label = LANGUAGE_BUTTON_LABELS.get(
            label,
            _button_code(label, position).upper(),
        )
        with column:
            clicked = st.button(
                short_label,
                key=f"{key}-button-{_button_code(label, position)}",
                type="primary" if label == current else "secondary",
                help=label,
                use_container_width=True,
            )
        if clicked and label != current:
            st.session_state[key] = label
            st.rerun()

    return current


def install_language_button_adapter() -> None:
    """Converte somente o seletor lateral legado em botões na página principal."""
    if getattr(DeltaGenerator, _ADAPTER_MARKER, False):
        return

    original_selectbox = DeltaGenerator.selectbox

    def selectbox_adapter(
        self: DeltaGenerator,
        label: str,
        options: Sequence[Any],
        *args: Any,
        **kwargs: Any,
    ):
        if _is_sidebar_container(self) and label == LEGACY_LANGUAGE_SELECTOR_LABEL:
            index = int(kwargs.get("index", 0) or 0)
            key = str(kwargs.get("key") or "interface_language")
            return render_inline_language_buttons(
                options=[str(option) for option in options],
                index=index,
                key=key,
            )
        return original_selectbox(self, label, options, *args, **kwargs)

    DeltaGenerator.selectbox = selectbox_adapter
    setattr(DeltaGenerator, _ADAPTER_MARKER, True)


__all__ = [
    "LANGUAGE_BUTTON_LABELS",
    "LEGACY_LANGUAGE_SELECTOR_LABEL",
    "install_language_button_adapter",
    "render_inline_language_buttons",
    "resolve_language_label",
]
