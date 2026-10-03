"""Unit tests for signature verification."""
import json
import unittest

from paypal_webhook.simulator import make_event, sign_event
from paypal_webhook.verifier import verify_signature

SECRET = "test-webhook-secret"
WEBHOOK_ID = "WH-TEST-123"


class VerifyTests(unittest.TestCase):
    def _envelope(self):
        event = make_event("PAYMENT.CAPTURE.COMPLETED")
        return sign_event(event, SECRET, WEBHOOK_ID)

    def test_valid_signature_passes(self):
        env = self._envelope()
        ok = verify_signature(
            env["body"].encode(),
            env["headers"]["paypal-transmission-id"],
            env["headers"]["paypal-transmission-time"],
            WEBHOOK_ID,
            SECRET,
            env["headers"]["paypal-transmission-sig"],
        )
        self.assertTrue(ok)

    def test_tampered_body_fails(self):
        env = self._envelope()
        body = json.loads(env["body"])
        body["resource"]["amount"]["value"] = "9999.00"
        ok = verify_signature(
            json.dumps(body, separators=(",", ":")).encode(),
            env["headers"]["paypal-transmission-id"],
            env["headers"]["paypal-transmission-time"],
            WEBHOOK_ID,
            SECRET,
            env["headers"]["paypal-transmission-sig"],
        )
        self.assertFalse(ok)

    def test_wrong_secret_fails(self):
        env = self._envelope()
        ok = verify_signature(
            env["body"].encode(),
            env["headers"]["paypal-transmission-id"],
            env["headers"]["paypal-transmission-time"],
            WEBHOOK_ID,
            "attacker-secret",
            env["headers"]["paypal-transmission-sig"],
        )
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
