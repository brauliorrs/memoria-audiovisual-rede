import pytest

from scripts.migrate_streamlit_entrypoint import (
    INFRASTRUCTURE_IMPORT,
    LEGACY_NAVIGATION_BLOCK,
    MODULAR_NAVIGATION_BLOCK,
    NAVIGATION_IMPORT,
    transform_entrypoint,
    validate_transformed_source,
)


def _legacy_source() -> str:
    return (
        "from memoria_audiovisual.output_files import list_output_filenames\n\n"
        + LEGACY_NAVIGATION_BLOCK
        + "\nfor category_tab in category_tabs:\n    pass\n"
    )


def test_transform_adds_imports_and_modular_navigation():
    transformed = transform_entrypoint(_legacy_source())

    assert NAVIGATION_IMPORT in transformed
    assert INFRASTRUCTURE_IMPORT in transformed
    assert MODULAR_NAVIGATION_BLOCK in transformed
    assert LEGACY_NAVIGATION_BLOCK not in transformed
    validate_transformed_source(transformed)


def test_transform_is_idempotent():
    first = transform_entrypoint(_legacy_source())
    second = transform_entrypoint(first)
    assert second == first


def test_transform_rejects_unknown_structure():
    with pytest.raises(RuntimeError, match="Bloco legado"):
        transform_entrypoint(
            "from memoria_audiovisual.output_files import list_output_filenames\n"
        )


def test_validation_rejects_partial_integration():
    with pytest.raises(RuntimeError, match="Integração incompleta"):
        validate_transformed_source(NAVIGATION_IMPORT + INFRASTRUCTURE_IMPORT)
