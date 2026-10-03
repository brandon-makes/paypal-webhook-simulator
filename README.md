# paypal-webhook-simulator
**A lightweight Python CLI that generates and signs realistic PayPal webhook payloads for local testing - no PayPal account or ngrok required.**

## The problem it solves
Testing PayPal webhook integrations locally is cumbersome: you need a sandbox account, a publicly-exposed endpoint (often via ngrok), and manual steps to trigger events. This tool eliminates those friction points by producing authentic-looking webhook envelopes you can verify locally against your own shared secret.

## Features
- **Realistic event payloads** - supports common webhook types such as `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`, `CHECKOUT.ORDER.APPROVED`, etc.
- **Signature generation** - creates the `PayPal-Transmission-Sig` header using HMAC-SHA256 over a PayPal-style transmission string.
- **In-memory idempotency store** - keyed by `PayPal-Transmission-Id` with configurable TTL, enabling duplicate-delivery testing.
- **Zero external dependencies** - pure Python standard library, works with Python 3.10+.
- **CLI sub-commands** for simulation, verification, and stress-testing idempotent handling.

## Install
```bash
# Clone the repository
git clone https://github.com/brandon-makes/paypal-webhook-simulator.git
cd paypal-webhook-simulator

# No third-party packages required; just ensure Python 3.10+ is available
python -m venv .venv
source .venv/bin/activate
```

## Usage examples

### Simulate a webhook event
```bash
python -m paypal_webhook.cli --secret s3cret simulate \
    --event PAYMENT.CAPTURE.COMPLETED \
    --amount 49.99 \
    --currency EUR
```
The command prints a JSON envelope containing the signed headers and the event body.

### Verify a saved envelope
```bash
# Save the previous output to envelope.json
python -m paypal_webhook.cli --secret s3cret verify \
    --file envelope.json
```
Outputs `VALID` or `INVALID` and exits with status 0/1.

### Duplicate-delivery demo (idempotency)
```bash
python -m paypal_webhook.cli stress \
    --count 1000 \
    --duplicates 300 \
    --ttl 86400
```
Shows how many deliveries are accepted versus rejected and asserts exactly-once semantics.

## Project layout

```
paypal-webhook-simulator/
|- src/
|  |- paypal_webhook/
|     |- __init__.py
|     |- cli.py          # entry point for the command-line interface
|     |- simulator.py    # event templates, payload creation, signing
|     |- verifier.py     # HMAC-SHA256 signature verification utilities
|     |- idempotency.py  # in-memory store for transmission-id deduplication
|- tests/
|  |- ...                # unit tests for simulator, verifier, idempotency
|- run_tests.py          # test runner
|- README.md             # this file
|- pyproject.toml        # package metadata (optional)
```

## Running the tests
```bash
python run_tests.py
```
All tests are written using the standard library's `unittest` framework and require no external packages.

## How it relates to PayPal
The simulator mirrors the shape of PayPal's webhook format:

| Header / Field                | Description |
|------------------------------|----------------------------------|
| `PayPal-Transmission-Id`      | Unique identifier for the delivery |
| `PayPal-Transmission-Time`   | UTC timestamp of the transmission |
| `PayPal-Transmission-Sig`     | HMAC-SHA256 of the transmission string (local simulation only - see Limitations) |
| `PayPal-Cert-Url` (optional)  | URL of PayPal's signing certificate |
| `PayPal-Auth-Algo` (optional) | Algorithm used (`SHA256withRSA` in live PayPal traffic) |
| Body (`event` JSON)           | Conforms to PayPal's webhook event schema (resource, summary, etc.) |

The transmission string is built in the same layout PayPal documents:

```
transmission_id | transmission_time | webhook_id | crc32(body)
```

## Limitations
- **Local simulation only.** Real PayPal webhooks are verified with asymmetric signature verification: you call PayPal's `verify-webhook-signature` API (or verify the `transmission_sig` against the certificate at `cert_url` using `auth_algo`, e.g. `SHA256withRSA`). This tool instead uses its own HMAC-SHA256 signature with a developer-provided shared secret, so simulated payloads **will not pass PayPal's real verification endpoint**, and real PayPal payloads cannot be verified with this tool's HMAC check.
- The point of the tool is to exercise your own webhook-handling code paths (parsing, signature-check logic, idempotency) end to end on your machine, not to reproduce PayPal's production signature scheme.

---

*Happy hacking!*

- Brandon
