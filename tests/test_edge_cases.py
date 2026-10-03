"""Edge-case tests: malformed input, missing headers, CLI behaviour."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from paypal_webhook.simulator import make_event, sign_event
from paypal_webhook.verifier import verify_signature

SECRET = "edge-secret"
WEBHOOK_ID = "WH-EDGE-1"
ROOT = os.path.join(os.path.dirname(__file__), "..")


def _cli(*argv):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(ROOT, "src")
    return subprocess.run(
        [sys.executable, "-m", "paypal_webhook.cli", *argv],
        capture_output=True, text=True, env=env, cwd=ROOT,
    )


class MissingHeaderTests(unittest.TestCase):
    def setUp(self):
        event = make_event("PAYMENT.CAPTURE.COMPLETED")
        self.env = sign_event(event, SECRET, WEBHOOK_ID)

    def test_empty_transmission_id_fails(self):
        ok = verify_signature(
            self.env["body"].encode(), "", self.env["headers"]["paypal-transmission-time"],
            WEBHOOK_ID, SECRET, self.env["headers"]["paypal-transmission-sig"])
        self.assertFalse(ok)

    def test_empty_signature_fails(self):
        ok = verify_signature(
            self.env["body"].encode(), self.env["headers"]["paypal-transmission-id"],
            self.env["headers"]["paypal-transmission-time"], WEBHOOK_ID, SECRET, "")
        self.assertFalse(ok)

    def test_garbage_signature_fails(self):
        ok = verify_signature(
            self.env["body"].encode(), self.env["headers"]["paypal-transmission-id"],
            self.env["headers"]["paypal-transmission-time"], WEBHOOK_ID, SECRET,
            "not-a-hex-signature!!!")
        self.assertFalse(ok)

    def test_wrong_webhook_id_fails(self):
        ok = verify_signature(
            self.env["body"].encode(), self.env["headers"]["paypal-transmission-id"],
            self.env["headers"]["paypal-transmission-time"], "WH-OTHER", SECRET,
            self.env["headers"]["paypal-transmission-sig"])
        self.assertFalse(ok)

    def test_uppercase_signature_accepted(self):
        ok = verify_signature(
            self.env["body"].encode(), self.env["headers"]["paypal-transmission-id"],
            self.env["headers"]["paypal-transmission-time"], WEBHOOK_ID, SECRET,
            self.env["headers"]["paypal-transmission-sig"].upper())
        self.assertTrue(ok)


class SimulatorTests(unittest.TestCase):
    def test_unknown_event_type_raises(self):
        with self.assertRaises(ValueError):
            make_event("NOT.A.REAL.EVENT")

    def test_all_templates_produce_required_fields(self):
        from paypal_webhook.simulator import _EVENT_TEMPLATES
        for et in _EVENT_TEMPLATES:
            ev = make_event(et, amount="10.00", currency="USD")
            self.assertEqual(ev["event_type"], et)
            self.assertIn("id", ev)
            self.assertIn("create_time", ev)


class CliTests(unittest.TestCase):
    def test_simulate_then_verify_roundtrip(self):
        r = _cli("--secret", SECRET, "simulate", "--event", "CHECKOUT.ORDER.APPROVED",
                 "--amount", "9.99", "--currency", "EUR")
        self.assertEqual(r.returncode, 0, r.stderr)
        env = json.loads(r.stdout)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(env, f)
            path = f.name
        try:
            v = _cli("--secret", SECRET, "verify", "--file", path)
            self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
            self.assertIn("VALID", v.stdout)
        finally:
            os.unlink(path)

    def test_verify_tampered_file_exits_1(self):
        r = _cli("--secret", SECRET, "simulate")
        env = json.loads(r.stdout)
        env["body"] = env["body"].replace("25.00", "99999.00")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(env, f)
            path = f.name
        try:
            v = _cli("--secret", SECRET, "verify", "--file", path)
            self.assertEqual(v.returncode, 1)
            self.assertIn("INVALID", v.stdout)
        finally:
            os.unlink(path)

    def test_stress_exactly_once(self):
        r = _cli("stress", "--count", "200", "--duplicates", "50")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)

    def _write_tmp(self, text):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        f.write(text)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_verify_malformed_json_file_exits_1_no_traceback(self):
        path = self._write_tmp("{not valid json")
        v = _cli("--secret", SECRET, "verify", "--file", path)
        self.assertEqual(v.returncode, 1)
        self.assertIn("INVALID", v.stdout)
        self.assertNotIn("Traceback", v.stderr)

    def test_verify_missing_headers_exits_1_no_traceback(self):
        path = self._write_tmp(json.dumps({"body": "{}", "webhook_id": "WH-1"}))
        v = _cli("--secret", SECRET, "verify", "--file", path)
        self.assertEqual(v.returncode, 1)
        self.assertIn("INVALID", v.stdout)
        self.assertNotIn("Traceback", v.stderr)

    def test_verify_missing_file_exits_1_no_traceback(self):
        v = _cli("--secret", SECRET, "verify", "--file", "/nonexistent/env.json")
        self.assertEqual(v.returncode, 1)
        self.assertIn("INVALID", v.stdout)
        self.assertNotIn("Traceback", v.stderr)


if __name__ == "__main__":
    unittest.main()
