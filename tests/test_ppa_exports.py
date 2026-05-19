import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.output_files import PPA_OUTPUT_FILES
from memoria_audiovisual.ppa_exports import (
    PPA_ANALYTIC_SHEET_TITLES,
    build_ppa_analysis_extra_sheets,
    build_ppa_analysis_frames,
    write_ppa_analysis_outputs,
)


class PpaExportsTests(unittest.TestCase):
    def setUp(self):
        self.summary_df = pd.DataFrame(
            [
                {
                    "institution": "Portal Português de Arquivos",
                    "slug": "portal-portugues-arquivos",
                    "integrity_status": "integro",
                    "video_links_found_total": 1,
                    "embedded_video_signals_total": 1,
                    "candidate_internal_pages": 5,
                    "website_available": True,
                    "archive_type": "National archival aggregator",
                    "country": "Portugal",
                    "continent": "Europe",
                }
            ]
        )
        self.links_df = pd.DataFrame(
            [
                {
                    "institution": "Portal Português de Arquivos",
                    "slug": "portal-portugues-arquivos",
                    "platform": "Portal Português de Arquivos",
                    "video_link": "https://portal.arquivos.pt/record?id=oai%3APT%2FMVFX-ARQ%3A303127",
                    "video_title": "Arquivo Audiovisual da RTP",
                    "video_subject": "audiovisual",
                    "video_description": "registro descritivo com ligação à fonte original detectada",
                    "video_published_at": "1957-",
                    "country": "Portugal",
                    "continent": "Europe",
                }
            ]
        )

    def test_build_ppa_analysis_frames_returns_expected_contract(self):
        frames = build_ppa_analysis_frames(self.summary_df, self.links_df)

        self.assertEqual(set(frames.keys()), set(PPA_ANALYTIC_SHEET_TITLES.keys()))
        self.assertEqual(len(frames["analytic_summary"]), len(self.summary_df))
        self.assertEqual(len(frames["analytic_video_catalog"]), len(self.links_df))
        self.assertEqual(int(frames["visibility_summary"]["total"].sum()), len(self.summary_df))

    def test_build_ppa_analysis_extra_sheets_matches_titles(self):
        frames = build_ppa_analysis_frames(self.summary_df, self.links_df)
        sheets = build_ppa_analysis_extra_sheets(frames)

        self.assertEqual(len(sheets), len(PPA_ANALYTIC_SHEET_TITLES))
        self.assertEqual(
            [sheet["title"] for sheet in sheets],
            list(PPA_ANALYTIC_SHEET_TITLES.values()),
        )

    def test_write_ppa_analysis_outputs_creates_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            write_ppa_analysis_outputs(output_dir, self.summary_df, self.links_df)

            for key in PPA_ANALYTIC_SHEET_TITLES:
                self.assertTrue((output_dir / PPA_OUTPUT_FILES[key]).exists())


if __name__ == "__main__":
    unittest.main()
