from pathlib import Path

from ..errors import AptError
from .common import PackageManager, capture_command, run_command


class PacmanPackageManager(PackageManager):
    def __init__(self) -> None:
        super().__init__("pacman", "pacman", "pacman", "pacman")

    def install_plan(self, path: Path) -> list[str]:
        return [f"sudo pacman -U {path}"]

    def remove_plan(self, package: str, purge: bool = False) -> str:
        return f"sudo pacman {'-Rns' if purge else '-R'} {package}"

    def autoremove_plan(self) -> str:
        return "pacman orphan cleanup is not automated by Spork"

    def install_file(self, path: Path) -> None:
        run_command(["sudo", "pacman", "-U", str(path)], "pacman 安装失败，请检查上方 pacman 输出。")

    def remove_package(self, package: str) -> None:
        run_command(["sudo", "pacman", "-R", package], "pacman 卸载失败，请检查上方 pacman 输出。")

    def purge_package(self, package: str) -> None:
        run_command(["sudo", "pacman", "-Rns", package], "pacman purge 失败，请检查上方 pacman 输出。")

    def autoremove(self) -> None:
        raise AptError("pacman 适配器暂不支持自动清理孤儿包。")

    def installed_version(self, package: str) -> str | None:
        result = capture_command(["pacman", "-Q", package])
        if result.returncode != 0:
            return None
        parts = result.stdout.strip().split(maxsplit=1)
        return parts[1] if len(parts) == 2 else None

    def depends(self, package: str) -> None:
        run_command(["pacman", "-Si", package], "pacman depends 执行失败。")
