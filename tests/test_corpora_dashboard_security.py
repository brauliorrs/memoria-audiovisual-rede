"""Admin console is separate, OIDC-gated and never renders before auth."""
import unittest
from pathlib import Path
from types import SimpleNamespace

from admin.corpora_dashboard import authorized_admin

ROOT = Path(__file__).resolve().parents[1]


class CorpusDashboardSafetyTests(unittest.TestCase):
    def test_deny_missing_identity_provider_verification_or_allowlist(self):
        cases = [
            ({"is_logged_in": False, "email_verified": True, "email": "admin@example.org"}, "admin@example.org"),
            ({"is_logged_in": True, "email_verified": False, "email": "admin@example.org"}, "admin@example.org"),
            ({"is_logged_in": True, "email_verified": True, "email": "other@example.org"}, "admin@example.org"),
            ({"is_logged_in": True, "email_verified": True, "email": "admin@example.org"}, ""),
            ({}, "admin@example.org"),
        ]
        for user, allowlist in cases:
            with self.subTest(user=user, allowlist=allowlist):
                self.assertFalse(authorized_admin(user, allowlist))

    def test_allow_explicit_verified_oidc_identity(self):
        self.assertTrue(authorized_admin(
            {"is_logged_in": True, "email_verified": True, "email": "ADMIN@example.org"},
            "other@example.org,admin@example.org",
        ))
        user = SimpleNamespace(is_logged_in=True, email_verified=True,
                               email="admin@example.org")
        self.assertTrue(authorized_admin(user, "admin@example.org"))

    def test_entrypoint_never_appears_in_public_app(self):
        source = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
        self.assertNotIn("admin.corpora_dashboard", source)
        admin = (ROOT / "admin" / "corpora_dashboard.py").read_text()
        self.assertIn("read_only_role_assertion(conn)", admin)
        self.assertIn("if not authorized_admin(st.user, allowlist)", admin)
        self.assertIn("st.stop()", admin)
        self.assertNotIn("sync_registered_connectors(", admin)
        self.assertNotIn("st.download_button", admin)

    def test_migration_does_not_claim_worm_or_create_scientific_approval(self):
        sql = (ROOT / "sql" / "migrations" /
               "20261116_mar_corpora_audit_v1.sql").read_text()
        self.assertIn("CREATE SCHEMA IF NOT EXISTS mar_corpora", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS mar_corpora.audit_events", sql)
        self.assertIn("CREATE TRIGGER mar_corpora_audit_immutable", sql)
        self.assertIn("false AS publication_authorized", sql)
        self.assertIn("NOLOGIN", sql)
        guard = (ROOT / "sql" / "migrations" /
                 "20261116_mar_corpora_attestation_guard_v1.sql").read_text()
        self.assertIn("'USAGE'", guard)
        self.assertNotIn("'member'", guard)
        self.assertIn("REVOKE ALL ON ALL TABLES", sql)
        self.assertNotIn("DROP TABLE", sql)
        self.assertNotIn("neon_auth.", sql)
        self.assertNotIn("mar_p0.", sql)


if __name__ == "__main__":
    unittest.main()
