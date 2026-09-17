"""Ed25519 keys and signatures for map sidecars.

The private key never belongs in a repository. `keygen` writes it with owner only permissions
and prints a reminder.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature

__all__ = [
    "InvalidSignature",
    "generate_keypair",
    "load_private_key",
    "load_public_key",
    "public_key_bytes",
    "key_id",
    "sign",
    "verify",
]


def generate_keypair(out_stem: str | Path) -> tuple[Path, Path]:
    """Write `<stem>.pem` (private) and `<stem>.pub.pem` (public). Returns both paths."""
    stem = Path(out_stem)
    private_path = stem.with_suffix(".pem")
    public_path = stem.with_name(stem.name + ".pub.pem")

    private = Ed25519PrivateKey.generate()
    private_bytes = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_path.write_bytes(private_bytes)
    private_path.chmod(0o600)
    public_path.write_bytes(public_bytes)
    return private_path, public_path


def load_private_key(path: str | Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError(f"{path} is not an Ed25519 private key")
    return key


def load_public_key(path: str | Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(Path(path).read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError(f"{path} is not an Ed25519 public key")
    return key


def public_key_bytes(key: Ed25519PublicKey) -> bytes:
    return key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def key_id(key: Ed25519PublicKey) -> str:
    return "sha256:" + hashlib.sha256(public_key_bytes(key)).hexdigest()


def sign(private: Ed25519PrivateKey, payload: bytes) -> bytes:
    return private.sign(payload)


def verify(public: Ed25519PublicKey, signature: bytes, payload: bytes) -> None:
    """Raises `InvalidSignature` if the signature does not match."""
    public.verify(signature, payload)
