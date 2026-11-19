#!/usr/bin/env python3
"""MAR F02: fail-closed live privilege preflight for a future backup reader.

Default: offline HOLD. --execute: only SELECT on Postgres catalog, using the
operator's existing libpq environment. Never prints URLs, keys, SQL rows or
database stderr. The application login is NOT provisioned by this script.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

EXPECTED_ROLE = "mar_p0_backup_reader"
EXPECTED_TABLES = ["checkpoint_pages", "checkpoints", "raw_artifacts"]

# psql returns only catalog-derived role/privilege booleans, not table contents.
# A role name is NOT sufficient to establish least privilege.
SQL = """
WITH tab AS (
 SELECT c.oid, c.relname
 FROM pg_class AS c JOIN pg_namespace AS n ON n.oid=c.relnamespace
 WHERE n.nspname='mar_p0' AND c.relkind IN ('r','p')
), rights AS (
 SELECT count(*)::integer AS table_count,
   coalesce(array_agg(relname::text ORDER BY relname),ARRAY[]::text[]) AS tables,
   coalesce(bool_and(has_table_privilege(current_user,oid,'SELECT')),false) AS all_select,
   coalesce(bool_or(
     has_table_privilege(current_user,oid,'INSERT') OR
     has_table_privilege(current_user,oid,'UPDATE') OR
     has_table_privilege(current_user,oid,'DELETE') OR
     has_table_privilege(current_user,oid,'TRUNCATE') OR
     has_table_privilege(current_user,oid,'REFERENCES') OR
     has_table_privilege(current_user,oid,'TRIGGER')
   ),true) AS any_write
 FROM tab
)
SELECT row_to_json(proof)::text FROM (
 SELECT current_user AS role,
   (current_user=session_user) AS direct_login,
   r.rolcanlogin AS can_login,
   r.rolinherit AS inherits_roles,
   (r.rolsuper OR r.rolcreatedb OR r.rolcreaterole OR
    r.rolreplication OR r.rolbypassrls) AS admin,
   has_database_privilege(current_user,current_database(),'CREATE') AS can_create_database_objects,
   has_schema_privilege(current_user,'mar_p0','USAGE') AS schema_usage,
   has_schema_privilege(current_user,'mar_p0','CREATE') AS can_create_in_schema,
   has_schema_privilege(current_user,'public','CREATE') AS can_create_in_public,
   coalesce(pg_has_role(current_user,to_regrole('neon_superuser'),'MEMBER'),false) AS neon_superuser_member,
   coalesce(pg_has_role(current_user,to_regrole('pg_write_all_data'),'MEMBER'),false) AS pg_write_all_data_member,
   coalesce(pg_has_role(current_user,
     (SELECT datdba FROM pg_database WHERE datname=current_database()),'MEMBER'),false) AS database_owner_member,
   EXISTS(SELECT 1 FROM pg_auth_members m WHERE m.member=r.oid) AS member_of_other_roles,
   EXISTS(
     SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
     WHERE n.nspname='mar_p0' AND p.prosecdef
       AND has_function_privilege(current_user,p.oid,'EXECUTE')
   ) AS executable_security_definer_in_mar_p0,
   rights.table_count,rights.tables,rights.all_select,rights.any_write
 FROM pg_roles AS r CROSS JOIN rights
 WHERE r.rolname=current_user
) AS proof;
"""


def assess(report: object) -> list[str]:
    if not isinstance(report, dict):
        return ["missing_or_invalid_catalog_proof"]
    errors: list[str] = []
    if report.get("role") != EXPECTED_ROLE:
        errors.append("role_not_dedicated_backup_reader")
    must_be_true = ("direct_login", "can_login", "schema_usage", "all_select")
    must_be_false = (
        "inherits_roles", "admin", "can_create_database_objects",
        "can_create_in_schema", "can_create_in_public",
        "neon_superuser_member", "pg_write_all_data_member",
        "database_owner_member", "member_of_other_roles",
        "executable_security_definer_in_mar_p0", "any_write",
    )
    for key in must_be_true:
        if report.get(key) is not True:
            errors.append(key + "_not_confirmed")
    for key in must_be_false:
        if report.get(key) is not False:
            errors.append(key + "_must_be_false")
    if type(report.get("table_count")) is not int or report["table_count"] != 3:
        errors.append("expected_exactly_three_mar_p0_tables")
    names = report.get("tables")
    if not isinstance(names, list) or names != EXPECTED_TABLES:
        errors.append("unexpected_mar_p0_table_inventory")
    return errors


def run_psql() -> dict:
    command = ["psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-c", SQL]
    # Command has no credentials. libpq reads operator-provided env/secrets.
    env = os.environ.copy()
    env["PGCONNECT_TIMEOUT"] = "12"
    env["PGAPPNAME"] = "mar-f02-reader-preflight"
    try:
        completed = subprocess.run(
            command, env=env, text=True, capture_output=True,
            check=False, timeout=25,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("database_check_unavailable") from exc
    if completed.returncode != 0:
        # NEVER echo stderr; connection/auth errors may include private fields.
        raise RuntimeError("database_check_rejected")
    try:
        data = json.loads(completed.stdout.strip())
    except (ValueError, TypeError) as exc:
        raise RuntimeError("database_check_invalid_response") from exc
    if not isinstance(data, dict):
        raise RuntimeError("database_check_invalid_response")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MAR F02 read-only credential preflight")
    parser.add_argument("--execute", action="store_true", help="Use configured libpq credentials, SELECT-only")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({
            "status": "HOLD", "mode": "offline",
            "database_requests": 0, "production_authorized": False,
        }, sort_keys=True))
        return 0
    try:
        errors = assess(run_psql())
    except RuntimeError:
        errors = ["live_check_failed"]
    print(json.dumps({
        "status": "HOLD" if errors else "PASS",
        "read_only_proven": not errors,
        "failed_checks": sorted(errors),  # known safe symbols, not database values
        "production_authorized": False,
    }, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
