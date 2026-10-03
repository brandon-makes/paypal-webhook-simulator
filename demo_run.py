import sys, os, json, subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from paypal_webhook.cli import main

print("--- simulate ---")
main(["--secret", "s3cret", "simulate", "--event", "CUSTOMER.DISPUTE.CREATED"])

# round-trip: simulate to file, then verify
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    main(["--secret", "s3cret", "simulate", "--event", "PAYMENT.CAPTURE.REFUNDED"])
env = json.loads(buf.getvalue())
with open("envelope.json", "w") as f:
    json.dump(env, f)

print("--- verify ---")
main(["--secret", "s3cret", "verify", "--file", "envelope.json"])

print("--- stress ---")
main(["stress", "--count", "500", "--duplicates", "200"])
