"""Neon registry facade: safety, stable hashes, pagination and fail-closed roles."""
import unittest
from types import SimpleNamespace

from memoria_audiovisual.corpus_admission_engine import REGISTRY
from memoria_audiovisual.corpus_registry_pg import (
    RegistryDrift, connector_digest, list_corpora,
    list_corpus_events, read_only_role_assertion,
    sync_registered_connectors,
)


class DummyCursor:
    def __init__(self, grant=None, initial=None, *, readonly=False):
        self.grant = grant
        self.records = dict(initial or {})
        self.readonly = readonly
        self.last = ""
        self.calls = []
        self.current = None
        self.event_log = []
        self.list_result = []
        self.total = 0

    def execute(self, sql, params=()):
        self.last = sql
        self.calls.append((sql, params))
        if "pg_has_role" in sql and "has_table_privilege" in sql:
            self.current = (True, False, False, False) if self.readonly else (True, True, False, False)
        elif "pg_has_role" in sql:
            self.current = (self.grant,)
        elif sql.startswith("SELECT spec_sha256"):
            val = self.records.get(params[0])
            self.current = (val,) if val is not None else None
        elif sql.startswith("INSERT INTO mar_corpora.connector_registry"):
            self.records[params[0]] = params[-1]
        elif sql.startswith("INSERT INTO mar_corpora.audit_events"):
            self.event_log.append(params)
        elif sql.startswith("SELECT count(*)"):
            self.current = (self.total,)

    def fetchone(self):
        return self.current

    def fetchall(self):
        return self.list_result

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class DummyConnection:
    def __init__(self, cursor):
        self.dummy = cursor

    def transaction(self):
        return self

    def cursor(self):
        return self.dummy

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class RegistryPgTests(unittest.TestCase):
    def test_fingerprint_is_deterministic(self):
        self.assertEqual(connector_digest(REGISTRY["eye"]),
                         connector_digest(REGISTRY["eye"]))
        self.assertEqual(len(connector_digest(REGISTRY["ciclic"])), 64)

    def test_operator_sync_inserts_only_register_state_and_is_idempotent(self):
        cursor = DummyCursor(grant=True)
        conn = DummyConnection(cursor)
        result = sync_registered_connectors(conn)
        self.assertEqual(result, {"inserted": 5, "unchanged": 0, "total": 5})
        self.assertEqual(len(cursor.records), 5)
        self.assertEqual(len(cursor.event_log), 5)
        self.assertTrue(all("registry-sync" in sql for sql, _ in cursor.calls
                            if sql.startswith("INSERT INTO mar_corpora.audit_events")))
        for sql, _ in cursor.calls:
            self.assertNotIn("approved_for_publication", sql)
        result2 = sync_registered_connectors(conn)
        self.assertEqual(result2, {"inserted": 0, "unchanged": 5, "total": 5})
        self.assertEqual(len(cursor.event_log), 5)

    def test_sync_rejects_role_without_insert_grant(self):
        cursor = DummyCursor(grant=False)
        with self.assertRaises(PermissionError):
            sync_registered_connectors(DummyConnection(cursor))
        self.assertFalse(cursor.records)

    def test_sync_rejects_hash_drift_without_mutating(self):
        cursor = DummyCursor(grant=True, initial={"eye": "0" * 64})
        with self.assertRaises(RegistryDrift):
            sync_registered_connectors(DummyConnection(cursor))
        self.assertEqual(cursor.records["eye"], "0" * 64)

    def test_paged_search_is_parameterized_and_bounded(self):
        cursor = DummyCursor(readonly=True)
        cursor.total = 150
        conn = DummyConnection(cursor)
        result = list_corpora(conn, search="%' OR 1=1 --",
                              stage="registered", page=2, page_size=25)
        self.assertEqual((result["page"], result["total"]), (2, 150))
        self.assertEqual(len(cursor.calls), 2)
        self.assertTrue(all(sql.startswith("SELECT") for sql, _ in cursor.calls))
        self.assertNotIn("OR 1=1", cursor.calls[0][0])
        self.assertIn("OR 1=1", cursor.calls[0][1][0])
        self.assertEqual(cursor.calls[1][1][-2:], (25, 25))
        for kwargs in ({"page": 0}, {"page_size": 51}, {"page": True},
                       {"search": "a" * 121}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                list_corpora(conn, **kwargs)

    def test_audit_events_only_select_and_require_registered_code(self):
        cursor = DummyCursor(readonly=True)
        out = list_corpus_events(DummyConnection(cursor), "eye")
        self.assertEqual(out, [])
        self.assertTrue(cursor.last.startswith("SELECT"))
        with self.assertRaises(ValueError):
            list_corpus_events(DummyConnection(cursor), "ape")

    def test_read_only_role_must_not_have_write_privileges(self):
        cursor = DummyCursor(readonly=True)
        read_only_role_assertion(DummyConnection(cursor))
        with self.assertRaises(PermissionError):
            read_only_role_assertion(DummyConnection(DummyCursor(readonly=False)))


if __name__ == "__main__":
    unittest.main()
