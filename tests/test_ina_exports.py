import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.ina_exports import (
    INA_ANALYTIC_SHEET_TITLES,
    build_ina_analysis_extra_sheets,
    build_ina_analysis_frames,
    write_ina_analysis_outputs,
)
from memoria_audiovisual.output_files import INA_OUTPUT_FILES


class InaExportsTests(unittest.TestCase):
    def setUp(self):
        self.summary_df = pd.DataFrame(
            [
                {
                    "institution": "INA",
                    "slug": "ina",
                    "integrity_status": "integro",
                    "video_links_found_total": 2,
                    "embedded_video_signals_total": 1,
                    "candidate_internal_pages": 2,
                    "website_available": True,
                    "archive_type": "National audiovisual archive",
                    "country": "France",
                    "continent": "Europe",
                }
            ]
        )
        self.links_df = pd.DataFrame(
            [
                {
                    "institution": "INA",
                    "slug": "ina",
                    "platform": "YouTube",
                    "video_link": "https://youtube.com/watch?v=1",
                    "video_title": "INA collection overview",
                    "video_subject": "",
                    "video_description": "",
                    "video_published_at": "2025-01-01",
                    "country": "France",
                    "continent": "Europe",
                }
            ]
        )

    def test_build_ina_analysis_frames_returns_expected_contract(self):
        frames = build_ina_analysis_frames(self.summary_df, self.links_df)

        self.assertEqual(set(frames.keys()), set(INA_ANALYTIC_SHEET_TITLES.keys()))
        self.assertEqual(len(frames["analytic_summary"]), len(self.summary_df))
        self.assertEqual(len(frames["analytic_video_catalog"]), len(self.links_df))
        self.assertEqual(int(frames["visibility_summary"]["total"].sum()), len(self.summary_df))
        self.assertEqual(int(frames["theme_summary"]["total"].sum()), 1)

    def test_build_ina_analysis_extra_sheets_matches_titles(self):
        frames = build_ina_analysis_frames(self.summary_df, self.links_df)
        sheets = build_ina_analysis_extra_sheets(frames)

        self.assertEqual(len(sheets), len(INA_ANALYTIC_SHEET_TITLES))
        self.assertEqual(
            [sheet["title"] for sheet in sheets],
            list(INA_ANALYTIC_SHEET_TITLES.values()),
        )

    def test_write_ina_analysis_outputs_creates_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            write_ina_analysis_outputs(output_dir, self.summary_df, self.links_df)

            for key in INA_ANALYTIC_SHEET_TITLES:
                self.assertTrue((output_dir / INA_OUTPUT_FILES[key]).exists())


if __name__ == "__main__":
    unittest.main()
