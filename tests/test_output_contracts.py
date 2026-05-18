import unittest

from memoria_audiovisual.dashboard_data import DASHBOARD_SOURCE_KEYS
from memoria_audiovisual.output_files import (
    APE_OUTPUT_FILES,
    EUSCREEN_OUTPUT_FILES,
    EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
    EUROPEANA_OUTPUT_FILES,
    INA_OUTPUT_FILES,
    PARES_OUTPUT_FILES,
    list_ape_output_filenames,
    list_euscreen_output_filenames,
    list_european_film_gateway_output_filenames,
    list_europeana_output_filenames,
    list_ina_output_filenames,
    list_pares_output_filenames,
)


class OutputContractsTests(unittest.TestCase):
    def test_dashboard_source_keys_exist_in_output_manifest(self):
        for key in DASHBOARD_SOURCE_KEYS:
            self.assertIn(key, APE_OUTPUT_FILES)
            self.assertIn(key, EUROPEAN_FILM_GATEWAY_OUTPUT_FILES)
            self.assertIn(key, EUROPEANA_OUTPUT_FILES)

    def test_output_manifest_values_are_unique(self):
        filenames = list_ape_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, APE_OUTPUT_FILES)

    def test_ina_output_manifest_values_are_unique(self):
        filenames = list_ina_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_ina_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, INA_OUTPUT_FILES)

    def test_euscreen_output_manifest_values_are_unique(self):
        filenames = list_euscreen_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_euscreen_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, EUSCREEN_OUTPUT_FILES)

    def test_pares_output_manifest_values_are_unique(self):
        filenames = list_pares_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_european_film_gateway_output_manifest_values_are_unique(self):
        filenames = list_european_film_gateway_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_europeana_output_manifest_values_are_unique(self):
        filenames = list_europeana_output_filenames()
        self.assertEqual(len(filenames), len(set(filenames)))

    def test_pares_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, PARES_OUTPUT_FILES)

    def test_european_film_gateway_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, EUROPEAN_FILM_GATEWAY_OUTPUT_FILES)

    def test_europeana_required_report_files_exist_in_manifest(self):
        for key in [
            "report_json",
            "report_txt",
            "report_xlsx",
            "snapshot_metadata",
            "timeline_corpus",
            "timeline_institutions",
            "extinction_signals",
        ]:
            self.assertIn(key, EUROPEANA_OUTPUT_FILES)


if __name__ == "__main__":
    unittest.main()
