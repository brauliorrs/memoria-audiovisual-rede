"""KAVI P0: encrypted, offline, single-epoch staging checkpoint backup.

This is NOT an object-store backend or proof of long-term durability.
Use only on explicitly provisioned private storage (POSIX mode 0700),
with an independently supplied secret-manager key. No HTTP/media,
no new cursor, no publishing and no retry/restart of the source API.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import stat
import struct
import tempfile
import zipfile
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .digital_infrastructure.locking import FileWriteLock
from .kavi_finna_adapter import FinnaScope
from .metadata_staging import StageRejected, _digest, _restore
from scripts.audit_kavi_finna_staging import audit_finna_staging

MAGIC = b"MAR-KAVI-P0-v1\0"
SCHEMA = "kavi-p0-aes256gcm-epoch-1.0"
SHA = re.compile(r"^[a-f0-9]{64}$")
EPOCH = re.compile(r"^epoch-[a-zA-Z0-9_-]{1,60}$")
RAW_PATH = re.compile(r"^raw/([a-f0-9]{2})/([a-f0-9]{64})\.json$")
MAX_PAGES = 25
MAX_ARCHIVE_PLAINTEXT = 64 * 1024 * 1024
MAX_BACKUP_BYTES = 66 * 1024 * 1024
MAX_HEADER_BYTES = 4096
KEY_ENV = "MAR_KAVI_BACKUP_KEY_B64"


class BackupRejected(ValueError):
    """Stable error code only: never include encrypted payload or raw tokens."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _key(key: bytes) -> bytes:
    if not isinstance(key, bytes) or len(key) != 32:
        raise BackupRejected("p0_key_must_be_32_bytes")
    return key


def load_backup_key_from_environment() -> bytes:
    """Read key from operator-provisioned secret; never print it."""
    encoded = os.environ.get(KEY_ENV)
    if not isinstance(encoded, str) or not encoded:
        raise BackupRejected("p0_secret_key_unavailable")
    try:
        return _key(base64.b64decode(encoded, validate=True))
    except (ValueError, TypeError) as exc:
        raise BackupRejected("p0_secret_key_invalid") from exc


def _safe_epoch(epoch_id: str) -> str:
    if not isinstance(epoch_id, str) or not EPOCH.fullmatch(epoch_id):
        raise BackupRejected("p0_epoch_identity_invalid")
    return epoch_id


def _anchors(evidence_sha256: str, expected_total: int) -> None:
    if not isinstance(evidence_sha256, str) or not SHA.fullmatch(evidence_sha256):
        raise BackupRejected("p0_scope_fingerprint_invalid")
    if (not isinstance(expected_total, int) or isinstance(expected_total, bool)
            or expected_total < 1):
        raise BackupRejected("p0_expected_total_invalid")


def _private(directory: Path) -> None:
    if not directory.is_dir() or directory.is_symlink():
        raise BackupRejected("p0_private_directory_missing_or_symlink")
    if os.name != "posix":
        # Windows access controls need a dedicated ACL provider integration.
        raise BackupRejected("p0_posix_acl_backend_required")
    info = directory.stat()
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise BackupRejected("p0_private_directory_acl_not_verified")


def _private_file(file: Path) -> None:
    if not file.is_file() or file.is_symlink():
        raise BackupRejected("p0_private_file_missing_or_symlink")
    info = file.stat()
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
        raise BackupRejected("p0_private_file_acl_not_verified")


