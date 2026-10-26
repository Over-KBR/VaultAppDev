"""Génération locale des codes TOTP selon RFC 6238."""

import base64
import binascii
import hashlib
import hmac
import struct
import time


PERIOD_SECONDS = 30
CODE_DIGITS = 6
MIN_SECRET_BYTES = 10


def normalize_totp_secret(secret: str) -> str:
    """Valide un secret Base32 et retourne sa forme compacte en majuscules."""
    normalized = "".join(secret.split()).rstrip("=").upper()
    if not normalized:
        return ""

    padded = normalized + "=" * (-len(normalized) % 8)
    try:
        decoded = base64.b32decode(padded, casefold=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Le secret TOTP doit être une clé Base32 valide.") from exc

    if len(decoded) < MIN_SECRET_BYTES:
        raise ValueError("Le secret TOTP doit contenir au moins 80 bits.")
    return normalized


def generate_totp_code(secret: str, timestamp: float = None) -> str:
    """Génère le code courant à 6 chiffres pour un secret Base32."""
    normalized = normalize_totp_secret(secret)
    if not normalized:
        raise ValueError("Le secret TOTP est vide.")

    padded = normalized + "=" * (-len(normalized) % 8)
    key = base64.b32decode(padded, casefold=True)
    current_time = time.time() if timestamp is None else timestamp
    counter = int(current_time // PERIOD_SECONDS)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary_code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{binary_code % (10 ** CODE_DIGITS):0{CODE_DIGITS}d}"


def seconds_until_next_code(timestamp: float = None) -> int:
    """Retourne les secondes restantes avant le prochain code."""
    current_time = time.time() if timestamp is None else timestamp
    return PERIOD_SECONDS - int(current_time % PERIOD_SECONDS)