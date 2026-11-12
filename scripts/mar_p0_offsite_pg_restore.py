"""Operator-run offsite recovery of MAR P0 checkpoints: no automated side effects.

Backup: pg_dump only mar_p0 from the existing Neon VALIDATION branch using
the limited SELECT role; encrypt the dump with AES-256-GCM before writing it
into a private offsite storage mount. Restore: decrypt into ephemeral private
space and pg_restore into a NEW local PostgreSQL database; compare all row
digests, schema definitions, and internal integrity constraints.

Connection URLs and AES keys are read from the executor's own environment,
NEVER from GitHub, command-line arguments, a provider tool or this program.
The command must run from an operator-authorized environment holding those
secrets. --execute is mandatory. No modification of Neon/main is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"MAR-P0-NEON-PGDUMP-AESGCM-V1\0"
SCHEMA = "mar.p0.offsite-pgdump.v1"
AAD_PREFIX = b"mar-p0-offsite-backup"
MAX_DUMP_BYTES = 64 * 1024 * 1024
MAX_HEADER_BYTES = 8192
MAX_FILE_BYTES = MAX_DUMP_BYTES + MAX_HEADER_BYTES + 512
EXPECTED = ("checkpoints", "checkpoint_pages", "raw_artifacts")
SOURCE_PROJECT = "holy-bread-70461948"
SOURCE_BRANCH = "br-lingering-smoke-b8hjdnzb"


class RecoveryRejected(ValueError):
    """Stable error class only: never include secret values or SQL payloads."""


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(obj):
    return json.dumps(obj, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _key(env):
    candidate = env.get("MAR_P0_RESTORE_AES_KEY_HEX")
    if not isinstance(candidate, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", candidate):
        raise RecoveryRejected("aes_key_not_provisioned")
    return bytes.fromhex(candidate)


def _postgres_env(variable, *, origin, env):
    """Pass password by libpq environment, NOT shell args / process argv."""
    connection = env.get(variable, "")
    try:
        parsed = urlsplit(connection)
        username = unquote(parsed.username or "")
        password = unquote(parsed.password or "")
        hostname = (parsed.hostname or "").lower()
        port = parsed.port or 5432
        database = unquote(parsed.path.lstrip("/"))
    except (ValueError, AttributeError) as error:
        raise RecoveryRejected("invalid_connection_url") from error
    if (parsed.scheme not in ("postgresql", "postgres") or not username or
            not password or port != 5432 or parsed.fragment or
            not re.fullmatch(r"[A-Za-z0-9_]+", database)):
        raise RecoveryRejected("invalid_connection_url")
    if origin:
        if (username != "mar_p0_limited" or not hostname.endswith(".neon.tech")
                or database != "neondb"):
            raise RecoveryRejected("source_must_be_limited_neon_validation_role")
    else:
        if hostname not in ("localhost", "127.0.0.1", "::1"):
            raise RecoveryRejected("restore_target_must_be_local_isolated_postgres")
        if not database.startswith("mar_p0_restore_"):
            raise RecoveryRejected("restore_database_name_not_isolated")
    safe = {k: v for k, v in env.items() if not k.startswith(("PG", "MAR_P0_"))}
    safe.update({
        "PGHOST": hostname, "PGPORT": str(port), "PGUSER": username,
        "PGPASSWORD": password, "PGDATABASE": database,
        "PGCONNECT_TIMEOUT": "12",
        "PGAPPNAME": "mar-p0-backup-readonly" if origin else "mar-p0-restore-lab",
    })
    if origin:
        # libpq 18 must validate certificate against the system trust store.
        safe.update({"PGSSLMODE": "verify-full", "PGSSLROOTCERT": "system",
                     "PGCHANNELBINDING": "require"})
    else:
        safe["PGSSLMODE"] = "disable"
    return safe


def _run(command, *, env, output=False):
    result = subprocess.run(
        command, env=env, check=True, capture_output=True, text=True,
        timeout=120,  # bounded; no long-running crawler or background job
    )
    return result.stdout.strip() if output else None


def _db_summary(env):
    tables = [
        ("checkpoints", "run_key"),
        ("checkpoint_pages", "run_key,sequence"),
        ("raw_artifacts", "sha256"),
    ]
    sections = []
    for name, order in tables:
        sections.append(f"""
         '{name}', (SELECT json_build_object(
            'count', count(*)::int,
            'sha256', encode(sha256(convert_to(
             coalesce(string_agg(to_jsonb(t)::text,E'\\n' ORDER BY {order}),''),
             'UTF8')), 'hex')) FROM mar_p0.{name} t)
        """)
    query = "SELECT json_build_object(" + ",".join(sections) + ")::text"
    raw = _run(["psql", "-X", "-At", "-v", "ON_ERROR_STOP=1", "-c", query],
               env=env, output=True)
    try:
        values = json.loads(raw)
    except (ValueError, TypeError) as error:
        raise RecoveryRejected("fingerprint_query_invalid") from error
    if set(values) != set(EXPECTED):
        raise RecoveryRejected("unexpected_tables")
    for name in EXPECTED:
        record = values[name]
        if (type(record.get("count")) is not int or record["count"] < 1
                or not re.fullmatch("[0-9a-f]{64}", str(record.get("sha256")))):
            raise RecoveryRejected("missing_or_invalid_fingerprint")
    return values


SCHEMA_SQL = r"""WITH cols AS (
 SELECT table_name,ordinal_position::text||':'||column_name||':'||
   data_type||':'||is_nullable||':'||coalesce(column_default,'') AS detail
 FROM information_schema.columns WHERE table_schema='mar_p0'
), defs AS (
 SELECT 'column' AS kind,table_name AS object_name,detail FROM cols
 UNION ALL
 SELECT 'constraint',c.relname,
   con.conname||':'||pg_get_constraintdef(con.oid)
 FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid
 JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='mar_p0'
 UNION ALL
 SELECT 'index',t.relname,ix.relname||':'||pg_get_indexdef(i.indexrelid)
 FROM pg_index i JOIN pg_class t ON t.oid=i.indrelid
 JOIN pg_class ix ON ix.oid=i.indexrelid
 JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname='mar_p0'
)
SELECT json_build_object('count',count(*)::int,
 'sha256',encode(sha256(convert_to(
 string_agg(kind||'|'||object_name||'|'||detail,E'\n'
 ORDER BY kind,object_name,detail),'UTF8')),'hex'))::text FROM defs"""

INTEGRITY_SQL = r"""SELECT json_build_object(
 'invalid_manifest_hashes',(SELECT count(*)::int FROM mar_p0.checkpoints c
 WHERE c.manifest_sha256<>encode(sha256(c.manifest),'hex')),
 'invalid_artifact_hashes',(SELECT count(*)::int FROM mar_p0.raw_artifacts a
 WHERE a.sha256<>encode(sha256(a.payload),'hex')),
 'orphan_pages',(SELECT count(*)::int FROM mar_p0.checkpoint_pages p
 LEFT JOIN mar_p0.checkpoints c ON c.run_key=p.run_key WHERE c.run_key IS NULL),
 'orphan_artifacts',(SELECT count(*)::int FROM mar_p0.checkpoint_pages p
 LEFT JOIN mar_p0.raw_artifacts a ON a.sha256=p.artifact_sha256 WHERE a.sha256 IS NULL),
 'forbidden_flags',(SELECT count(*)::int FROM mar_p0.checkpoints
 WHERE media_downloaded OR promotion_authorized))::text"""


def _schema_summary(env):
    return json.loads(_run(["psql", "-X", "-At", "-v", "ON_ERROR_STOP=1",
                            "-c", SCHEMA_SQL], env=env, output=True))


def _integrity_summary(env):
    values = json.loads(_run(["psql", "-X", "-At", "-v", "ON_ERROR_STOP=1",
                              "-c", INTEGRITY_SQL], env=env, output=True))
    if any(type(v) is not int or v != 0 for v in values.values()):
        raise RecoveryRejected("mar_p0_internal_integrity_failed")
    return values


def _seal(dump, source, schema, key):
    if not 1 < len(dump) <= MAX_DUMP_BYTES or not dump.startswith(b"PGDMP"):
        raise RecoveryRejected("not_a_bounded_pg_custom_dump")
    header = {
        "schema": SCHEMA, "source_project": SOURCE_PROJECT,
        "source_branch": SOURCE_BRANCH, "database_schema": "mar_p0",
        "format": "pg_dump-custom-18", "dump_sha256": _sha(dump),
        "rows": source, "schema_fingerprint": schema,
        "production_gate": "HOLD",
    }
    raw_header = _canonical(header)
    if len(raw_header) > MAX_HEADER_BYTES:
        raise RecoveryRejected("header_too_large")
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, dump, AAD_PREFIX + raw_header)
    return MAGIC + len(raw_header).to_bytes(4, "big") + raw_header + nonce + ciphertext


def _unseal(envelope, key):
    if (len(envelope) > MAX_FILE_BYTES or not envelope.startswith(MAGIC)
            or len(envelope) < len(MAGIC) + 4 + 12 + 16):
        raise RecoveryRejected("invalid_backup_envelope")
    pos = len(MAGIC)
    size = int.from_bytes(envelope[pos:pos + 4], "big")
    pos += 4
    if size < 1 or size > MAX_HEADER_BYTES or len(envelope) < pos + size + 28:
        raise RecoveryRejected("invalid_backup_header_size")
    raw_header = envelope[pos:pos + size]
    pos += size
    try:
        header = json.loads(raw_header)
    except (ValueError, TypeError) as error:
        raise RecoveryRejected("invalid_backup_header") from error
    if (not isinstance(header, dict) or _canonical(header) != raw_header
            or header.get("schema") != SCHEMA
            or header.get("source_project") != SOURCE_PROJECT
            or header.get("source_branch") != SOURCE_BRANCH
            or header.get("database_schema") != "mar_p0"
            or header.get("production_gate") != "HOLD"):
        raise RecoveryRejected("backup_header_not_trusted")
    try:
        data = AESGCM(key).decrypt(
            envelope[pos:pos + 12], envelope[pos + 12:],
            AAD_PREFIX + raw_header,
        )
    except (InvalidTag, ValueError) as error:
        raise RecoveryRejected("encrypted_backup_authentication_failed") from error
    if data[:5] != b"PGDMP" or _sha(data) != header.get("dump_sha256"):
        raise RecoveryRejected("dump_checksum_mismatch")
    if not isinstance(header.get("rows"), dict) or not isinstance(header.get("schema_fingerprint"), dict):
        raise RecoveryRejected("backup_fingerprints_not_present")
    return data, header


def _write_exclusive(path, content):
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
        raise RecoveryRejected("backup_output_must_be_new_in_existing_private_directory")
    if os.name == "posix" and (path.parent.stat().st_mode & 0o077):
        raise RecoveryRejected("backup_directory_not_private_0700")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if os.name == "posix":
            parent_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def export_backup(output, env):
    source = _postgres_env("MAR_P0_READONLY_DATABASE_URL", origin=True, env=env)
    key = _key(env)
    before, before_schema = _db_summary(source), _schema_summary(source)
    _integrity_summary(source)
    with tempfile.TemporaryDirectory(prefix="mar-p0-export-") as folder:
        dump_path = Path(folder) / "p0.pgcustom"
        _run(["pg_dump", "--format=custom", "--schema=mar_p0",
              "--no-owner", "--no-acl", "--lock-wait-timeout=5s",
              "--file=" + str(dump_path)], env=source)
        data = dump_path.read_bytes()
        if _db_summary(source) != before or _schema_summary(source) != before_schema:
            raise RecoveryRejected("source_changed_during_export")
        envelope = _seal(data, before, before_schema, key)
        _write_exclusive(output, envelope)
    return {
        "status": "encrypted_backup_exported",
        "encrypted_sha256": _sha(envelope),
        "encrypted_size_bytes": len(envelope),
        "table_counts": {t: before[t]["count"] for t in EXPECTED},
        "source_modified": False, "recovery_verified": False,
        "production_gate": "HOLD",
    }


def restore_backup(encrypted, env, expected_sha256):
    target = _postgres_env("MAR_P0_ISOLATED_RESTORE_DATABASE_URL",
                           origin=False, env=env)
    key = _key(env)
    if not re.fullmatch("[a-f0-9]{64}", expected_sha256 or ""):
        raise RecoveryRejected("external_backup_sha256_not_pinned")
    if encrypted.is_symlink() or not encrypted.is_file():
        raise RecoveryRejected("encrypted_backup_unavailable")
    envelope = encrypted.read_bytes()
    if _sha(envelope) != expected_sha256:
        raise RecoveryRejected("external_backup_sha256_mismatch")
    data, header = _unseal(envelope, key)
    # STRICT: never restore into a database containing mar_p0.
    preflight = _run(["psql", "-X", "-At", "-v", "ON_ERROR_STOP=1",
                      "-c", "SELECT to_regnamespace('mar_p0') IS NULL"],
                     env=target, output=True)
    if preflight != "t":
        raise RecoveryRejected("target_schema_already_exists")
    with tempfile.TemporaryDirectory(prefix="mar-p0-restore-") as folder:
        dump_path = Path(folder) / "p0.pgcustom"
        dump_path.write_bytes(data)
        _run(["pg_restore", "--no-owner", "--no-acl",
              "--single-transaction", "--exit-on-error",
              "--dbname=" + target["PGDATABASE"], str(dump_path)],
             env=target)
    if (_db_summary(target) != header["rows"]
            or _schema_summary(target) != header["schema_fingerprint"]):
        raise RecoveryRejected("restored_rows_or_schema_differ")
    _integrity_summary(target)
    return {
        "status": "offsite_restored_and_verified",
        "encrypted_sha256": expected_sha256,
        "table_counts": {t: header["rows"][t]["count"] for t in EXPECTED},
        "same_encrypted_blob": True,
        "rows_and_schema_sha256_equal": True,
        "original_neon_modified": False,
        "production_gate": "HOLD",
    }


def main(argv=None, environ=None):
    parser = argparse.ArgumentParser(description="MAR P0 secure encrypted export / independent restore")
    parser.add_argument("operation", choices=("backup", "restore"))
    parser.add_argument("--encrypted-file", type=Path, required=True)
    parser.add_argument("--expected-sha256", default=None, help="External encrypted blob pin for restore")
    parser.add_argument("--execute", action="store_true", help="Explicitly authorize this action")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({"status": "dry_run", "network_requests": 0,
                          "filesystem_writes": 0, "production_gate": "HOLD"}))
        return 0
    env = os.environ if environ is None else environ
    try:
        if args.operation == "backup":
            result = export_backup(args.encrypted_file, env)
        else:
            result = restore_backup(args.encrypted_file, env, args.expected_sha256)
    except (RecoveryRejected, OSError, subprocess.SubprocessError, KeyError,
            ValueError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "HOLD", "rejected_class": type(error).__name__,
                          "production_gate": "HOLD"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