def _source_files(root: Path, *, evidence_sha256: str, expected_total: int):
    checkpoint = root / "checkpoint.json"
    if checkpoint.is_symlink():
        raise BackupRejected("p0_checkpoint_symlink_refused")
    try:
        raw_checkpoint = checkpoint.read_bytes()
        state = json.loads(raw_checkpoint)
    except (OSError, ValueError, TypeError) as exc:
        raise BackupRejected("p0_checkpoint_invalid") from exc
    if not isinstance(state, dict) or not 1 <= len(state.get("pages", [])) <= MAX_PAGES:
        raise BackupRejected("p0_page_budget_invalid")
    scope = FinnaScope("0/KAVI/", "0/Video/", evidence_sha256).to_dict()
    try:
        _restore(root, state, _digest(scope), expected_total)
    except (StageRejected, OSError, ValueError) as exc:
        raise BackupRejected("p0_stage_integrity_failed") from exc
    files = {"checkpoint.json": raw_checkpoint}
    for page in state["pages"]:
        digest = page["artifact_sha256"]
        if not isinstance(digest, str) or not SHA.fullmatch(digest):
            raise BackupRejected("p0_raw_artifact_digest_invalid")
        name = f"raw/{digest[:2]}/{digest}.json"
        source = root / name
        if source.is_symlink():
            raise BackupRejected("p0_raw_artifact_symlink_refused")
        try:
            content = source.read_bytes()
        except OSError as exc:
            raise BackupRejected("p0_raw_artifact_missing") from exc
        if _sha(content) != digest:
            raise BackupRejected("p0_raw_artifact_tampered")
        if name in files:
            raise BackupRejected("p0_raw_artifact_duplicate")
        files[name] = content
    if sum(map(len, files.values())) > MAX_ARCHIVE_PLAINTEXT:
        raise BackupRejected("p0_archive_size_limit")
    return state, files


def _zip_data(files: dict[str, bytes]) -> bytes:
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, mode="w", compression=zipfile.ZIP_STORED) as output:
        for name in sorted(files):
            output.writestr(name, files[name])
    archive = memory.getvalue()
    if len(archive) > MAX_ARCHIVE_PLAINTEXT:
        raise BackupRejected("p0_archive_size_limit")
    return archive


def _header_bytes(header: dict) -> bytes:
    blob = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(blob) > MAX_HEADER_BYTES:
        raise BackupRejected("p0_header_too_large")
    return blob


def _fsync_directory(folder: Path) -> None:
    fd = os.open(folder, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def backup_verified_epoch(
    source_dir: str | Path, backup_file: str | Path, *,
    evidence_sha256: str, expected_total: int,
    epoch_id: str, key: bytes,
) -> dict:
    """Seal one audited stage epoch as an authenticated backup on private disk."""
    _anchors(evidence_sha256, expected_total)
    _safe_epoch(epoch_id)
    _key(key)
    source, target = Path(source_dir), Path(backup_file)
    _private(source)
    _private(target.parent)
    if target.exists() or target.is_symlink() or source.resolve() in target.parent.resolve().parents:
        raise BackupRejected("p0_backup_target_unsafe_or_exists")
    before = _sha((source / "checkpoint.json").read_bytes())
    # Audit source-normalized IDs and rights separately from the payload's
    # self-asserted digests; never copy an unverified stage.
    try:
        audit = audit_finna_staging(
            source, evidence_sha256=evidence_sha256,
            expected_total=expected_total,
        )
    except (ValueError, StageRejected, OSError) as exc:
        raise BackupRejected("p0_source_offline_audit_failed") from exc
    with FileWriteLock(source / "run", timeout=10):
        if _sha((source / "checkpoint.json").read_bytes()) != before:
            raise BackupRejected("p0_checkpoint_changed_during_audit")
        state, files = _source_files(
            source, evidence_sha256=evidence_sha256, expected_total=expected_total,
        )
        if (audit["record_count"] != state["record_count"]
                or audit["page_count"] != len(state["pages"])
                or audit["status"] != state["status"]):
            raise BackupRejected("p0_source_audit_state_mismatch")
        archive = _zip_data(files)
    header = {
        "schema": SCHEMA, "epoch_id": epoch_id,
        "source_scope_sha256": state["scope_sha256"],
        "expected_total": expected_total,
        "checkpoint_sha256": _sha(files["checkpoint.json"]),
        "archive_sha256": _sha(archive),
        "record_count": state["record_count"],
        "page_count": len(state["pages"]),
    }
    auth = _header_bytes(header)
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, archive, auth)
    sealed = MAGIC + struct.pack(">I", len(auth)) + auth + nonce + ciphertext
    if len(sealed) > MAX_BACKUP_BYTES:
        raise BackupRejected("p0_encrypted_size_limit")
    temp_path = None
    try:
        fd, name = tempfile.mkstemp(prefix=".kavi-backup-", dir=target.parent)
        temp_path = Path(name)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(sealed)
            handle.flush()
            os.fsync(handle.fileno())
        # Atomic no-clobber installation using a hardlink within private dir.
        os.link(temp_path, target, follow_symlinks=False)
        _fsync_directory(target.parent)
    except (OSError, FileExistsError) as exc:
        raise BackupRejected("p0_backup_atomic_commit_failed") from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return {
        "status": "encrypted",
        "epoch_id": epoch_id,
        "backup_sha256": _sha(sealed),
        "checkpoint_sha256": header["checkpoint_sha256"],
        "record_count": state["record_count"],
        "page_count": len(state["pages"]),
        "media_downloaded": False,
        "promotion_authorized": False,
        "durability_verified": False,
    }


