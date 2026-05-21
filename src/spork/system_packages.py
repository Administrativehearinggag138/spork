from pathlib import Path

from .package_managers import get_package_manager


def install_plan(path: Path) -> list[str]:
    return get_package_manager().install_plan(path)


def remove_plan(package: str, purge: bool = False) -> str:
    return get_package_manager().remove_plan(package, purge=purge)


def autoremove_plan() -> str:
    return get_package_manager().autoremove_plan()


def preinstall_file(path: Path) -> None:
    get_package_manager().preinstall_file(path)


def install_file(path: Path) -> None:
    get_package_manager().install_file(path)


def remove_package(package: str) -> None:
    get_package_manager().remove_package(package)


def purge_package(package: str) -> None:
    get_package_manager().purge_package(package)


def autoremove() -> None:
    get_package_manager().autoremove()
