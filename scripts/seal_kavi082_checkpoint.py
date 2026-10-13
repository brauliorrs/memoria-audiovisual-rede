"""Seal KAVI-082 checkpoint using X25519+HKDF+AES-256-GCM, no secret in CI.

The private key stays outside GitHub. Public repository receives only
encrypted checkpoint and redacted probe report. Never print source content.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import tarfile
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

AAD = b"kavi-finna-082-staged-metadata-three-batch-v1"
MAX_BYTES = 32 * 1024 * 1024


def seal(source: Path, output: Path, public_b64: str) -> None:
    if not source.is_dir() or source.is_symlink():
        raise ValueError("checkpoint_directory_unavailable")
    files = sorted(source.rglob("*"))
    total = 0
    for path in files:
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("checkpoint_contains_unsupported_file")
        if path.is_file():
            total += path.stat().st_size
        if total > MAX_BYTES:
            raise ValueError("checkpoint_exceeds_32mib_safety_cap")
    try:
        raw_public = base64.b64decode(public_b64, validate=True)
        public_key = x25519.X25519PublicKey.from_public_bytes(raw_public)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid_public_key") from exc
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as archive:
        for path in files:
            archive.add(
                path,
                arcname="kavi082/" + path.relative_to(source).as_posix(),
                recursive=False,
            )
    ephemeral = x25519.X25519PrivateKey.generate()
    salt, nonce = os.urandom(16), os.urandom(12)
    key = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=salt, info=AAD,
    ).derive(ephemeral.exchange(public_key))
    ciphertext = AESGCM(key).encrypt(nonce, buf.getvalue(), AAD)
    sealed = {
        "format": "kavi082-x25519-hkdf-aes256gcm-v1",
        "ephemeral_public_key_b64": base64.b64encode(
            ephemeral.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        ).decode("ascii"),
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "nonce_b64": base64.b64encode(nonce).decode("ascii"),
        "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sealed, sort_keys=True), encoding="utf-8")
    os.chmod(output, 0o600)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--public-key-b64", required=True)
    a = parser.parse_args()
    seal(a.directory, a.output, a.public_key_b64)
    print("Encrypted checkpoint sealed; no plaintext checkpoint exported.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
