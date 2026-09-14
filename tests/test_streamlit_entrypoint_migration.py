import unittest

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


class StreamlitEntrypointMigrationTests(unittest.TestCase):
    def test_transform_adds_imports_and_modular_navigation(self):
        transformed = transform_entrypoint(_legacy_source())

        self.assertIn(NAVIGATION_IMPORT, transformed)
        self.assertIn(INFRASTRUCTURE_IMPORT, transformed)
        self.assertIn(MODULAR_NAVIGATION_BLOCK, transformed)
        self.assertNotIn(LEGACY_NAVIGATION_BLOCK, transformed)
        validate_transformed_source(transformed)

    def test_transform_is_idempotent(self):
        first = transform_entrypoint(_legacy_source())
        second = transform_entrypoint(first)
        self.assertEqual(second, first)

    def test_transform_rejects_unknown_structure(self):
        with self.assertRaisesRegex(RuntimeError, "Bloco legado"):
            transform_entrypoint(
                "from memoria_audiovisual.output_files import list_output_filenames\n"
            )

    def test_validation_rejects_partial_integration(self):
        with self.assertRaisesRegex(RuntimeError, "Integração incompleta"):
            validate_transformed_source(NAVIGATION_IMPORT + INFRASTRUCTURE_IMPORT)


if __name__ == "__main__":
    unittest.main()
