from ..errors import AptError
from .apt import AptPackageManager
from .common import PackageManager
from .detection import configured_package_manager, detect_package_manager, normalize_package_manager
from .dnf import DnfPackageManager
from .pacman import PacmanPackageManager
from .zypper import ZypperPackageManager


def get_package_manager(name: str | None = None) -> PackageManager:
    selected = normalize_package_manager(name or configured_package_manager())
    if selected in {"apt", "apt-get"}:
        return AptPackageManager(selected)
    if selected in {"dnf", "yum"}:
        return DnfPackageManager(selected)
    if selected == "zypper":
        return ZypperPackageManager()
    if selected == "pacman":
        return PacmanPackageManager()
    raise AptError(f"不支持的包管理器：{selected}")


__all__ = [
    "AptPackageManager",
    "DnfPackageManager",
    "PackageManager",
    "PacmanPackageManager",
    "ZypperPackageManager",
    "configured_package_manager",
    "detect_package_manager",
    "get_package_manager",
    "normalize_package_manager",
]
