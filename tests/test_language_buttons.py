from memoria_audiovisual.ui.language_buttons import (
    LANGUAGE_BUTTON_LABELS,
    LEGACY_LANGUAGE_SELECTOR_LABEL,
    resolve_language_label,
)


LANGUAGE_LABELS = ["Português", "Español", "English"]


def test_language_buttons_use_compact_public_labels():
    assert LANGUAGE_BUTTON_LABELS == {
        "Português": "PT",
        "Español": "ES",
        "English": "EN",
    }


def test_resolve_language_label_preserves_session_selection():
    assert (
        resolve_language_label(
            LANGUAGE_LABELS,
            index=0,
            stored_label="English",
        )
        == "English"
    )


def test_resolve_language_label_uses_requested_index_without_session_value():
    assert resolve_language_label(LANGUAGE_LABELS, index=1) == "Español"


def test_resolve_language_label_clamps_invalid_index():
    assert (
        resolve_language_label(
            LANGUAGE_LABELS,
            index=99,
            stored_label="invalid",
        )
        == "English"
    )


def test_adapter_is_limited_to_the_legacy_language_selector():
    assert LEGACY_LANGUAGE_SELECTOR_LABEL == "Idioma / Language / Idioma"
