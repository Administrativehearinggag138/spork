from pathlib import Path
from typing import Any

from . import paths
from .bucket import list_buckets, update_bucket
from .config import load_config, now_iso, write_json
from .errors import AppNotFoundError, IndexError
from .manifest import read_generated_dir, read_manifest_dir, validate_generated_app
from .output import warn
from .providers import resolve_manifest


def _bucket_apps(bucket: dict[str, Any], allow_local_resolve: bool) -> list[dict[str, Any]]:
    bucket_path = Path(bucket["path"])
    generated = read_generated_dir(bucket_path / "generated")
    if generated:
        for app in generated:
            app["bucket"] = bucket["name"]
        return generated
    if not allow_local_resolve:
        warn(f"bucket {bucket['name']} 没有 generated index，已跳过。")
        return []
    if not bucket.get("trusted", False):
        warn(f"bucket {bucket['name']} 未被信任，不能执行本地解析。")
        return []
    apps: list[dict[str, Any]] = []
    for manifest in read_manifest_dir(bucket_path / "apps"):
        try:
            app = resolve_manifest(manifest)
            app["bucket"] = bucket["name"]
            validate_generated_app(app, bucket_path / "apps" / f"{manifest.get('id', 'unknown')}.json")
            apps.append(app)
        except Exception as exc:
            warn(f"解析 {manifest.get('id', '<unknown>')} 失败：{exc}")
    return apps


def update_index(local_resolve: bool = False, no_bucket_update: bool = False) -> dict[str, Any]:
    config = load_config()
    if config.get("autoUpdateBuckets", True) and not no_bucket_update:
        update_bucket()

    allow_local_resolve = local_resolve or bool(config.get("allowLocalResolve", False))
    merged_by_id: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    for bucket in list_buckets():
        apps = _bucket_apps(bucket, allow_local_resolve)
        bucket_index = {"schemaVersion": 1, "updatedAt": now_iso(), "apps": apps}
        write_json(paths.index_dir() / f"{bucket['name']}.json", bucket_index)
        for app in apps:
            app_id = app["id"]
            if app_id in merged_by_id:
                warn(f"应用 {app_id} 在多个 bucket 中重复，后添加的 bucket {bucket['name']} 优先。")
            else:
                ordered_ids.append(app_id)
            merged_by_id[app_id] = app
    merged = {
        "schemaVersion": 1,
        "updatedAt": now_iso(),
        "apps": [merged_by_id[app_id] for app_id in ordered_ids if app_id in merged_by_id],
    }
    write_json(paths.merged_index_file(), merged)
    return merged


def load_index() -> dict[str, Any]:
    if not paths.merged_index_file().exists():
        raise IndexError("本地索引不存在，请先执行：\n  spork update")
    from .config import read_json

    return read_json(paths.merged_index_file(), {"schemaVersion": 1, "apps": []})


def all_apps() -> list[dict[str, Any]]:
    return list(load_index().get("apps", []))


def find_app(app_id: str) -> dict[str, Any]:
    for app in all_apps():
        if app.get("id") == app_id:
            return app
    raise AppNotFoundError(f"未找到应用：{app_id}\n\n可以执行：\n  spork search {app_id}")


def search_apps(keyword: str) -> list[dict[str, Any]]:
    needle = keyword.lower()
    fields = ("id", "name", "package", "description")
    return [
        app
        for app in all_apps()
        if any(needle in str(app.get(field, "")).lower() for field in fields)
    ]
