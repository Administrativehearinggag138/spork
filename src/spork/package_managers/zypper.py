from pathlib import Path

from ..errors import AptError
from .common import run_command
from .dnf import DnfPackageManager


class ZypperPackageManager(DnfPackageManager):
    def __init__(self) -> None:
        super().__init__("zypper")

    def install_file(self, path: Path) -> None:
        run_command(["sudo", "zypper", "install", str(path)], "zypper 安装失败，请检查上方 zypper 输出。")

    def remove_package(self, package: str) -> None:
        run_command(["sudo", "zypper", "remove", package], "zypper 卸载失败，请检查上方 zypper 输出。")

    def autoremove_plan(self) -> str:
        return "zypper autoremove is not automated by Spork"

    def autoremove(self) -> None:
        raise AptError("zypper 适配器暂不支持 autoremove。")

    def depends(self, package: str) -> None:
        run_command(["zypper", "info", "--requires", package], "zypper depends 执行失败。")
