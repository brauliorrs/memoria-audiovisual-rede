import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.euscreen_exports import build_euscreen_analysis_frames
from memoria_audiovisual.output_files import EUSCREEN_OUTPUT_FILES
from memoria_audiovisual.snapshot_metadata import (
    build_euscreen_snapshot_metadata,
    write_euscreen_snapshot_metadata,
)


class EUscreenSnapshotMetadataTests(unittest.TestCase):
    def setUp(self):
        self.summary_df = pd.DataFrame(
            [
                {
                    "institution": "EUscreen",
                    "slug": "euscreen",
                    "integrity_status": "integro",
                    "video_links_found_total": 1,
                    "embedded_video_signals_total": 1,
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

    def test_build_euscreen_snapshot_metadata_counts_match_inputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_euscreen_analysis_frames(self.summary_df, self.links_df)
            metadata = build_euscreen_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            self.assertEqual(metadata["dataset"], "euscreen")
            self.assertEqual(metadata["counts"]["institutions"], 1)
            self.assertEqual(metadata["counts"]["institutions_with_website"], 1)
            self.assertEqual(metadata["counts"]["institutions_with_video_links"], 1)
            self.assertEqual(metadata["counts"]["video_links_total"], 1)
            self.assertEqual(metadata["counts"]["videos_in_curatorial_catalog"], 1)
            self.assertIn("snapshot_metadata", metadata["files"])

    def test_write_euscreen_snapshot_metadata_creates_json_with_self_manifest(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_euscreen_analysis_frames(self.summary_df, self.links_df)
            payload = write_euscreen_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            metadata_path = output_dir / EUSCREEN_OUTPUT_FILES["snapshot_metadata"]
            self.assertTrue(metadata_path.exists())
            saved_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_payload["generated_by"], "tests")
            self.assertTrue(saved_payload["files"]["snapshot_metadata"]["exists"])
            self.assertGreater(saved_payload["files"]["snapshot_metadata"]["size_bytes"], 0)
            self.assertEqual(saved_payload["counts"], payload["counts"])


if __name__ == "__main__":
    unittest.main()