def _open_sealed(blob: bytes, *, evidence_sha256: str, expected_total: int,
                 epoch_id: str, key: bytes):
    if len(blob) > MAX_BACKUP_BYTES or not blob.startswith(MAGIC):
        raise BackupRejected("p0_backup_format_invalid")
    at = len(MAGIC)
    if len(blob) < at + 4:
        raise BackupRejected("p0_backup_truncated")
    length = struct.unpack(">I", blob[at:at + 4])[0]
    if not 1 <= length <= MAX_HEADER_BYTES:
        raise BackupRejected("p0_backup_header_length_invalid")
    at += 4
    if len(blob) < at + length + 12 + 16:
        raise BackupRejected("p0_backup_truncated")
    auth = blob[at:at + length]
    try:
        header = json.loads(auth)
    except (ValueError, TypeError) as exc:
        raise BackupRejected("p0_backup_header_invalid") from exc
    if not isinstance(header, dict) or set(header) != {
        "schema", "epoch_id", "source_scope_sha256", "expected_total",
        "checkpoint_sha256", "archive_sha256", "record_count", "page_count",
    }:
        raise BackupRejected("p0_backup_header_schema_invalid")
    scope = FinnaScope("0/KAVI/", "0/Video/", evidence_sha256).to_dict()
    if (header["schema"] != SCHEMA
            or header["epoch_id"] != epoch_id
            or header["source_scope_sha256"] != _digest(scope)
            or header["expected_total"] != expected_total):
        raise BackupRejected("p0_backup_anchor_mismatch")
    for name in ("checkpoint_sha256", "archive_sha256"):
        val = header[name]
        if not isinstance(val, str) or not SHA.fullmatch(val):
            raise BackupRejected("p0_backup_hash_invalid")
    at += length
    nonce, ciphertext = blob[at:at + 12], blob[at + 12:]
    try:
        archive = AESGCM(key).decrypt(nonce, ciphertext, auth)
    except (InvalidTag, ValueError) as exc:
        raise BackupRejected("p0_backup_authentication_failed") from exc
    if _sha(archive) != header["archive_sha256"]:
        raise BackupRejected("p0_backup_archive_integrity_failed")
    return header, archive


