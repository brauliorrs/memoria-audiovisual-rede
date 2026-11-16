-- MAR additive V1 hardening: attestations require a separate role.
-- User account credentials must be provisioned outside this migration.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mar_corpora_attestor') THEN
        CREATE ROLE mar_corpora_attestor NOLOGIN;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION mar_corpora.guard_audit_insert()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.event_kind IN ('evidence_validated','curator_reviewed','admission_ready')
       AND NOT pg_has_role(current_user, 'mar_corpora_attestor', 'member') THEN
        RAISE EXCEPTION 'independent attestor role required for advanced corpus state';
    END IF;
    -- The DB principal and server timestamp, never self-asserted actor/date,
    -- are the authoritative observer of this *declarative* event.
    NEW.actor_ref := current_user;
    NEW.recorded_at := clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE TRIGGER mar_corpora_audit_insert_guard
BEFORE INSERT ON mar_corpora.audit_events
FOR EACH ROW EXECUTE FUNCTION mar_corpora.guard_audit_insert();

-- mar_corpora_attestor intentionally has NO LOGIN, NO TABLE privileges and
-- NO membership assignments here. A separately authenticated reviewer
-- requires approved per-person credentials and scoped grants.
