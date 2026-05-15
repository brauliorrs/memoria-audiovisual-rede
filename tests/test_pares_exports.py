import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.output_files import PARES_OUTPUT_FILES
from memoria_audiovisual.pares_exports import (
    PARES_ANALYTIC_SHEET_TITLES,
    build_pares_analysis_extra_sheets,
    build_pares_analysis_frames,
    write_pares_analysis_outputs,
)


class ParesExportsTests(unittest.TestCase):
    def setUp(self):
        self.summary_df = pd.DataFrame(
            [
                {
                    "institution": "PARES",
                    "slug": "pares",
                    "integrity_status": "integro",
                    "video_links_found_total": 2,
                    "embedded_video_signals_total": 1,
                    "candidate_internal_pages": 4,
                    "website_available": True,
                    "archive_type": "National archival aggregator",
                    "country": "Spain",
                    "continent": "Europe",
                }
            ]
        )
        self.links_df = pd.DataFrame(
            [
                {
                    "institution": "PARES",
                    "slug": "pares",
                    "platform": "PARES",
                    "video_link": "https://pares.mcu.es/ParesBusquedas20/catalogo/description/2122299?nm",
                    "video_title": "Archivo audiovisual del Partido Carlista",
                    "video_subject": "audiovisual",
                    "video_description": "objeto digital detectado; registro PARES 2122299",
                    "video_published_at": "",
                    "country": "Spain",
                    "continent": "Europe",
                }
            ]
        )

    def test_build_pares_analysis_frames_returns_expected_contract(self):
        frames = build_pares_analysis_frames(self.summary_df, self.links_df)

        self.assertEqual(set(frames.keys()), set(PARES_ANALYTIC_SHEET_TITLES.keys()))
        self.assertEqual(len(frames["analytic_summary"]), len(self.summary_df))
        self.assertEqual(len(frames["analytic_video_catalog"]), len(self.links_df))
        self.assertEqual(int(frames["visibility_summary"]["total"].sum()), len(self.summary_df))

    def test_build_pares_analysis_extra_sheets_matches_titles(self):
        frames = build_pares_analysis_frames(self.summary_df, self.links_df)
        sheets = build_pares_analysis_extra_sheets(frames)

        self.assertEqual(len(sheets), len(PARES_ANALYTIC_SHEET_TITLES))
        self.assertEqual(
            [sheet["title"] for sheet in sheets],
            list(PARES_ANALYTIC_SHEET_TITLES.values()),
        )

    def test_write_pares_analysis_outputs_creates_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            write_pares_analysis_outputs(output_dir, self.summary_df, self.links_df)

            for key in PARES_ANALYTIC_SHEET_TITLES:
                self.assertTrue((output_dir / PARES_OUTPUT_FILES[key]).exists())


if __name__ == "__main__":
    unittest.main()
