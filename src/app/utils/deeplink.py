import re

DEEPLINK_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def normalize_source_code(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    if not DEEPLINK_RE.match(value):
        return None
    return value

