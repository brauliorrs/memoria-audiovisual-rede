"""Local-only encryption self-test: no network, no real KAVI metadata."""
from __future__ import annotations

import base64
import io
import json
import tempfile
import tarfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from scripts.seal_kavi082_checkpoint import AAD, seal


class SealCheckpointTests(unittest.TestCase):
    def test_encrypted_roundtrip_and_plaintext_absent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "raw"
            source.mkdir()
            (source / "checkpoint.json").write_text(
                '{"cursor":"very-secret-test-token"}', encoding="utf-8"
            )
            priv = x25519.X25519PrivateKey.generate()
            pub_b64 = base64.b64encode(priv.public_key().public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            )).decode("ascii")
            output = root / "sealed.json"
            seal(source, output, pub_b64)
            sealed = json.loads(output.read_text(encoding="utf-8"))
            self.assertNotIn("very-secret-test-token", output.read_text())
            self.assertEqual(sealed["format"], "kavi082-x25519-hkdf-aes256gcm-v1")
            decode = lambda name: base64.b64decode(sealed[name], validate=True)
            ephemeral = x25519.X25519PublicKey.from_public_bytes(
                decode("ephemeral_public_key_b64")
            )
            key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=decode("salt_b64"),
                info=AAD,
            ).derive(priv.exchange(ephemeral))
            clear = AESGCM(key).decrypt(
                decode("nonce_b64"), decode("ciphertext_b64"), AAD,
            )
            with tarfile.open(fileobj=io.BytesIO(clear), mode="r:gz") as archive:
                saved = archive.extractfile("kavi082/checkpoint.json")
                self.assertIsNotNone(saved)
                self.assertEqual(
                    saved.read(),
                    b'{"cursor":"very-secret-test-token"}',
                )

    def test_invalid_public_key_and_existing_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, "invalid_public_key"):
                seal(source, root / "sealed.json", "bad!")
            (source / "link").symlink_to(root)
            public = x25519.X25519PrivateKey.generate().public_key()
            pub = base64.b64encode(public.public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            )).decode("ascii")
            with self.assertRaisesRegex(
                ValueError, "checkpoint_contains_unsupported_file"
            ):
                seal(source, root / "sealed.json", pub)


if __name__ == "__main__":
    unittest.main()
