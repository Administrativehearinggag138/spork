import subprocess

from .package_managers import get_package_manager


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def is_installed(package: str) -> bool:
    return installed_version(package) is not None


def installed_version(package: str) -> str | None:
    return get_package_manager().installed_version(package)


def compare_versions(left: str, op: str, right: str) -> bool:
    return get_package_manager().compare_versions(left, op, right)


def deb_field(deb_path: str, field: str) -> str | None:
    result = _run(["dpkg-deb", "-f", deb_path, field])
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None
