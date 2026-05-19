import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.output_files import PPA_OUTPUT_FILES
from memoria_audiovisual.ppa_exports import build_ppa_analysis_frames
from memoria_audiovisual.snapshot_metadata import (
    build_ppa_snapshot_metadata,
    write_ppa_snapshot_metadata,
)


class PpaSnapshotMetadataTests(unittest.TestCase):
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

    def test_build_ppa_snapshot_metadata_counts_match_inputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_ppa_analysis_frames(self.summary_df, self.links_df)
            metadata = build_ppa_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            self.assertEqual(metadata["dataset"], "portal-portugues-arquivos")
            self.assertEqual(metadata["counts"]["institutions"], 1)
            self.assertEqual(metadata["counts"]["institutions_with_website"], 1)
            self.assertEqual(metadata["counts"]["institutions_with_video_links"], 1)
            self.assertEqual(metadata["counts"]["video_links_total"], 1)
            self.assertEqual(metadata["counts"]["videos_in_curatorial_catalog"], 1)
            self.assertIn("snapshot_metadata", metadata["files"])

    def test_write_ppa_snapshot_metadata_creates_json_with_self_manifest(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analysis_frames = build_ppa_analysis_frames(self.summary_df, self.links_df)
            payload = write_ppa_snapshot_metadata(
                output_dir,
                summary_df=self.summary_df,
                links_df=self.links_df,
                analysis_frames=analysis_frames,
                generated_by="tests",
            )

            metadata_path = output_dir / PPA_OUTPUT_FILES["snapshot_metadata"]
            self.assertTrue(metadata_path.exists())
            saved_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_payload["generated_by"], "tests")
            self.assertTrue(saved_payload["files"]["snapshot_metadata"]["exists"])
            self.assertGreater(saved_payload["files"]["snapshot_metadata"]["size_bytes"], 0)
            self.assertEqual(saved_payload["counts"], payload["counts"])


if __name__ == "__main__":
    unittest.main()
