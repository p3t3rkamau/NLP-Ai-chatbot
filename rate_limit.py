"""Simple in-memory rate limiting by key."""

import time
from collections import defaultdict, deque
from config import RATE_LIMIT_WINDOW_SECONDS, RATE_LIMIT_MAX_REQUESTS

_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def is_limited(key: str) -> bool:
    now = time.time()
    q = _BUCKETS[key]
    while q and now - q[0] > RATE_LIMIT_WINDOW_SECONDS:
        q.popleft()
    if len(q) >= RATE_LIMIT_MAX_REQUESTS:
        return True
    q.append(now)
    return False
