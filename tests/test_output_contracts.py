import unittest

from memoria_audiovisual.dashboard_data import DASHBOARD_SOURCE_KEYS
from memoria_audiovisual.output_files import APE_OUTPUT_FILES, list_ape_output_filenames


class OutputContractsTests(unittest.TestCase):
    def test_dashboard_source_keys_exist_in_output_manifest(self):
        for key in DASHBOARD_SOURCE_KEYS:
            self.assertIn(key, APE_OUTPUT_FILES)

    def test_output_manifest_values_are_unique(self):
        filenames = list_ape_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_required_report_files_exist_in_manifest(self):
        for key in ["report_json", "report_txt", "report_xlsx", "snapshot_metadata"]:
            self.assertIn(key, APE_OUTPUT_FILES)


if __name__ == "__main__":
    unittest.main()
