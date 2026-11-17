"""A public catalog merge must never trigger network collection by itself."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PipelineActivationGateTests(unittest.TestCase):
    def test_pipeline_is_manual_and_requires_explicit_authorization(self):
        workflow = (ROOT / ".github/workflows/pipeline.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^on:\s*\n\s+workflow_dispatch:")
        self.assertNotRegex(workflow, r"(?m)^\s+push:")
        self.assertNotRegex(workflow, r"(?m)^\s+schedule:")
        self.assertIn("confirm_collection:", workflow)
        self.assertIn("required: true", workflow)
        self.assertIn(
            "github.event.inputs.confirm_collection == 'RUN_AUTHORIZED'",
            workflow,
        )
        self.assertIn("    if: ${{", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)

    def test_quality_still_runs_on_main_push_and_pull_request(self):
        workflow = (ROOT / ".github/workflows/quality.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^\s+pull_request:")
        self.assertRegex(workflow, r"(?m)^\s+push:")
        self.assertIn("      - main", workflow)


if __name__ == "__main__":
    unittest.main()
