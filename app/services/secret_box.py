"""Encryption at rest for the QuickBooks Online tokens (25 Oct 2026).

The key is the server's ``QBO_TOKEN_KEY`` environment setting (at least 32 random bytes, URL-safe base64; make one
with ``python -c "import secrets,base64;print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"``). It is
never stored in the database, the code, Git or the logs. Without it, nothing is stored and the connection refuses.

The application's locked dependencies have no cipher library, so this uses only the standard library: an
encrypt-then-MAC construction from HMAC-SHA256 (keystream = HMAC(enc_key, nonce || counter), tag = HMAC(mac_key,
version || nonce || ciphertext), separate keys derived from the setting, a fresh 16-byte random nonce per value,
constant-time tag check). A value that was changed, or made with another key, is refused, never half-read.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets

from flask import current_app, has_app_context

ENV_KEY = "QBO_TOKEN_KEY"
VERSION = b"cbx1"
NONCE_BYTES = 16
TAG_BYTES = 32


class SecretBoxError(RuntimeError):
    pass


def _raw_key() -> bytes:
    value = ""
    if has_app_context():
        value = str(current_app.config.get(ENV_KEY) or "")
    value = value or os.environ.get(ENV_KEY, "")
    if not value:
        raise SecretBoxError("QBO_TOKEN_KEY is not set on the server.")
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, TypeError):
        raise SecretBoxError("QBO_TOKEN_KEY is not valid base64.") from None
    if len(raw) < 32:
        raise SecretBoxError("QBO_TOKEN_KEY must be at least 32 random bytes.")
    return raw


def key_present() -> bool:
    try:
        _raw_key()
    except SecretBoxError:
        return False
    return True


def _keys():
    raw = _raw_key()
    return (hmac.new(raw, b"calibraytai-qbo-enc", hashlib.sha256).digest(),
            hmac.new(raw, b"calibraytai-qbo-mac", hashlib.sha256).digest())


def _stream(enc_key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out.extend(hmac.new(enc_key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest())
        counter += 1
    return bytes(out[:length])


def seal(plaintext: str) -> str:
    if plaintext is None:
        raise SecretBoxError("Nothing to encrypt.")
    enc_key, mac_key = _keys()
    data = plaintext.encode("utf-8")
    nonce = secrets.token_bytes(NONCE_BYTES)
    body = bytes(a ^ b for a, b in zip(data, _stream(enc_key, nonce, len(data))))
    tag = hmac.new(mac_key, VERSION + nonce + body, hashlib.sha256).digest()
    return VERSION.decode() + ":" + base64.urlsafe_b64encode(nonce + body + tag).decode()


def open_sealed(token: str) -> str:
    if not token or not token.startswith(VERSION.decode() + ":"):
        raise SecretBoxError("The stored value is not an encrypted value.")
    enc_key, mac_key = _keys()
    try:
        blob = base64.urlsafe_b64decode(token.split(":", 1)[1].encode())
    except (ValueError, TypeError):
        raise SecretBoxError("The stored value is damaged.") from None
    if len(blob) < NONCE_BYTES + TAG_BYTES:
        raise SecretBoxError("The stored value is damaged.")
    nonce, body, tag = blob[:NONCE_BYTES], blob[NONCE_BYTES:-TAG_BYTES], blob[-TAG_BYTES:]
    expected = hmac.new(mac_key, VERSION + nonce + body, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise SecretBoxError("The stored value was changed or made with another key.")
    data = bytes(a ^ b for a, b in zip(body, _stream(enc_key, nonce, len(body))))
    return data.decode("utf-8")
