import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.euscreen_exports import (
    EUSCREEN_ANALYTIC_SHEET_TITLES,
    build_euscreen_analysis_extra_sheets,
    build_euscreen_analysis_frames,
    write_euscreen_analysis_outputs,
)
from memoria_audiovisual.output_files import EUSCREEN_OUTPUT_FILES


class EUscreenExportsTests(unittest.TestCase):
    def setUp(self):
        self.summary_df = pd.DataFrame(
            [
                {
                    "institution": "EUscreen",
                    "slug": "euscreen",
                    "integrity_status": "integro",
                    "video_links_found_total": 2,
                    "embedded_video_signals_total": 2,
                    "candidate_internal_pages": 6,
                    "website_available": True,
                    "archive_type": "European audiovisual aggregator",
                    "country": "Netherlands",
                    "continent": "Europe",
                }
            ]
        )
        self.links_df = pd.DataFrame(
            [
                {
                    "institution": "EUscreen",
                    "slug": "euscreen",
                    "platform": "EUscreen",
                    "video_link": "https://www.euscreen.eu/?page_id=388&item_id=EUS_1",
                    "video_title": "Opening of the Nuremberg trials",
                    "video_subject": "INA",
                    "video_description": "The first session of the Nuremberg trials.",
                    "video_published_at": "",
                    "country": "Netherlands",
                    "continent": "Europe",
                }
            ]
        )

    def test_build_euscreen_analysis_frames_returns_expected_contract(self):
        frames = build_euscreen_analysis_frames(self.summary_df, self.links_df)

        self.assertEqual(set(frames.keys()), set(EUSCREEN_ANALYTIC_SHEET_TITLES.keys()))
        self.assertEqual(len(frames["analytic_summary"]), len(self.summary_df))
        self.assertEqual(len(frames["analytic_video_catalog"]), len(self.links_df))
        self.assertEqual(int(frames["visibility_summary"]["total"].sum()), len(self.summary_df))
        self.assertEqual(int(frames["theme_summary"]["total"].sum()), 1)

    def test_build_euscreen_analysis_extra_sheets_matches_titles(self):
        frames = build_euscreen_analysis_frames(self.summary_df, self.links_df)
        sheets = build_euscreen_analysis_extra_sheets(frames)

        self.assertEqual(len(sheets), len(EUSCREEN_ANALYTIC_SHEET_TITLES))
        self.assertEqual(
            [sheet["title"] for sheet in sheets],
            list(EUSCREEN_ANALYTIC_SHEET_TITLES.values()),
        )

    def test_write_euscreen_analysis_outputs_creates_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            write_euscreen_analysis_outputs(output_dir, self.summary_df, self.links_df)

            for key in EUSCREEN_ANALYTIC_SHEET_TITLES:
                self.assertTrue((output_dir / EUSCREEN_OUTPUT_FILES[key]).exists())


if __name__ == "__main__":
    unittest.main()
