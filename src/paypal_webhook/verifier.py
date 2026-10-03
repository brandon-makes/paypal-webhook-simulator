"""PayPal webhook signature verification.

Real PayPal verification uses their /v1/notifications/verify-webhook-signature
endpoint. This module implements the offline equivalent: HMAC-SHA256 of the
transmission string against the webhook secret, which is the scheme PayPal
documents for self-verification of webhook payloads, and a pluggable verifier
interface so the live API call can be swapped in.

Transmission string format (documented by PayPal):
    transmission_id | transmission_time | webhook_id | crc32(body)
"""
import hashlib
import hmac
import zlib


def build_transmission_string(
    transmission_id: str,
    transmission_time: str,
    webhook_id: str,
    body: bytes,
) -> str:
    crc = zlib.crc32(body) & 0xFFFFFFFF
    return f"{transmission_id}|{transmission_time}|{webhook_id}|{crc}"


def expected_signature(transmission_string: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        transmission_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_signature(
    body: bytes,
    transmission_id: str,
    transmission_time: str,
    webhook_id: str,
    secret: str,
    provided_signature: str,
) -> bool:
    """Constant-time verification of a webhook signature."""
    ts = build_transmission_string(transmission_id, transmission_time, webhook_id, body)
    expected = expected_signature(ts, secret)
    return hmac.compare_digest(expected, provided_signature.lower())
