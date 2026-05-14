import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.ape_exports import build_ape_analysis_frames
from memoria_audiovisual.output_files import APE_OUTPUT_FILES
from memoria_audiovisual.timeline import write_timeline_outputs


class TimelineOutputsTests(unittest.TestCase):
    def test_timeline_outputs_track_absence_and_recurrent_unavailability(self):
        first_summary_df = pd.DataFrame(
            [
                {
                    "institution": "Arquivo A",
                    "slug": "a",
                    "repository_code": "PT-A",
                    "country": "Portugal",
                    "continent": "Europe",
                    "archive_type": "National archives",
                    "website_available": True,
                    "partner_site": "https://arquivo-a.example",
                    "partner_domain": "arquivo-a.example",
                    "status": "ok",
                    "http_code": 200,
                    "integrity_status": "instavel",
                    "final_url": "https://arquivo-a.example",
                    "video_links_found_total": 0,
                    "embedded_video_signals_total": 0,
                    "candidate_internal_pages": 0,
                },
                {
                    "institution": "Arquivo B",
                    "slug": "b",
                    "repository_code": "PT-B",
                    "country": "Portugal",
                    "continent": "Europe",
                    "archive_type": "Municipal archives",
                    "website_available": True,
                    "partner_site": "https://arquivo-b.example",
                    "partner_domain": "arquivo-b.example",
                    "status": "ok",
                    "http_code": 200,
                    "integrity_status": "integro",
                    "final_url": "https://arquivo-b.example",
                    "video_links_found_total": 1,
                    "embedded_video_signals_total": 0,
                    "candidate_internal_pages": 0,
                },
            ]
        )
        first_links_df = pd.DataFrame(
            [
                {
                    "institution": "Arquivo B",
                    "slug": "b",
                    "platform": "YouTube",
                    "video_link": "https://youtube.com/watch?v=1",
                    "video_title": "Archive B video",
                    "video_subject": "",
                    "video_description": "",
                    "video_published_at": "2025-12-15",
                    "country": "Portugal",
                    "continent": "Europe",
                }
            ]
        )

        second_summary_df = pd.DataFrame(
            [
                {
                    "institution": "Arquivo A",
                    "slug": "a",
                    "repository_code": "PT-A",
                    "country": "Portugal",
                    "continent": "Europe",
                    "archive_type": "National archives",
                    "website_available": True,
                    "partner_site": "https://arquivo-a.example",
                    "partner_domain": "arquivo-a.example",
                    "status": "erro",
                    "http_code": 503,
                    "integrity_status": "instavel",
                    "final_url": "https://arquivo-a.example",
                    "video_links_found_total": 0,
                    "embedded_video_signals_total": 0,
                    "candidate_internal_pages": 0,
                }
            ]
        )
        second_links_df = pd.DataFrame()

        first_analysis_frames = build_ape_analysis_frames(first_summary_df, first_links_df)
        second_analysis_frames = build_ape_analysis_frames(second_summary_df, second_links_df)

        first_snapshot_metadata = {
            "dataset": "ape",
            "observation_key": "ape:2026-01-01T00:00:00Z",
            "generated_at": "2026-01-01T00:00:00Z",
            "source_status_date": "2025-12-15",
            "generated_by": "tests",
            "counts": {},
        }
        second_snapshot_metadata = {
            "dataset": "ape",
            "observation_key": "ape:2026-02-01T00:00:00Z",
            "generated_at": "2026-02-01T00:00:00Z",
            "source_status_date": "2026-01-15",
            "generated_by": "tests",
            "counts": {},
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            write_timeline_outputs(
                output_dir,
                dataset="ape",
                output_files=APE_OUTPUT_FILES,
                snapshot_metadata=first_snapshot_metadata,
                summary_df=first_summary_df,
                analysis_frames=first_analysis_frames,
            )
            timeline_outputs = write_timeline_outputs(
                output_dir,
                dataset="ape",
                output_files=APE_OUTPUT_FILES,
                snapshot_metadata=second_snapshot_metadata,
                summary_df=second_summary_df,
                analysis_frames=second_analysis_frames,
            )

            signals_df = timeline_outputs["extinction_signals"]
            self.assertFalse(signals_df.empty)
            self.assertIn("ausencia_na_rodada_atual", signals_df["signal_type"].tolist())
            self.assertIn("indisponibilidade_digital_reincidente", signals_df["signal_type"].tolist())

            absence_row = signals_df.loc[signals_df["signal_type"] == "ausencia_na_rodada_atual"].iloc[0]
            self.assertEqual(absence_row["slug"], "b")
            self.assertEqual(int(absence_row["rounds_since_last_seen"]), 1)

            recurrent_row = signals_df.loc[
                signals_df["signal_type"] == "indisponibilidade_digital_reincidente"
            ].iloc[0]
            self.assertEqual(recurrent_row["slug"], "a")
            self.assertEqual(int(recurrent_row["consecutive_unavailable_observations"]), 2)


if __name__ == "__main__":
    unittest.main()
