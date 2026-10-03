"""CLI for the PayPal webhook simulator.

Usage:
    python -m paypal_webhook.cli simulate --event PAYMENT.CAPTURE.COMPLETED --secret s3cret
    python -m paypal_webhook.cli verify --file envelope.json --secret s3cret
    python -m paypal_webhook.cli stress --count 1000 --duplicates 300
"""
import argparse
import json
import random
import sys

from .idempotency import IdempotencyStore
from .simulator import _EVENT_TEMPLATES, make_event, sign_event
from .verifier import verify_signature

SECRET_DEFAULT = "dev-secret"


def cmd_simulate(args):
    event = make_event(args.event, amount=args.amount, currency=args.currency)
    env = sign_event(event, args.secret)
    print(json.dumps(env, indent=2))


def cmd_verify(args):
    with open(args.file) as f:
        env = json.load(f)
    ok = verify_signature(
        env["body"].encode(),
        env["headers"]["paypal-transmission-id"],
        env["headers"]["paypal-transmission-time"],
        env["webhook_id"],
        args.secret,
        env["headers"]["paypal-transmission-sig"],
    )
    print("VALID" if ok else "INVALID")
    sys.exit(0 if ok else 1)


def cmd_stress(args):
    store = IdempotencyStore(ttl_seconds=args.ttl)
    ids = [f"tx-{i}" for i in range(args.count)]
    deliveries = ids + random.sample(ids, min(args.duplicates, len(ids)))
    random.shuffle(deliveries)
    accepted = sum(1 for d in deliveries if store.check_and_record(d))
    rejected = len(deliveries) - accepted
    print(f"deliveries={len(deliveries)} accepted={accepted} duplicates_rejected={rejected}")
    assert accepted == args.count, "every unique delivery must be accepted exactly once"
    print("OK: exactly-once semantics held")


def main(argv=None):
    p = argparse.ArgumentParser(prog="paypal-webhook-simulator")
    p.add_argument("--secret", default=SECRET_DEFAULT)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("simulate", help="generate a signed webhook envelope")
    s.add_argument("--event", default="PAYMENT.CAPTURE.COMPLETED",
                   choices=sorted(_EVENT_TEMPLATES))
    s.add_argument("--amount", default="25.00")
    s.add_argument("--currency", default="USD")
    s.set_defaults(fn=cmd_simulate)

    v = sub.add_parser("verify", help="verify a signed envelope file")
    v.add_argument("--file", required=True)
    v.set_defaults(fn=cmd_verify)

    t = sub.add_parser("stress", help="stress-test idempotent delivery handling")
    t.add_argument("--count", type=int, default=1000)
    t.add_argument("--duplicates", type=int, default=300)
    t.add_argument("--ttl", type=float, default=86400.0)
    t.set_defaults(fn=cmd_stress)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
