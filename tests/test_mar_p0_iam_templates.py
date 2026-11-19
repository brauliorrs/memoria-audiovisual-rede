"""Validate public IAM/OIDC policy templates offline without contacting AWS."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "infra/aws"
PREFIX = "arn:aws:s3:::REPLACE_WITH_PRIVATE_BUCKET_NAME/mar-p0/validation/*"


def load(name):
    return json.loads((ROOT / ("mar-p0-backup-" + name + ".template.json")).read_text())


class IAMTemplatesTests(unittest.TestCase):
    def test_all_templates_parse_as_valid_json(self):
        names = ("upload-role-policy", "restore-role-policy",
                 "upload-trust", "restore-trust", "bucket-policy")
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(load(name)["Version"], "2012-10-17")

    def test_oidc_trust_is_scoped_by_exact_repo_environment(self):
        for kind, env in (("upload", "mar-p0-backup-automation"),
                          ("restore", "mar-p0-restore-automation")):
            with self.subTest(kind=kind):
                rule = load(kind + "-trust")["Statement"][0]
                self.assertEqual(rule["Action"], "sts:AssumeRoleWithWebIdentity")
                eq = rule["Condition"]["StringEquals"]
                self.assertEqual(eq["token.actions.githubusercontent.com:aud"], "sts.amazonaws.com")
                self.assertEqual(
                    eq["token.actions.githubusercontent.com:sub"],
                    "repo:brauliorrs/memoria-audiovisual-rede:environment:" + env,
                )
                self.assertNotIn("*", eq["token.actions.githubusercontent.com:sub"])

    def test_export_role_can_write_only_under_prefix(self):
        rules = load("upload-role-policy")["Statement"]
        allow = [x for x in rules if x["Effect"] == "Allow"]
        writes = [x for x in allow if "s3:PutObject" in x["Action"]]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0]["Resource"], PREFIX)
        self.assertIn("s3:PutObjectRetention", writes[0]["Action"])
        self.assertNotIn("s3:GetObject", str(allow))
        self.assertNotIn("s3:DeleteObject", str(allow))

    def test_restore_role_cannot_write_or_delete(self):
        rules = load("restore-role-policy")["Statement"]
        allow = [x for x in rules if x["Effect"] == "Allow"]
        self.assertNotIn("s3:PutObject", str(allow))
        self.assertNotIn("s3:DeleteObject", str(allow))
        self.assertTrue(any("s3:GetObjectVersion" in x["Action"] and x["Resource"] == PREFIX
                            for x in allow))
        deny = [x for x in rules if x["Effect"] == "Deny"]
        self.assertTrue(any("s3:PutObject" in x["Action"] for x in deny))

    def test_bucket_policy_denies_http_and_scheduled_delete(self):
        rules = load("bucket-policy")["Statement"]
        self.assertTrue(all(x["Effect"] == "Deny" for x in rules))
        self.assertTrue(any(x.get("Condition", {}).get("Bool", {}).get(
            "aws:SecureTransport") == "false" for x in rules))
        self.assertTrue(any("s3:DeleteObjectVersion" in x["Action"] for x in rules))

    def test_templates_require_operator_provisioning(self):
        for file in ROOT.glob("mar-p0-backup-*.template.json"):
            with self.subTest(file=file.name):
                body = file.read_text()
                self.assertIn("REPLACE_WITH_", body)
                self.assertNotIn("secretAccessKey", body)
                self.assertNotIn("aws_secret_access_key", body)


if __name__ == "__main__":
    unittest.main()
