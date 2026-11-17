"""Neon registry facade: safety, stable hashes, pagination and fail-closed roles."""
import unittest

from memoria_audiovisual.corpus_admission_engine import REGISTRY
from memoria_audiovisual.corpus_registry_pg import (
    RegistryDrift, connector_digest, list_corpora,
    list_corpus_events, read_only_role_assertion,
    sync_registered_connectors, record_technical_observation,
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
        if "has_schema_privilege" in sql and "mar_corpora.current_status" in sql:
            self.current = (True,) * 13 if self.readonly else (
                True, False, True, True, True, True, True,
                True, False, True, True, True, True,
            )
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
        # Effective grants decide access. Membership in a named group
        # is not mandatory for a Neon read_only LOGIN with equivalent scope.
        self.assertTrue(all(cursor.current))
        self.assertIn("to_regnamespace('neon_auth')", cursor.last)
        self.assertIn("to_regnamespace('mar_p0')", cursor.last)


class ObservationCursor(DummyCursor):
    def __init__(self, stage="registered", prior=None):
        super().__init__(grant=True)
        self.stage = stage
        self.prior = prior

    def execute(self, sql, params=()):
        super().execute(sql, params)
        if "SELECT last_reported_stage" in sql:
            self.current = (self.stage,)
        elif "SELECT event_id FROM mar_corpora.audit_events" in sql:
            self.current = ((self.prior,) if self.prior is not None else None)
        elif sql.startswith("INSERT INTO mar_corpora.audit_events") and "RETURNING" in sql:
            self.current = (42,)


class TechnicalObservationTests(unittest.TestCase):
    def test_probe_requires_real_anchored_evidence_and_registered_stage(self):
        cursor = ObservationCursor()
        result = record_technical_observation(
            DummyConnection(cursor), corpus_code="eye", event_kind="probed",
            note="One bounded public page", evidence_sha256="a" * 64,
            evidence_ref="https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/12345",
        )
        self.assertEqual(result["event_id"], 42)
        self.assertFalse(result["publication_authorized"])
        sqls = [sql for sql, _ in cursor.calls]
        self.assertTrue(any("INSERT INTO mar_corpora.audit_events" in x for x in sqls))
        self.assertFalse(any("curator_reviewed" in x for x in sqls))
        self.assertFalse(any("approved_for_publication" in x for x in sqls))

    def test_probe_repeat_does_not_append(self):
        cursor = ObservationCursor(prior=14)
        result = record_technical_observation(
            DummyConnection(cursor), corpus_code="eye", event_kind="probed",
            note="Same bounded page", evidence_sha256="b" * 64,
            evidence_ref="https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/99",
        )
        self.assertEqual(result["event_id"], 14)
        self.assertTrue(result["already_recorded"])
        self.assertFalse(any(x.startswith("INSERT INTO mar_corpora.audit_events")
                             for x, _ in cursor.calls))

    def test_unregistered_or_hold_cannot_insert_probe(self):
        for code, stage in (("ape", "registered"), ("eye", "HOLD")):
            with self.subTest(code=code, stage=stage), self.assertRaises(ValueError):
                record_technical_observation(
                    DummyConnection(ObservationCursor(stage=stage)),
                    corpus_code=code, event_kind="probed", note="test",
                    evidence_sha256="c" * 64,
                    evidence_ref="https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/123",
                )

    def test_advanced_stages_and_invalid_evidence_are_rejected(self):
        for kind in ("curator_reviewed", "evidence_validated", "admission_ready"):
            with self.assertRaises(ValueError):
                record_technical_observation(
                    DummyConnection(ObservationCursor()),
                    corpus_code="eye", event_kind=kind, note="not allowed",
                )
        for ref in ("https://example.org/run/123",
                    "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/123?fake=1",
                    ""):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                record_technical_observation(
                    DummyConnection(ObservationCursor()),
                    corpus_code="eye", event_kind="probed", note="bounded probe",
                    evidence_sha256="d" * 64, evidence_ref=ref,
                )

    def test_note_and_hold_use_db_generated_actor_not_client_identity(self):
        cursor = ObservationCursor()
        record_technical_observation(
            DummyConnection(cursor), corpus_code="eye", event_kind="HOLD",
            note="Origin terms need review",
        )
        inserts = [(sql, params) for sql, params in cursor.calls
                   if sql.startswith("INSERT INTO mar_corpora.audit_events")]
        self.assertEqual(len(inserts), 1)
        self.assertIn("'sql-principal'", inserts[0][0])
        self.assertNotIn("admin@example.com", inserts[0][1])


if __name__ == "__main__":
    unittest.main()