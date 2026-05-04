import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.ape_exports import build_ape_analysis_frames
from memoria_audiovisual.output_files import APE_OUTPUT_FILES
from memoria_audiovisual.snapshot_metadata import build_ape_snapshot_metadata
from memoria_audiovisual.snapshot_metadata import write_ape_snapshot_metadata


class SnapshotMetadataTests(unittest.TestCase):
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
                    "integrity_status": "acessivel",
                    "video_links_found_total": 0,
                    "embedded_video_signals_total": 1,
                    "candidate_internal_pages": 1,
                    "website_available": True,
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

    def test_build_snapshot_metadata_counts_match_inputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_ape_analysis_frames(self.summary_df, self.links_df)
            metadata = build_ape_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            self.assertEqual(metadata["dataset"], "ape")
            self.assertEqual(metadata["source_status_date"], "2025-12-15")
            self.assertEqual(metadata["counts"]["institutions"], 2)
            self.assertEqual(metadata["counts"]["institutions_with_website"], 2)
            self.assertEqual(metadata["counts"]["institutions_with_video_links"], 1)
            self.assertEqual(metadata["counts"]["video_links_total"], 1)
            self.assertEqual(metadata["counts"]["videos_in_curatorial_catalog"], 1)
            self.assertIn("snapshot_metadata", metadata["files"])

    def test_write_snapshot_metadata_creates_json_with_self_manifest(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_ape_analysis_frames(self.summary_df, self.links_df)
            payload = write_ape_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            metadata_path = output_dir / APE_OUTPUT_FILES["snapshot_metadata"]
            self.assertTrue(metadata_path.exists())
            saved_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_payload["generated_by"], "tests")
            self.assertTrue(saved_payload["files"]["snapshot_metadata"]["exists"])
            self.assertGreater(saved_payload["files"]["snapshot_metadata"]["size_bytes"], 0)
            self.assertEqual(saved_payload["counts"], payload["counts"])


if __name__ == "__main__":
    unittest.main()
