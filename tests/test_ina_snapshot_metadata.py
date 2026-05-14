import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.ina_exports import build_ina_analysis_frames
from memoria_audiovisual.output_files import INA_OUTPUT_FILES
from memoria_audiovisual.snapshot_metadata import build_ina_snapshot_metadata
from memoria_audiovisual.snapshot_metadata import write_ina_snapshot_metadata


class InaSnapshotMetadataTests(unittest.TestCase):
    def setUp(self):
        self.summary_df = pd.DataFrame(
            [
                {
                    "institution": "INA",
                    "slug": "ina",
                    "integrity_status": "integro",
                    "video_links_found_total": 1,
                    "embedded_video_signals_total": 1,
                    "candidate_internal_pages": 1,
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

    def test_build_ina_snapshot_metadata_counts_match_inputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_ina_analysis_frames(self.summary_df, self.links_df)
            metadata = build_ina_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            self.assertEqual(metadata["dataset"], "ina")
            self.assertEqual(metadata["counts"]["institutions"], 1)
            self.assertEqual(metadata["counts"]["institutions_with_website"], 1)
            self.assertEqual(metadata["counts"]["institutions_with_video_links"], 1)
            self.assertEqual(metadata["counts"]["video_links_total"], 1)
            self.assertEqual(metadata["counts"]["videos_in_curatorial_catalog"], 1)
            self.assertIn("snapshot_metadata", metadata["files"])

    def test_write_ina_snapshot_metadata_creates_json_with_self_manifest(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_ina_analysis_frames(self.summary_df, self.links_df)
            payload = write_ina_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            metadata_path = output_dir / INA_OUTPUT_FILES["snapshot_metadata"]
            self.assertTrue(metadata_path.exists())
            saved_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_payload["generated_by"], "tests")
            self.assertTrue(saved_payload["files"]["snapshot_metadata"]["exists"])
            self.assertGreater(saved_payload["files"]["snapshot_metadata"]["size_bytes"], 0)
            self.assertEqual(saved_payload["counts"], payload["counts"])


if __name__ == "__main__":
    unittest.main()
