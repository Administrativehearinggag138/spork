import os
from pathlib import Path

from .common import has_command


def _os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"')
    return data


def detect_package_manager() -> str:
    forced = os.environ.get("SPORK_PACKAGE_MANAGER")
    if forced:
        return normalize_package_manager(forced)

    release = _os_release()
    distro = " ".join((release.get("ID", ""), release.get("ID_LIKE", ""))).lower()
    candidates: list[str] = []
    if any(name in distro for name in ("debian", "ubuntu", "linuxmint", "pop")):
        candidates.extend(["apt", "apt-get"])
    if any(name in distro for name in ("fedora", "rhel", "centos", "rocky", "almalinux")):
        candidates.extend(["dnf", "yum"])
    if any(name in distro for name in ("suse", "opensuse")):
        candidates.append("zypper")
    if any(name in distro for name in ("arch", "manjaro")):
        candidates.append("pacman")
    candidates.extend(["apt", "dnf", "yum", "zypper", "pacman"])
    for candidate in candidates:
        if has_command(candidate):
            return candidate
    return "apt"


def normalize_package_manager(name: str) -> str:
    normalized = name.strip().lower()
    aliases = {
        "aptitude": "apt",
        "debian": "apt",
        "ubuntu": "apt",
        "fedora": "dnf",
        "rhel": "dnf",
        "centos": "yum",
        "opensuse": "zypper",
        "suse": "zypper",
        "arch": "pacman",
    }
    return aliases.get(normalized, normalized)


def configured_package_manager() -> str:
    from ..config import load_config

    config = load_config()
    return normalize_package_manager(str(config.get("packageManager") or detect_package_manager()))
