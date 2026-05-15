import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.output_files import PARES_OUTPUT_FILES
from memoria_audiovisual.pares_exports import build_pares_analysis_frames
from memoria_audiovisual.snapshot_metadata import (
    build_pares_snapshot_metadata,
    write_pares_snapshot_metadata,
)


class ParesSnapshotMetadataTests(unittest.TestCase):
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
                    "video_link": "https://pares.mcu.es/ParesBusquedas20/catalogo/show/2122306?nm",
                    "video_title": "Archivo audiovisual del Partido Carlista",
                    "video_subject": "audiovisual",
                    "video_description": "objeto digital detectado; registro PARES 2122306",
                    "video_published_at": "",
                    "country": "Spain",
                    "continent": "Europe",
                }
            ]
        )

    def test_build_pares_snapshot_metadata_counts_match_inputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_pares_analysis_frames(self.summary_df, self.links_df)
            metadata = build_pares_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            self.assertEqual(metadata["dataset"], "pares")
            self.assertEqual(metadata["counts"]["institutions"], 1)
            self.assertEqual(metadata["counts"]["institutions_with_website"], 1)
            self.assertEqual(metadata["counts"]["institutions_with_video_links"], 1)
            self.assertEqual(metadata["counts"]["video_links_total"], 1)
            self.assertEqual(metadata["counts"]["videos_in_curatorial_catalog"], 1)
            self.assertIn("snapshot_metadata", metadata["files"])

    def test_write_pares_snapshot_metadata_creates_json_with_self_manifest(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_pares_analysis_frames(self.summary_df, self.links_df)
            payload = write_pares_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            metadata_path = output_dir / PARES_OUTPUT_FILES["snapshot_metadata"]
            self.assertTrue(metadata_path.exists())
            saved_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_payload["generated_by"], "tests")
            self.assertTrue(saved_payload["files"]["snapshot_metadata"]["exists"])
            self.assertGreater(saved_payload["files"]["snapshot_metadata"]["size_bytes"], 0)
            self.assertEqual(saved_payload["counts"], payload["counts"])


if __name__ == "__main__":
    unittest.main()
