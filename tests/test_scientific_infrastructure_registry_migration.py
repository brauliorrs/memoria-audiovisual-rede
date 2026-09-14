from scripts.migrate_scientific_infrastructure_registry import (
    NEW_IMPORTS,
    NEW_RENDER_SETUP,
    OLD_IMPORTS,
    OLD_LOCAL_LOADERS_START,
    OLD_RENDER_SETUP,
    transform,
    validate,
)


def _legacy_source() -> str:
    return (
        OLD_IMPORTS
        + "\n"
        + OLD_LOCAL_LOADERS_START
        + "    pass\n\n"
        + "def _as_list(value: object) -> list[Any]:\n    return []\n\n"
        + "def render_scientific_infrastructure(base_dir):\n"
        + OLD_RENDER_SETUP
        + "    return None\n"
    )


def test_transform_replaces_local_registry_and_loader_logic():
    migrated = transform(_legacy_source())

    assert NEW_IMPORTS in migrated
    assert NEW_RENDER_SETUP in migrated
    assert "class ScientificInfrastructurePaths" not in migrated
    validate(migrated)


def test_transform_is_idempotent():
    first = transform(_legacy_source())
    second = transform(first)
    assert second == first
