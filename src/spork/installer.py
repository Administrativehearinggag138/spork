from typing import Iterable
from pathlib import Path

from . import dpkg, system_packages
from .config import load_config
from .downloader import download
from .errors import AppNotFoundError
from .index import all_apps, find_app
from .output import confirm, warn
from .i18n import t
from .state import is_held, upsert_installed


def show_install_plan(app: dict, action: str) -> None:
    title = "即将升级" if action == "upgrade" else "即将安装"
    print(f"{title}：\n")
    print(f"  应用：{app.get('name')}")
    print(f"  ID：{app.get('id')}")
    print(f"  包名：{app.get('package')}")
    print(f"  版本：{app.get('version')}")
    print(f"  来源：{app.get('bucket')}")
    print(f"  地址：{app.get('url')}")
    print(f"  sha256：{app.get('sha256') or '<未提供>'}")
    print("\n安装阶段将调用：")
    for line in system_packages.install_plan(Path(f"./{app.get('id')}.deb")):
        print(f"  {line}")


def install(app_id: str, yes: bool = False) -> None:
    app = find_app(app_id)
    installed = dpkg.installed_version(app["package"])
    if installed:
        if not dpkg.compare_versions(installed, "lt", app["version"]):
            print(f"已安装 {app_id}，当前版本 {installed} 不低于索引版本 {app['version']}。")
            return
        print(f"已安装旧版本 {installed}，可执行 spork upgrade {app_id}。")
        return
    show_install_plan(app, "install")
    if not app.get("sha256"):
        warn("该软件源未提供 sha256。")
    if not confirm("继续安装吗？", yes=yes):
        print("已取消。")
        return
    config = load_config()
    deb_path = download(app, int(config.get("downloadTimeoutSeconds", 120)))
    system_packages.install_file(deb_path)
    actual = dpkg.installed_version(app["package"]) or app["version"]
    upsert_installed(app, "install", actual)
    print(f"安装完成：{app_id} {actual}")


def _upgrade_candidates(apps: Iterable[dict]) -> list[tuple[dict, str]]:
    candidates: list[tuple[dict, str]] = []
    for app in apps:
        if is_held(app["id"]):
            print(t("skip_held", app_id=app["id"]))
            continue
        installed = dpkg.installed_version(app["package"])
        if installed and dpkg.compare_versions(installed, "lt", app["version"]):
            candidates.append((app, installed))
    return candidates


def upgrade(app_id: str | None = None, yes: bool = False, stop_on_error: bool = False) -> None:
    apps = [find_app(app_id)] if app_id else all_apps()
    candidates = _upgrade_candidates(apps)
    if not candidates:
        print("没有可升级软件。")
        return
    print(f"发现 {len(candidates)} 个可升级软件：")
    for app, installed in candidates:
        print(f"  {app['id']}: {installed} -> {app['version']}")
    if not confirm("继续升级吗？", yes=yes):
        print("已取消。")
        return
    config = load_config()
    for app, _installed in candidates:
        try:
            deb_path = download(app, int(config.get("downloadTimeoutSeconds", 120)))
            system_packages.install_file(deb_path)
            actual = dpkg.installed_version(app["package"]) or app["version"]
            upsert_installed(app, "upgrade", actual)
            print(f"升级完成：{app['id']} {actual}")
        except Exception:
            if stop_on_error:
                raise
            print(f"错误：升级失败：{app['id']}")


def check() -> list[dict]:
    updates: list[dict] = []
    for app in all_apps():
        installed = dpkg.installed_version(app["package"])
        if installed and dpkg.compare_versions(installed, "lt", app["version"]):
            updates.append(
                {
                    "id": app["id"],
                    "package": app["package"],
                    "installed": installed,
                    "latest": app["version"],
                    "bucket": app.get("bucket"),
                }
            )
    return updates
