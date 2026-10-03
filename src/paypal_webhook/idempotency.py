"""In-memory idempotency store keyed by PayPal-Transmission-Id, with TTL."""
import threading
import time


class IdempotencyStore:
    """Thread-safe store that rejects duplicate webhook deliveries within a TTL."""

    def __init__(self, ttl_seconds: float = 86400.0, clock=time.monotonic):
        self.ttl = ttl_seconds
        self._clock = clock
        self._seen: dict[str, float] = {}
        self._lock = threading.Lock()

    def check_and_record(self, transmission_id: str) -> bool:
        """Return True if this delivery is new (and record it); False if duplicate."""
        if not transmission_id:
            raise ValueError("transmission_id must be a non-empty string")
        now = self._clock()
        with self._lock:
            self._expire(now)
            if transmission_id in self._seen:
                return False
            self._seen[transmission_id] = now
            return True

    def _expire(self, now: float) -> None:
        cutoff = now - self.ttl
        stale = [k for k, t in self._seen.items() if t < cutoff]
        for k in stale:
            del self._seen[k]

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._seen)
