import time
from collections import defaultdict, deque

_USER_EVENTS: dict[int, deque[float]] = defaultdict(deque)


def is_support_spam(user_id: int, max_messages: int = 5, window_seconds: int = 10) -> bool:
    now = time.monotonic()
    bucket = _USER_EVENTS[user_id]
    while bucket and bucket[0] < now - window_seconds:
        bucket.popleft()
    if len(bucket) >= max_messages:
        return True
    bucket.append(now)
    return False

