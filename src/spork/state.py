from typing import Any

from . import paths
from .config import now_iso, read_json, write_json


def load_state() -> dict[str, Any]:
    paths.ensure_dirs()
    return read_json(paths.installed_file(), {"schemaVersion": 1, "apps": []})


def save_state(data: dict[str, Any]) -> None:
    write_json(paths.installed_file(), data)


def get_installed(app_id: str) -> dict[str, Any] | None:
    for app in load_state().get("apps", []):
        if app.get("id") == app_id:
            return app
    return None


def list_installed() -> list[dict[str, Any]]:
    return list(load_state().get("apps", []))


def upsert_installed(app: dict[str, Any], action: str = "install", actual_version: str | None = None) -> None:
    data = load_state()
    apps = data.setdefault("apps", [])
    now = now_iso()
    existing = next((item for item in apps if item.get("id") == app["id"]), None)
    record = {
        "id": app["id"],
        "package": app["package"],
        "name": app.get("name", app["id"]),
        "version": actual_version or app["version"],
        "arch": app.get("arch"),
        "bucket": app.get("bucket"),
        "updatedAt": now,
        "lastAction": action,
    }
    if existing:
        record["installedAt"] = existing.get("installedAt", now)
        existing.clear()
        existing.update(record)
    else:
        record["installedAt"] = now
        apps.append(record)
    save_state(data)


def remove_installed(app_id: str) -> None:
    data = load_state()
    data["apps"] = [app for app in data.get("apps", []) if app.get("id") != app_id]
    save_state(data)


def set_hold(app_id: str, held: bool, app: dict[str, Any] | None = None) -> None:
    data = load_state()
    apps = data.setdefault("apps", [])
    existing = next((item for item in apps if item.get("id") == app_id), None)
    if not existing:
        source = app or {"id": app_id, "package": app_id, "name": app_id, "version": None}
        existing = {
            "id": source["id"],
            "package": source.get("package", source["id"]),
            "name": source.get("name", source["id"]),
            "version": source.get("version"),
            "arch": source.get("arch"),
            "bucket": source.get("bucket"),
            "installedAt": now_iso(),
            "updatedAt": now_iso(),
            "lastAction": "hold",
        }
        apps.append(existing)
    existing["held"] = held
    existing["updatedAt"] = now_iso()
    save_state(data)


def is_held(app_id: str) -> bool:
    app = get_installed(app_id)
    return bool(app and app.get("held"))
