"""Generate realistic PayPal webhook event fixtures and signed envelopes."""
import json
import time
import uuid

from .verifier import build_transmission_string, expected_signature

_EVENT_TEMPLATES = {
    "PAYMENT.CAPTURE.COMPLETED": {
        "resource_type": "capture",
        "summary": "Payment completed for $ {amount} {currency}",
        "resource": {
            "id": "CAPTURE-{n}",
            "status": "COMPLETED",
            "amount": {"currency_code": "{currency}", "value": "{amount}"},
        },
    },
    "PAYMENT.CAPTURE.REFUNDED": {
        "resource_type": "refund",
        "summary": "Refund completed for $ {amount} {currency}",
        "resource": {
            "id": "REFUND-{n}",
            "status": "COMPLETED",
            "amount": {"currency_code": "{currency}", "value": "{amount}"},
        },
    },
    "CUSTOMER.DISPUTE.CREATED": {
        "resource_type": "dispute",
        "summary": "A dispute has been opened",
        "resource": {
            "dispute_id": "PP-D-{n}",
            "status": "OPEN",
            "reason": "MERCHANDISE_OR_SERVICE_NOT_RECEIVED",
        },
    },
    "CHECKOUT.ORDER.APPROVED": {
        "resource_type": "order",
        "summary": "Order approved for $ {amount} {currency}",
        "resource": {
            "id": "ORDER-{n}",
            "status": "APPROVED",
            "purchase_units": [
                {"amount": {"currency_code": "{currency}", "value": "{amount}"}}
            ],
        },
    },
}


def make_event(event_type: str, amount: str = "25.00", currency: str = "USD") -> dict:
    if event_type not in _EVENT_TEMPLATES:
        raise ValueError(f"unknown event type: {event_type}")
    n = uuid.uuid4().hex[:12].upper()
    tpl = json.loads(json.dumps(_EVENT_TEMPLATES[event_type]))
    blob = json.dumps(tpl).replace("{n}", n).replace("{amount}", amount).replace(
        "{currency}", currency
    )
    resource = json.loads(blob)
    return {
        "id": f"WH-{n}",
        "event_version": "1.0",
        "create_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event_type": event_type,
        **resource,
    }


def sign_event(
    event: dict,
    secret: str,
    webhook_id: str = "WH-TEST-123",
    transmission_id: str | None = None,
) -> dict:
    """Wrap an event in a signed transmission envelope."""
    body = json.dumps(event, separators=(",", ":")).encode("utf-8")
    transmission_id = transmission_id or uuid.uuid4().hex
    transmission_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ts = build_transmission_string(transmission_id, transmission_time, webhook_id, body)
    return {
        "headers": {
            "paypal-transmission-id": transmission_id,
            "paypal-transmission-time": transmission_time,
            "paypal-transmission-sig": expected_signature(ts, secret),
        },
        "webhook_id": webhook_id,
        "body": body.decode("utf-8"),
    }
