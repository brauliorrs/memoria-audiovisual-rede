import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.ape_exports import (
    APE_ANALYTIC_SHEET_TITLES,
    build_ape_analysis_extra_sheets,
    build_ape_analysis_frames,
    write_ape_analysis_outputs,
)
from memoria_audiovisual.output_files import APE_OUTPUT_FILES


class ApeExportsTests(unittest.TestCase):
    def setUp(self):
        self.summary_df = pd.DataFrame(
            [
                {
                    "institution": "Arquivo A",
                    "slug": "a",
                    "integrity_status": "integro",
                    "video_links_found_total": 1,
                    "embedded_video_signals_total": 0,
                    "candidate_internal_pages": 0,
                    "website_available": True,
                    "archive_type": "National archives",
                    "country": "Portugal",
                    "continent": "Europe",
                },
                {
                    "institution": "Arquivo B",
                    "slug": "b",
                    "integrity_status": "restrito",
                    "video_links_found_total": 0,
                    "embedded_video_signals_total": 0,
                    "candidate_internal_pages": 0,
                    "website_available": False,
                    "archive_type": "Municipal archives",
                    "country": "Spain",
                    "continent": "Europe",
                },
            ]
        )
        self.links_df = pd.DataFrame(
            [
                {
                    "institution": "Arquivo A",
                    "slug": "a",
                    "platform": "YouTube",
                    "video_link": "https://youtube.com/watch?v=1",
                    "video_title": "Digitisation project overview",
                    "video_subject": "",
                    "video_description": "",
                    "video_published_at": "2025-12-15",
                    "country": "Portugal",
                    "continent": "Europe",
                }
            ]
        )

    def test_build_ape_analysis_frames_returns_expected_contract(self):
        frames = build_ape_analysis_frames(self.summary_df, self.links_df)

        self.assertEqual(set(frames.keys()), set(APE_ANALYTIC_SHEET_TITLES.keys()))
        self.assertEqual(len(frames["analytic_summary"]), len(self.summary_df))
        self.assertEqual(len(frames["analytic_video_catalog"]), len(self.links_df))
        self.assertEqual(int(frames["visibility_summary"]["total"].sum()), len(self.summary_df))
        self.assertEqual(int(frames["theme_summary"]["total"].sum()), 1)

    def test_build_ape_analysis_extra_sheets_matches_titles(self):
        frames = build_ape_analysis_frames(self.summary_df, self.links_df)
        sheets = build_ape_analysis_extra_sheets(frames)

        self.assertEqual(len(sheets), len(APE_ANALYTIC_SHEET_TITLES))
        self.assertEqual(
            [sheet["title"] for sheet in sheets],
            list(APE_ANALYTIC_SHEET_TITLES.values()),
        )

    def test_write_ape_analysis_outputs_creates_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            write_ape_analysis_outputs(output_dir, self.summary_df, self.links_df)

            for key in APE_ANALYTIC_SHEET_TITLES:
                self.assertTrue((output_dir / APE_OUTPUT_FILES[key]).exists())


if __name__ == "__main__":
    unittest.main()
