-- MAR Gate P0: test-branch-only SQL-native application login.
-- Run AFTER 001_mar_p0_checkpoint.sql, on an empty disposable branch only.
-- This deliberately creates a PASSWORDLESS (unusable) login.
-- Activate it privately in Neon Console, or via psql's interactive \password.
-- Do NOT use Neon Console/API "Create role": it inherits neon_superuser.
-- Apply exactly once; never reset passwords in application migrations.

CREATE ROLE mar_p0_limited
    LOGIN PASSWORD NULL NOINHERIT NOCREATEDB NOCREATEROLE NOBYPASSRLS;

GRANT CONNECT ON DATABASE neondb TO mar_p0_limited;
GRANT USAGE ON SCHEMA mar_p0 TO mar_p0_limited;
GRANT SELECT, INSERT ON mar_p0.raw_artifacts TO mar_p0_limited;
GRANT SELECT, INSERT, UPDATE ON mar_p0.checkpoints TO mar_p0_limited;
GRANT SELECT, INSERT ON mar_p0.checkpoint_pages TO mar_p0_limited;

-- Read-only verification; password must never be printed.
SELECT rolname, rolcanlogin, rolcreatedb, rolcreaterole, rolbypassrls
FROM pg_roles WHERE rolname = 'mar_p0_limited';

-- Application roles must never inherit the elevated neon_superuser role.
SELECT count(*) AS inherited_role_count
FROM pg_auth_members m
JOIN pg_roles r ON r.oid = m.member
WHERE r.rolname = 'mar_p0_limited';
