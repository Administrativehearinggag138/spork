import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import paths
from .i18n import normalize_language
from .package_managers import detect_package_manager


DEFAULT_CONFIG = {
    "schemaVersion": 1,
    "autoUpdateBuckets": True,
    "downloadTimeoutSeconds": 120,
    "installConfirm": True,
    "language": normalize_language(os.environ.get("LANG")),
    "packageManager": detect_package_manager(),
}

ENV_OVERRIDES = {
    "SPORK_AUTO_UPDATE_BUCKETS": ("autoUpdateBuckets", "bool"),
    "SPORK_DOWNLOAD_TIMEOUT_SECONDS": ("downloadTimeoutSeconds", int),
    "SPORK_INSTALL_CONFIRM": ("installConfirm", "bool"),
    "SPORK_LANG": ("language", str),
    "SPORK_LANGUAGE": ("language", str),
    "SPORK_PACKAGE_MANAGER": ("packageManager", str),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default.copy()
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _parse_env_value(value: str, parser: Any) -> Any:
    if parser == "bool":
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return parser(value)


def _apply_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    for env_name, (key, parser) in ENV_OVERRIDES.items():
        if env_name in os.environ:
            data[key] = _parse_env_value(os.environ[env_name], parser)
    if data.get("language") == "auto":
        data["language"] = normalize_language(os.environ.get("LANG"))
    elif "language" in data:
        data["language"] = normalize_language(str(data["language"]))
    return data


def load_config() -> dict[str, Any]:
    paths.ensure_dirs()
    data = DEFAULT_CONFIG.copy()
    data.update(read_json(paths.config_file(), DEFAULT_CONFIG))
    return _apply_env_overrides(data)


def save_config(data: dict[str, Any]) -> None:
    write_json(paths.config_file(), data)


def load_buckets() -> dict[str, Any]:
    paths.ensure_dirs()
    return read_json(paths.buckets_file(), {"schemaVersion": 1, "buckets": []})


def save_buckets(data: dict[str, Any]) -> None:
    write_json(paths.buckets_file(), data)


def load_trusted_buckets() -> dict[str, Any]:
    paths.ensure_dirs()
    return read_json(paths.trusted_buckets_file(), {"schemaVersion": 1, "trusted": []})


def save_trusted_buckets(data: dict[str, Any]) -> None:
    write_json(paths.trusted_buckets_file(), data)


def ensure_initial_files() -> None:
    paths.ensure_dirs()
    if not paths.config_file().exists():
        save_config(DEFAULT_CONFIG.copy())
    if not paths.buckets_file().exists():
        save_buckets({"schemaVersion": 1, "buckets": []})
    if not paths.trusted_buckets_file().exists():
        save_trusted_buckets({"schemaVersion": 1, "trusted": []})