def _unpack(archive: bytes, target: Path, expected_checkpoint_sha256: str) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as data:
            infos = data.infolist()
            names = [item.filename for item in infos]
            if (not 2 <= len(infos) <= MAX_PAGES + 1
                    or len(set(names)) != len(names)
                    or "checkpoint.json" not in names
                    or any(name != "checkpoint.json" and not RAW_PATH.fullmatch(name)
                           for name in names)
                    or sum(i.file_size for i in infos) > MAX_ARCHIVE_PLAINTEXT):
                raise BackupRejected("p0_backup_members_invalid")
            for entry in infos:
                filemode = (entry.external_attr >> 16) & 0o170000
                if filemode not in (0, stat.S_IFREG):
                    raise BackupRejected("p0_backup_special_file_refused")
            content = {name: data.read(name) for name in names}
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise BackupRejected("p0_backup_archive_invalid") from exc
    if _sha(content["checkpoint.json"]) != expected_checkpoint_sha256:
        raise BackupRejected("p0_checkpoint_digest_mismatch")
    try:
        checkpoint = json.loads(content["checkpoint.json"])
        raw_names = {
            f"raw/{p['artifact_sha256'][:2]}/{p['artifact_sha256']}.json"
            for p in checkpoint["pages"]
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise BackupRejected("p0_checkpoint_payload_invalid") from exc
    if set(content) != raw_names | {"checkpoint.json"}:
        raise BackupRejected("p0_archive_checkpoint_members_mismatch")
    for name, data in content.items():
        if name != "checkpoint.json":
            digest = RAW_PATH.fullmatch(name).group(2)
            if _sha(data) != digest:
                raise BackupRejected("p0_archive_raw_digest_mismatch")
    for name, data in content.items():
        path = target / name
        # Secure EVERY nested component, not only the leaf parent:
        # Path.mkdir(parents=True) otherwise creates raw/ with umask 0755.
        parent = target
        for part in Path(name).parts[:-1]:
            parent = parent / part
            parent.mkdir(mode=0o700, exist_ok=True)
            parent.chmod(0o700)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())


def restore_verified_epoch(
    backup_file: str | Path, new_epoch_dir: str | Path, *,
    evidence_sha256: str, expected_total: int,
    epoch_id: str, key: bytes,
) -> dict:
    """Decrypt into a NEW private directory and audit BEFORE making it visible."""
    _anchors(evidence_sha256, expected_total)
    _safe_epoch(epoch_id)
    _key(key)
    archive_path, final = Path(backup_file), Path(new_epoch_dir)
    _private(archive_path.parent)
    _private_file(archive_path)
    _private(final.parent)
    if final.exists() or final.is_symlink():
        raise BackupRejected("p0_restore_target_already_exists")
    if archive_path.parent.resolve() == final.parent.resolve():
        raise BackupRejected("p0_restore_storage_not_isolated")
    try:
        sealed = archive_path.read_bytes()
    except OSError as exc:
        raise BackupRejected("p0_backup_unreadable") from exc
    header, archive = _open_sealed(
        sealed, evidence_sha256=evidence_sha256,
        expected_total=expected_total, epoch_id=epoch_id, key=key,
    )
    stage = Path(tempfile.mkdtemp(prefix=".kavi-restore-", dir=final.parent))
    stage.chmod(0o700)
    try:
        _unpack(archive, stage, header["checkpoint_sha256"])
        try:
            audit = audit_finna_staging(
                stage, evidence_sha256=evidence_sha256,
                expected_total=expected_total,
            )
        except (StageRejected, ValueError, OSError) as exc:
            raise BackupRejected("p0_restored_stage_audit_failed") from exc
        if (audit["record_count"] != header["record_count"]
                or audit["page_count"] != header["page_count"]):
            raise BackupRejected("p0_restored_stage_counts_mismatch")
        if final.exists() or final.is_symlink():
            raise BackupRejected("p0_restore_target_already_exists")
        os.rename(stage, final)
        _fsync_directory(final.parent)
    except (BackupRejected, OSError) as exc:
        if isinstance(exc, BackupRejected):
            raise
        raise BackupRejected("p0_restore_atomic_commit_failed") from exc
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {
        "status": "restored_and_audited",
        "epoch_id": epoch_id,
        "backup_sha256": _sha(sealed),
        "checkpoint_sha256": header["checkpoint_sha256"],
        "record_count": audit["record_count"],
        "page_count": audit["page_count"],
        "offline_integrity_verified": True,
        "media_downloaded": False,
        "promotion_authorized": False,
        "durability_verified": False,
    }
