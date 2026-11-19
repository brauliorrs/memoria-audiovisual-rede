"""MAR F02: adversarial checks for live reader authorization without connecting CI."""
from __future__ import annotations

import copy
import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock

from scripts import mar_f02_readonly_preflight as gate


OK = {
    "role": gate.EXPECTED_ROLE,
    "direct_login": True, "can_login": True, "inherits_roles": False,
    "admin": False, "can_create_database_objects": False,
    "schema_usage": True, "can_create_in_schema": False,
    "can_create_in_public": False, "neon_superuser_member": False,
    "pg_write_all_data_member": False, "database_owner_member": False,
    "table_count": 3, "tables": list(gate.EXPECTED_TABLES),
    "all_select": True, "any_write": False,
}


class F02ReaderPreflightTests(unittest.TestCase):
    def doc(self):
        return copy.deepcopy(OK)

    def test_valid_dedicated_login_metadata_passes_only_credential_check(self):
        self.assertEqual(gate.assess(self.doc()), [])

    def test_cannot_reuse_checkpoint_writer_name(self):
        for name in ("mar_p0_limited", "neondb_owner", "mar_p0_reader", ""):
            with self.subTest(name=name):
                doc = self.doc()
                doc["role"] = name
                self.assertTrue(gate.assess(doc))

    def test_dml_grant_always_blocks(self):
        doc = self.doc()
        doc["any_write"] = True
        self.assertIn("any_write_must_be_false", gate.assess(doc))

    def test_neon_superuser_or_owner_membership_blocks(self):
        for name in ("neon_superuser_member", "database_owner_member", "pg_write_all_data_member"):
            with self.subTest(name=name):
                doc = self.doc()
                doc[name] = True
                self.assertTrue(gate.assess(doc))

    def test_admin_and_create_permissions_block(self):
        for name in ("admin", "can_create_database_objects", "can_create_in_schema",
                     "can_create_in_public", "inherits_roles"):
            with self.subTest(name=name):
                doc = self.doc()
                doc[name] = True
                self.assertTrue(gate.assess(doc))

    def test_no_passwordless_catalog_role_or_set_role(self):
        for name in ("direct_login", "can_login", "schema_usage", "all_select"):
            with self.subTest(name=name):
                doc = self.doc()
                doc[name] = False
                self.assertTrue(gate.assess(doc))

    def test_missing_or_extra_tables_fail_closed(self):
        for tables in (
            [], ["checkpoints"], ["checkpoint_pages", "checkpoints"],
            list(gate.EXPECTED_TABLES) + ["unexpected"],
            ["raw_artifacts", "checkpoint_pages", "checkpoints"],
        ):
            with self.subTest(tables=tables):
                doc = self.doc()
                doc["tables"] = tables
                self.assertTrue(gate.assess(doc))

    def test_wrong_table_count_or_bool_fails(self):
        for count in (0, 1, 4, True, "3", None):
            with self.subTest(count=count):
                doc = self.doc()
                doc["table_count"] = count
                self.assertTrue(gate.assess(doc))

    def test_bad_or_missing_reports_fail(self):
        self.assertTrue(gate.assess(None))
        self.assertTrue(gate.assess({}))
        doc = self.doc()
        del doc["any_write"]
        self.assertTrue(gate.assess(doc))

    def test_dry_run_has_zero_database_calls(self):
        with patch.object(gate, "run_psql") as run, io.StringIO() as output, redirect_stdout(output):
            self.assertEqual(gate.main([]), 0)
            self.assertEqual(json.loads(output.getvalue())["database_requests"], 0)
            run.assert_not_called()

    def test_executed_denial_has_nonzero_exit_and_no_raw_report_leak(self):
        doc = self.doc()
        doc["any_write"] = True
        with patch.object(gate, "run_psql", return_value=doc), io.StringIO() as output, redirect_stdout(output):
            self.assertEqual(gate.main(["--execute"]), 2)
            printed = output.getvalue()
            self.assertNotIn("mar_p0_backup_reader", printed)
            self.assertEqual(json.loads(printed)["status"], "HOLD")

    def test_successful_check_never_authorizes_production(self):
        with patch.object(gate, "run_psql", return_value=self.doc()), io.StringIO() as output, redirect_stdout(output):
            self.assertEqual(gate.main(["--execute"]), 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["production_authorized"])

    def test_subprocess_uses_no_url_or_password_in_argv(self):
        returned = MagicMock()
        returned.returncode = 0
        returned.stdout = json.dumps(self.doc())
        with patch.object(subprocess, "run", return_value=returned) as runner:
            self.assertEqual(gate.run_psql(), self.doc())
        args, kwargs = runner.call_args
        command = args[0]
        self.assertEqual(command[0], "psql")
        self.assertNotIn("PGPASSWORD", " ".join(command))
        self.assertNotIn("MAR_P0", " ".join(command))
        self.assertTrue(kwargs["capture_output"])

    def test_db_error_message_never_echoed(self):
        mocked = MagicMock()
        mocked.returncode = 1
        mocked.stdout = ""
        mocked.stderr = "postgresql://leaked-secret?password=supersecret"
        with patch.object(subprocess, "run", return_value=mocked), self.assertRaises(RuntimeError) as caught:
            gate.run_psql()
        self.assertEqual(str(caught.exception), "database_check_rejected")
        self.assertNotIn("supersecret", str(caught.exception))

    def test_failing_psql_or_bad_json_rejected(self):
        with patch.object(subprocess, "run", side_effect=OSError("host-secret")):
            with self.assertRaises(RuntimeError):
                gate.run_psql()
        mocked = MagicMock()
        mocked.returncode = 0
        mocked.stdout = "non-json"
        with patch.object(subprocess, "run", return_value=mocked):
            with self.assertRaises(RuntimeError):
                gate.run_psql()

    def test_sql_checks_all_six_write_privileges(self):
        for permission in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"):
            self.assertIn("'" + permission + "'", gate.SQL)
        self.assertNotIn("SELECT * FROM mar_p0", gate.SQL)


if __name__ == "__main__":
    unittest.main()
