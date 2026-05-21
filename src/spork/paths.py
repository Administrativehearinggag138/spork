import os
from pathlib import Path

from .branding import APP_DIR_NAME

APP_NAME = APP_DIR_NAME


def root_dir() -> Path:
    return Path(os.environ.get("SPORK_HOME", Path.home() / f".{APP_NAME}")).expanduser()


def config_dir() -> Path:
    return root_dir() / "config"


def data_dir() -> Path:
    return root_dir()


def cache_dir() -> Path:
    return root_dir() / "cache"


def buckets_dir() -> Path:
    return root_dir() / "buckets"


def apps_dir() -> Path:
    return root_dir() / "apps"


def shims_dir() -> Path:
    return root_dir() / "shims"


def app_dir(app_name: str) -> Path:
    return apps_dir() / app_name


def current_app_dir(app_name: str) -> Path:
    return app_dir(app_name) / "current"


def state_dir() -> Path:
    return root_dir() / "state"


def index_dir() -> Path:
    return cache_dir() / "index"


def downloads_dir() -> Path:
    return cache_dir() / "downloads"


def config_file() -> Path:
    return config_dir() / "config.json"


def buckets_file() -> Path:
    return config_dir() / "buckets.json"


def trusted_buckets_file() -> Path:
    return config_dir() / "trusted-buckets.json"


def merged_index_file() -> Path:
    return index_dir() / "merged.json"


def installed_file() -> Path:
    return state_dir() / "installed.json"


def ensure_dirs() -> None:
    for path in (config_dir(), buckets_dir(), apps_dir(), shims_dir(), state_dir(), index_dir(), downloads_dir()):
        path.mkdir(parents=True, exist_ok=True)
