import json
import shutil
from pathlib import Path
from typing import Any

from . import cache
from .config import load_buckets, load_config, save_buckets, save_config, write_json
from .downloader import download
from .errors import DebupError
from .i18n import t
from .index import find_app
from .manifest import read_json_file
from .output import confirm, print_json
from .package_managers import get_package_manager
from .state import list_installed, set_hold


UNSUPPORTED_REASONS = {
    "alias": "Scoop alias depends on PowerShell profile behavior; shell aliases should be managed by the user's shell.",
    "prefix": "Scoop prefix returns a portable app directory. Spork installs system packages through the configured package manager, so there is no app-owned prefix.",
    "reset": "Scoop reset fixes shim conflicts between portable versions. The system package manager owns package activation on Linux.",
    "shim": "Spork only creates a self shim for the spork command. Managed app executables are provided by Debian packages.",
    "virustotal": "VirusTotal integration requires an external service and does not belong in the core offline package manager.",
}


def unsupported(command: str) -> None:
    print(t("unsupported", command=command))
    print(t("unsupported_detail", reason=UNSUPPORTED_REASONS[command]))


def parse_config_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"null", "none"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def config_command(args: Any) -> None:
    data = load_config()
    if args.config_command == "list":
        print_json(data) if args.json else [print(f"{key}={value}") for key, value in sorted(data.items())]
    elif args.config_command == "get":
        if args.key not in data:
            raise DebupError(t("config_key_missing", key=args.key))
        value = data[args.key]
        print_json({args.key: value}) if args.json else print(value)
    elif args.config_command == "set":
        data[args.key] = parse_config_value(args.value)
        save_config(data)
        print(t("config_updated", key=args.key, value=data[args.key]))


def cat_command(app_id: str) -> None:
    app = find_app(app_id)
    print_json(app)


def download_command(app_id: str) -> Path:
    app = find_app(app_id)
    timeout = int(load_config().get("downloadTimeoutSeconds", 120))
    path = download(app, timeout)
    print(t("downloaded", path=path))
    return path


def export_command(path: Path | None, include_config: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schemaVersion": 1,
        "buckets": load_buckets().get("buckets", []),
        "apps": [
            {
                "id": app.get("id"),
                "package": app.get("package"),
                "version": app.get("version"),
                "held": bool(app.get("held")),
            }
            for app in list_installed()
        ],
    }
    if include_config:
        data["config"] = load_config()
    if path:
        write_json(path, data)
        print(t("exported", path=path))
    else:
        print_json(data)
    return data


def import_command(path: Path, include_config: bool = False) -> None:
    data = read_json_file(path)
    if include_config and isinstance(data.get("config"), dict):
        current = load_config()
        current.update(data["config"])
        save_config(current)
    if isinstance(data.get("buckets"), list):
        save_buckets({"schemaVersion": 1, "buckets": data["buckets"]})
    print(t("imported"))


def home_command(app_id: str) -> None:
    app = find_app(app_id)
    homepage = app.get("homepage")
    if not homepage:
        raise DebupError(t("homepage_missing"))
    print(homepage)


def hold_command(app_id: str, held: bool) -> None:
    app = find_app(app_id)
    set_hold(app_id, held, app)
    print(t("held" if held else "unheld", app_id=app_id))


def depends_command(app_id: str, package: str | None = None) -> None:
    pkg = package or find_app(app_id)["package"]
    get_package_manager().depends(pkg)


def cleanup_command(yes: bool = False) -> None:
    size = cache.downloads_size()
    print(t("cleanup_plan", size=cache.human_size(size)))
    if not confirm(t("continue"), yes=yes):
        print(t("cancelled"))
        return
    cache.clean_downloads()
    print(t("done"))


def create_command(app_id: str, path: Path, name: str | None, package: str | None, url: str | None, version: str | None) -> None:
    manifest = {
        "schemaVersion": 1,
        "id": app_id,
        "name": name or app_id,
        "description": "",
        "package": package or app_id,
        "arch": "amd64",
        "homepage": "",
        "source": {
            "type": "fixed-url",
            "url": url or "https://example.com/app_1.0.0_amd64.deb",
            "version": version or "1.0.0",
        },
        "install": {"type": "deb"},
    }
    write_json(path, manifest)
    print(path)


def which_command(name: str) -> None:
    found = shutil.which(name)
    if not found:
        raise DebupError(t("which_not_found", name=name))
    print(found)
