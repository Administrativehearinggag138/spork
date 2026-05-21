from . import dpkg, system_packages
from .errors import AppNotFoundError, IndexError
from .index import find_app
from .output import confirm
from .state import get_installed, remove_installed


def resolve_app_or_state(app_id: str, package: str | None = None) -> dict:
    if package:
        return {"id": app_id, "package": package, "name": app_id}
    try:
        return find_app(app_id)
    except (AppNotFoundError, IndexError):
        state_app = get_installed(app_id)
        if state_app:
            return state_app
        raise AppNotFoundError(f"未找到 {app_id}，可使用 --package 指定 Debian 包名。")


def remove(app_id: str, yes: bool = False, package: str | None = None, purge: bool = False) -> bool:
    app = resolve_app_or_state(app_id, package=package)
    pkg = app["package"]
    installed = dpkg.installed_version(pkg)
    if not installed:
        print(f"未安装：{pkg}")
        return False
    title = "即将彻底清理" if purge else "即将卸载"
    print(f"{title}：\n")
    print(f"  应用：{app.get('name', app_id)}")
    print(f"  ID：{app_id}")
    print(f"  包名：{pkg}")
    print(f"  当前版本：{installed}")
    if purge:
        print("\n警告：purge 会尝试删除软件包及系统级配置文件。")
    print(f"\n卸载阶段将调用：\n  {system_packages.remove_plan(pkg, purge=purge)}")
    if not confirm("继续吗？", yes=yes):
        print("已取消。")
        return False
    if purge:
        system_packages.purge_package(pkg)
    else:
        system_packages.remove_package(pkg)
    remove_installed(app_id)
    print(f"完成：{app_id}")
    return True


def autoremove(yes: bool = False) -> None:
    print(f"即将调用：\n  {system_packages.autoremove_plan()}")
    if not confirm("继续吗？", yes=yes):
        print("已取消。")
        return
    system_packages.autoremove()
