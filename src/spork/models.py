from dataclasses import dataclass
from typing import Any


REQUIRED_INDEX_FIELDS = {
    "id",
    "name",
    "package",
    "version",
    "arch",
    "url",
    "bucket",
    "updatedAt",
}


@dataclass(frozen=True)
class AppRef:
    id: str
    package: str
    name: str | None = None
    version: str | None = None


def require_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing or invalid field: {field}")
    return value
