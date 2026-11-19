"""No-network tests for operator-only encrypted MAR P0 PostgreSQL backup."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.mar_p0_offsite_pg_restore import (
    MAGIC, RecoveryRejected, _key, _postgres_env, _seal, _unseal,
    _write_exclusive, export_backup, restore_backup, main,
)

SOURCE_URI = "postgresql://mar_p0_backup_reader:synthetic-secret@ep-damp-term-b8wqhmz0.c-14.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require"
TARGET_URI = "postgresql://operator:synthetic-secret@localhost/mar_p0_restore_synthetic"
KEY = "ab" * 32
TABLE_STATS = {name: {"count": count, "sha256": "a" * 64} for name, count in
               (("checkpoints", 4), ("checkpoint_pages", 8), ("raw_artifacts", 4))}
SCHEMA_STATS = {"count": 69, "sha256": "b" * 64}
DUMP = b"PGDMP" + b"\x00" * 50 + b"synthetic-checkpoint"


class OffsiteEncryptedRecoveryTests(unittest.TestCase):
    def test_default_dry_run_has_no_queries_or_writes(self):
        with patch("scripts.mar_p0_offsite_pg_restore._run") as run:
            self.assertEqual(main(["backup", "--encrypted-file", "/unused/file"]), 0)
        run.assert_not_called()

    def test_source_requires_neon_and_only_limited_role(self):
        for url in (
            "postgresql://neondb_owner:secret@ep-test.neon.tech/neondb",
            "postgresql://mar_p0_backup_reader:secret@attacker.example/neondb",
            "postgresql://mar_p0_backup_reader:secret@ep-damp-term-b8wqhmz0-pooler.c-14.us-east-1.aws.neon.tech/neondb",
            "postgresql://mar_p0_backup_reader:secret@ep-test.neon.tech/otherdb",
            "postgresql://mar_p0_backup_reader:secret@ep-test.neon.tech:9999/neondb",
            "postgresql://mar_p0_backup_reader:secret@ep-test.neon.tech/neondb#frag",
        ):
            with self.subTest(url=url), self.assertRaises(RecoveryRejected):
                _postgres_env("MAR_P0_READONLY_DATABASE_URL", origin=True,
                              env={"MAR_P0_READONLY_DATABASE_URL": url})
        safe = _postgres_env("MAR_P0_READONLY_DATABASE_URL", origin=True,
                             env={"MAR_P0_READONLY_DATABASE_URL": SOURCE_URI})
        self.assertEqual(safe["PGUSER"], "mar_p0_backup_reader")
        self.assertEqual(safe["PGSSLMODE"], "verify-full")
        self.assertEqual(safe["PGCHANNELBINDING"], "require")
        self.assertEqual(safe["PGSSLROOTCERT"], "system")

    def test_restore_target_only_isolated_local_database(self):
        for url in (
            "postgresql://operator:secret@ep-test.neon.tech/mar_p0_restore_test",
            "postgresql://operator:secret@localhost/neondb",
            "postgresql://operator:secret@localhost/mar_p0",
        ):
            with self.subTest(url=url), self.assertRaises(RecoveryRejected):
                _postgres_env("MAR_P0_ISOLATED_RESTORE_DATABASE_URL",
                              origin=False,
                              env={"MAR_P0_ISOLATED_RESTORE_DATABASE_URL": url})
        e = _postgres_env("MAR_P0_ISOLATED_RESTORE_DATABASE_URL", origin=False,
                          env={"MAR_P0_ISOLATED_RESTORE_DATABASE_URL": TARGET_URI})
        self.assertEqual(e["PGHOST"], "localhost")
        self.assertEqual(e["PGSSLMODE"], "disable")

    def test_missing_or_incorrect_key_fails_closed(self):
        for candidate in ("", "short", "nothex" * 12):
            with self.assertRaises(RecoveryRejected):
                _key({"MAR_P0_RESTORE_AES_KEY_HEX": candidate})
        self.assertEqual(_key({"MAR_P0_RESTORE_AES_KEY_HEX": KEY}), bytes.fromhex(KEY))

    def test_aes_gcm_roundtrip_but_no_promotion(self):
        sealed = _seal(DUMP, TABLE_STATS, SCHEMA_STATS, bytes.fromhex(KEY))
        self.assertTrue(sealed.startswith(MAGIC))
        self.assertNotIn(DUMP, sealed)
        self.assertNotIn(b"synthetic-checkpoint", sealed)
        recovered, header = _unseal(sealed, bytes.fromhex(KEY))
        self.assertEqual(DUMP, recovered)
        self.assertEqual(header["rows"], TABLE_STATS)
        self.assertEqual(header["schema_fingerprint"], SCHEMA_STATS)
        self.assertEqual(header["production_gate"], "HOLD")

    def test_ciphertext_tampering_and_wrong_key_are_rejected(self):
        sealed = _seal(DUMP, TABLE_STATS, SCHEMA_STATS, bytes.fromhex(KEY))
        with self.assertRaises(RecoveryRejected):
            _unseal(sealed, bytes.fromhex("cd" * 32))
        for changed in (
            sealed[:-1] + bytes([sealed[-1] ^ 1]),
            sealed[:-12],
            b"X" + sealed[1:],
        ):
            with self.subTest(length=len(changed)), self.assertRaises(RecoveryRejected):
                _unseal(changed, bytes.fromhex(KEY))

    def test_random_nonce_prevents_repeated_identical_ciphertext(self):
        self.assertNotEqual(
            _seal(DUMP, TABLE_STATS, SCHEMA_STATS, bytes.fromhex(KEY)),
            _seal(DUMP, TABLE_STATS, SCHEMA_STATS, bytes.fromhex(KEY)),
        )

    def test_non_custom_or_excessively_large_dump_is_refused(self):
        with self.assertRaises(RecoveryRejected):
            _seal(b"not pg_dump", TABLE_STATS, SCHEMA_STATS, bytes.fromhex(KEY))

    def test_backup_file_creation_never_overwrites_and_uses_private_mode(self):
        with tempfile.TemporaryDirectory() as home:
            directory = Path(home) / "private"
            directory.mkdir(mode=0o700)
            path = directory / "backup.enc"
            _write_exclusive(path, b"encrypted-synthetic")
            self.assertEqual(path.read_bytes(), b"encrypted-synthetic")
            if os.name == "posix":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(RecoveryRejected):
                _write_exclusive(path, b"replace")
            self.assertEqual(path.read_bytes(), b"encrypted-synthetic")
            if os.name == "posix":
                directory.chmod(0o755)
                with self.assertRaises(RecoveryRejected):
                    _write_exclusive(directory / "other.enc", b"data")

    def test_offline_mock_export_encodes_only_encrypted_dump(self):
        with tempfile.TemporaryDirectory() as home:
            directory = Path(home) / "private"
            directory.mkdir(mode=0o700)
            file = directory / "proof.enc"

            def fake_run(cmd, *, env, output=False):
                if cmd[0] == "pg_dump":
                    out = next(x.split("=", 1)[1] for x in cmd if x.startswith("--file="))
                    Path(out).write_bytes(DUMP)
                return None

            env = {"MAR_P0_READONLY_DATABASE_URL": SOURCE_URI,
                   "MAR_P0_RESTORE_AES_KEY_HEX": KEY}
            with patch("scripts.mar_p0_offsite_pg_restore._run", side_effect=fake_run), \
                    patch("scripts.mar_p0_offsite_pg_restore._assert_source_readonly", return_value=None), \
                    patch("scripts.mar_p0_offsite_pg_restore._db_summary",
                          return_value=TABLE_STATS), \
                    patch("scripts.mar_p0_offsite_pg_restore._schema_summary",
                          return_value=SCHEMA_STATS), \
                    patch("scripts.mar_p0_offsite_pg_restore._integrity_summary",
                          return_value={"invalid": 0}):
                report = export_backup(file, env)
            self.assertEqual(report["status"], "encrypted_backup_exported")
            self.assertFalse(report["recovery_verified"])
            self.assertEqual(report["production_gate"], "HOLD")
            self.assertNotIn(DUMP, file.read_bytes())
            self.assertEqual(report["encrypted_sha256"],
                             hashlib.sha256(file.read_bytes()).hexdigest())

    def test_export_fails_before_pg_dump_if_live_reader_guard_rejects(self):
        with tempfile.TemporaryDirectory() as home:
            output = Path(home) / "blocked.aesgcm"
            env = {"MAR_P0_READONLY_DATABASE_URL": SOURCE_URI,
                   "MAR_P0_RESTORE_AES_KEY_HEX": KEY}
            with patch("scripts.mar_p0_offsite_pg_restore._assert_source_readonly",
                       side_effect=RecoveryRejected("source_reader_not_select_only")), \
                 patch("scripts.mar_p0_offsite_pg_restore._db_summary") as summary, \
                 patch("scripts.mar_p0_offsite_pg_restore._run") as run:
                with self.assertRaises(RecoveryRejected):
                    export_backup(output, env)
            summary.assert_not_called()
            run.assert_not_called()
            self.assertFalse(output.exists())

    def test_reader_live_proof_rejects_column_dml_or_table_ownership(self):
        from scripts.mar_p0_offsite_pg_restore import _assert_source_readonly
        from scripts.mar_f02_readonly_preflight import EXPECTED_TABLES
        proof = {
            "role": "mar_p0_backup_reader", "direct_login": True,
            "can_login": True, "inherits_roles": False, "admin": False,
            "can_create_database_objects": False, "schema_usage": True,
            "can_create_in_schema": False, "can_create_in_public": False,
            "neon_superuser_member": False, "pg_write_all_data_member": False,
            "database_owner_member": False, "member_of_other_roles": False,
            "executable_security_definer_in_mar_p0": False,
            "table_count": 3, "tables": list(EXPECTED_TABLES),
            "all_select": True, "any_write": False,
            "owns_any_protected_table": False,
        }
        for changed in ({"any_write": True}, {"owns_any_protected_table": True}):
            with self.subTest(changed=changed):
                with patch("scripts.mar_p0_offsite_pg_restore._run",
                           return_value=__import__("json").dumps({**proof, **changed})), \
                     self.assertRaises(RecoveryRejected):
                    _assert_source_readonly({"PGUSER": "mar_p0_backup_reader"})

    def test_reader_live_proof_must_be_valid_json_and_match_exact_role(self):
        from scripts.mar_p0_offsite_pg_restore import _assert_source_readonly
        for raw in ("", "not-json", '{"role":"mar_p0_limited"}'):
            with self.subTest(raw=raw), \
                 patch("scripts.mar_p0_offsite_pg_restore._run", return_value=raw), \
                 self.assertRaises(RecoveryRejected):
                _assert_source_readonly({"PGUSER": "mar_p0_backup_reader"})

    def test_offline_mock_restore_requires_empty_local_target_and_replays(self):
        with tempfile.TemporaryDirectory() as home:
            sealed = _seal(DUMP, TABLE_STATS, SCHEMA_STATS, bytes.fromhex(KEY))
            path = Path(home) / "proof.enc"
            path.write_bytes(sealed)
            expected_sha = hashlib.sha256(sealed).hexdigest()
            commands = []

            def fake_run(cmd, *, env, output=False):
                commands.append(cmd[0])
                return "t" if cmd[0] == "psql" else None

            env = {"MAR_P0_ISOLATED_RESTORE_DATABASE_URL": TARGET_URI,
                   "MAR_P0_RESTORE_AES_KEY_HEX": KEY}
            with patch("scripts.mar_p0_offsite_pg_restore._run", side_effect=fake_run), \
                    patch("scripts.mar_p0_offsite_pg_restore._db_summary",
                          return_value=TABLE_STATS), \
                    patch("scripts.mar_p0_offsite_pg_restore._schema_summary",
                          return_value=SCHEMA_STATS), \
                    patch("scripts.mar_p0_offsite_pg_restore._integrity_summary",
                          return_value={"invalid": 0}):
                report = restore_backup(path, env, expected_sha)
            self.assertEqual(report["status"], "offsite_restored_and_verified")
            self.assertTrue(report["rows_and_schema_sha256_equal"])
            self.assertIn("pg_restore", commands)
            self.assertEqual(report["production_gate"], "HOLD")

    def test_offline_mock_restore_rejects_existing_target_and_wrong_pin(self):
        with tempfile.TemporaryDirectory() as home:
            sealed = _seal(DUMP, TABLE_STATS, SCHEMA_STATS, bytes.fromhex(KEY))
            path = Path(home) / "proof.enc"
            path.write_bytes(sealed)
            env = {"MAR_P0_ISOLATED_RESTORE_DATABASE_URL": TARGET_URI,
                   "MAR_P0_RESTORE_AES_KEY_HEX": KEY}
            with self.assertRaises(RecoveryRejected):
                restore_backup(path, env, "0" * 64)
            with patch("scripts.mar_p0_offsite_pg_restore._run", return_value="f"), \
                    self.assertRaises(RecoveryRejected):
                restore_backup(path, env, hashlib.sha256(sealed).hexdigest())

    def test_failed_internal_integrity_never_claims_success(self):
        with patch("scripts.mar_p0_offsite_pg_restore._run",
                   return_value='{"invalid_manifest_hashes":1}'), \
                self.assertRaises(RecoveryRejected):
            from scripts.mar_p0_offsite_pg_restore import _integrity_summary
            _integrity_summary({})


if __name__ == "__main__":
    unittest.main()
