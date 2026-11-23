"""Portable encrypted P0 staging snapshot: offline, metadata-only, never uploaded.

This module does NOT back up the live PostgreSQL service by itself.
The caller must first restore a verified checkpoint to a staging directory and
then transfer the encrypted output to independent protected storage.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .digital_infrastructure.locking import FileWriteLock
from .digital_infrastructure.raw_artifacts import canonical_json_bytes
from .metadata_staging import StageRejected, _digest, _restore


class BackupRejected(StageRejected):
    """Reject unsafe or unverifiable archives without printing private content."""


_VERSION = "mar-p0-staging-aes256gcm-v1"
_AAD = b"MAR/P0/encrypted-staging/v1"
_MAX_FILES = 1001
_MAX_BYTES = 64 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 96 * 1024 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}")


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: object) -> bytes:
    if not isinstance(value, str):
        raise BackupRejected("backup_invalid_encoding")
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise BackupRejected("backup_invalid_encoding") from exc


def _key(secret: bytes, salt: bytes) -> bytes:
    if not isinstance(secret, bytes) or len(secret) < 16:
        raise BackupRejected("backup_secret_invalid")
    if len(salt) != 16:
        raise BackupRejected("backup_salt_invalid")
    return Scrypt(salt=salt, length=32, n=2**15, r=8, p=1).derive(secret)


def _validate_dir(root: Path) -> dict[str, bytes]:
    if root.is_symlink() or not root.is_dir():
        raise BackupRejected("backup_source_invalid")
    manifest_path = root / "checkpoint.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise BackupRejected("backup_manifest_missing")
    raw_manifest = manifest_path.read_bytes()
    try:
        manifest = json.loads(raw_manifest)
    except (ValueError, UnicodeDecodeError) as exc:
        raise BackupRejected("backup_manifest_invalid") from exc
    if not isinstance(manifest, dict) or (
        canonical_json_bytes(manifest) + b"\n" != raw_manifest
    ):
        raise BackupRejected("backup_manifest_not_canonical")
    if manifest.get("media_downloaded") is not False or (
        manifest.get("promotion_authorized") is not False
    ):
        raise BackupRejected("backup_outside_p0_scope")
    scope = manifest.get("scope")
    total = manifest.get("expected_total")
    pages = manifest.get("pages")
    if (not isinstance(scope, dict) or not isinstance(total, int)
        or isinstance(total, bool) or total < 0 or not isinstance(pages, list)
        or len(pages) > _MAX_FILES - 1):
        raise BackupRejected("backup_manifest_shape_invalid")

    paths = {"checkpoint.json"}
    for page in pages:
        sha = page.get("artifact_sha256") if isinstance(page, dict) else None
        if not isinstance(sha, str) or not _DIGEST.fullmatch(sha):
            raise BackupRejected("backup_artifact_path_invalid")
        path = f"raw/{sha[:2]}/{sha}.json"
        if path in paths:
            raise BackupRejected("backup_duplicate_artifact")
        paths.add(path)

    # Never traverse symbolic links or package unrelated local content.
    for path in root.rglob("*"):
        if path.is_symlink():
            raise BackupRejected("backup_symlink_refused")
        if path.is_file() and path.relative_to(root).as_posix() not in (
            paths | {"run.lock"}
        ):
            raise BackupRejected("backup_unexpected_file")
        if not path.is_dir() and not path.is_file():
            raise BackupRejected("backup_special_file_refused")

    result: dict[str, bytes] = {}
    consumed = 0
    for name in sorted(paths):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise BackupRejected("backup_artifact_missing")
        size = path.stat().st_size
        if size > _MAX_BYTES - consumed:
            raise BackupRejected("backup_size_limit")
        data = path.read_bytes()
        consumed += len(data)
        if consumed > _MAX_BYTES:
            raise BackupRejected("backup_size_limit")
        if name != "checkpoint.json":
            sha = path.stem
            if hashlib.sha256(data).hexdigest() != sha:
                raise BackupRejected("backup_artifact_digest_invalid")
        result[name] = data

    # Reuse the original MAR recovery validator, including cursor/ID checks.
    try:
        _restore(root, manifest, _digest(scope), total)
    except StageRejected as exc:
        raise BackupRejected("backup_original_checkpoint_invalid") from exc
    return result


def encrypt_staging(root: str | Path, archive: str | Path, secret: bytes) -> None:
    """Encrypt a verified staging tree to a new file, never overwriting."""
    source = Path(root)
    destination = Path(archive)
    if destination.exists() or destination.is_symlink():
        raise BackupRejected("backup_destination_exists")
    # Use the same staging lock as the collector; exclude its own lock file.
    with FileWriteLock(source / "run", timeout=10):
        files = _validate_dir(source)
        payload = canonical_json_bytes({
            "version": _VERSION,
            "files": [
                {"path": name, "sha256": hashlib.sha256(data).hexdigest(),
                 "data": _b64(data)}
                for name, data in files.items()
            ],
        })
    salt, nonce = os.urandom(16), os.urandom(12)
    encrypted = AESGCM(_key(secret, salt)).encrypt(nonce, payload, _AAD)
    envelope = canonical_json_bytes({
        "version": _VERSION, "salt": _b64(salt), "nonce": _b64(nonce),
        "ciphertext": _b64(encrypted),
    }) + b"\n"
    if len(envelope) > _MAX_ARCHIVE_BYTES:
        raise BackupRejected("backup_size_limit")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with FileWriteLock(destination, timeout=10):
        if destination.exists() or destination.is_symlink():
            raise BackupRejected("backup_destination_exists")
        temporary = destination.with_name(
            destination.name + "." + os.urandom(8).hex() + ".tmp"
        )
        try:
            fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(envelope)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, destination)  # atomic create-only: no overwrite
        finally:
            temporary.unlink(missing_ok=True)


def decrypt_staging(archive: str | Path, root: str | Path, secret: bytes) -> None:
    """Verify AEAD and MAR invariants before publishing a new restored folder."""
    source = Path(archive)
    destination = Path(root)
    if source.is_symlink() or not source.is_file():
        raise BackupRejected("backup_archive_missing")
    if source.stat().st_size > _MAX_ARCHIVE_BYTES:
        raise BackupRejected("backup_size_limit")
    try:
        envelope = json.loads(source.read_bytes())
        if not isinstance(envelope, dict) or envelope.get("version") != _VERSION:
            raise BackupRejected("backup_version_invalid")
        salt, nonce = _unb64(envelope.get("salt")), _unb64(envelope.get("nonce"))
        if len(nonce) != 12:
            raise BackupRejected("backup_nonce_invalid")
        plaintext = AESGCM(_key(secret, salt)).decrypt(
            nonce, _unb64(envelope.get("ciphertext")), _AAD
        )
        payload = json.loads(plaintext)
    except (InvalidTag, ValueError, UnicodeDecodeError) as exc:
        raise BackupRejected("backup_integrity_or_secret_invalid") from exc
    if not isinstance(payload, dict) or payload.get("version") != _VERSION:
        raise BackupRejected("backup_payload_invalid")
    entries = payload.get("files")
    if not isinstance(entries, list) or not 1 <= len(entries) <= _MAX_FILES:
        raise BackupRejected("backup_files_invalid")
    if destination.exists() or destination.is_symlink():
        raise BackupRejected("backup_restore_destination_exists")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with FileWriteLock(destination.parent / (destination.name + ".restore"),
                       timeout=10):
        if destination.exists() or destination.is_symlink():
            raise BackupRejected("backup_restore_destination_exists")
        temp = Path(tempfile.mkdtemp(prefix=".mar-p0-restore-", dir=destination.parent))
        try:
            seen = set()
            total = 0
            for entry in entries:
                if not isinstance(entry, dict):
                    raise BackupRejected("backup_file_entry_invalid")
                name, expected = entry.get("path"), entry.get("sha256")
                if not isinstance(name, str) or name in seen:
                    raise BackupRejected("backup_path_invalid")
                if name != "checkpoint.json" and not re.fullmatch(
                    r"raw/[0-9a-f]{2}/[0-9a-f]{64}\.json", name
                ):
                    raise BackupRejected("backup_path_invalid")
                if not isinstance(expected, str) or not _DIGEST.fullmatch(expected):
                    raise BackupRejected("backup_file_digest_invalid")
                seen.add(name)
                data = _unb64(entry.get("data"))
                total += len(data)
                if total > _MAX_BYTES:
                    raise BackupRejected("backup_size_limit")
                if hashlib.sha256(data).hexdigest() != expected:
                    raise BackupRejected("backup_file_digest_invalid")
                target = temp / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            if "checkpoint.json" not in seen:
                raise BackupRejected("backup_manifest_missing")
            _validate_dir(temp)
            os.rename(temp, destination)
        finally:
            if temp.exists():
                shutil.rmtree(temp)
