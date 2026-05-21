from pathlib import Path
from typing import Any

from .arch import detect_arch, normalize_arch
from .config import load_config, now_iso, save_config, write_json
from .downloader import download
from .errors import DebupError
from .i18n import t
from .index import find_app
from .output import print_json
from .package_managers import get_package_manager


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
        if args.key == "arch":
            raise DebupError("arch 是安装时检测到的 CPU 架构，不支持通过 config set 修改。")
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


def home_command(app_id: str) -> None:
    app = find_app(app_id)
    homepage = app.get("homepage")
    if not homepage:
        raise DebupError(t("homepage_missing"))
    print(homepage)


def depends_command(app_id: str, package: str | None = None) -> None:
    pkg = package or find_app(app_id)["package"]
    get_package_manager().depends(pkg)


def create_command(app_id: str, path: Path, name: str | None, package: str | None, url: str | None, version: str | None, arch: str | None = None) -> None:
    arch = normalize_arch(arch or detect_arch())
    version = version or "1.0.0"
    manifest = {
        "schemaVersion": 1,
        "id": app_id,
        "name": name or app_id,
        "description": "",
        "package": package or app_id,
        "version": version,
        "arch": arch,
        "url": url or f"https://example.com/app_{version}_{arch}.deb",
        "sha256": None,
        "homepage": "",
        "updatedAt": now_iso(),
    }
    write_json(path, manifest)
    print(path)
