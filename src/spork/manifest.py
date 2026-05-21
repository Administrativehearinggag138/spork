import json
from pathlib import Path
from typing import Any

from .errors import IndexError


def read_json_file(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise IndexError(f"JSON 格式错误：{path}: {exc}") from exc
    if not isinstance(data, dict):
        raise IndexError(f"JSON 顶层必须是对象：{path}")
    return data


def validate_generated_app(app: dict[str, Any], path: Path) -> None:
    required = ["id", "name", "package", "version", "arch", "url", "bucket", "updatedAt"]
    missing = [field for field in required if not app.get(field)]
    if missing:
        raise IndexError(f"generated index 缺少必要字段 {missing}：{path}")


def read_generated_dir(path: Path) -> list[dict[str, Any]]:
    apps: list[dict[str, Any]] = []
    if not path.exists():
        return apps
    for file_path in sorted(path.glob("*.json")):
        app = read_json_file(file_path)
        validate_generated_app(app, file_path)
        apps.append(app)
    return apps


def read_manifest_dir(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [read_json_file(file_path) for file_path in sorted(path.glob("*.json"))]
