"""Unit tests for the idempotency store."""
import threading
import unittest

from paypal_webhook.idempotency import IdempotencyStore


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class IdempotencyTests(unittest.TestCase):
    def test_first_delivery_accepted_duplicate_rejected(self):
        store = IdempotencyStore(ttl_seconds=60)
        self.assertTrue(store.check_and_record("tx-1"))
        self.assertFalse(store.check_and_record("tx-1"))

    def test_distinct_ids_accepted(self):
        store = IdempotencyStore()
        self.assertTrue(store.check_and_record("a"))
        self.assertTrue(store.check_and_record("b"))

    def test_expired_id_accepted_again(self):
        clock = FakeClock()
        store = IdempotencyStore(ttl_seconds=60, clock=clock)
        self.assertTrue(store.check_and_record("tx-1"))
        clock.t = 61.0
        self.assertTrue(store.check_and_record("tx-1"))

    def test_empty_id_raises(self):
        store = IdempotencyStore()
        with self.assertRaises(ValueError):
            store.check_and_record("")

    def test_thread_safety_single_winner(self):
        store = IdempotencyStore()
        results = []
        lock = threading.Lock()

        def attempt():
            ok = store.check_and_record("same-id")
            with lock:
                results.append(ok)

        threads = [threading.Thread(target=attempt) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sum(results), 1)


if __name__ == "__main__":
    unittest.main()
