import platform
from typing import Any


ARCH_ALIASES = {
    "x86_64": "amd64",
    "x64": "amd64",
    "amd64": "amd64",
    "i386": "i386",
    "i686": "i386",
    "x86": "i386",
    "aarch64": "arm64",
    "arm64": "arm64",
    "armv7l": "armhf",
    "armv7": "armhf",
    "armhf": "armhf",
    "armel": "armel",
    "riscv64": "riscv64",
    "ppc64le": "ppc64el",
    "ppc64el": "ppc64el",
    "s390x": "s390x",
    "all": "all",
    "any": "all",
    "noarch": "all",
}


def normalize_arch(value: str | None) -> str:
    if not value:
        return detect_arch()
    return ARCH_ALIASES.get(value.strip().lower(), value.strip().lower())


def detect_arch() -> str:
    return ARCH_ALIASES.get(platform.machine().lower(), platform.machine().lower())


def architecture_map(data: dict[str, Any]) -> dict[str, Any] | None:
    variants = data.get("architectures")
    if isinstance(variants, dict):
        return variants
    return None


def select_architecture(data: dict[str, Any], target_arch: str) -> tuple[dict[str, Any], str] | None:
    target = normalize_arch(target_arch)
    variants = architecture_map(data)
    if not variants:
        arch_value = data.get("arch")
        if isinstance(arch_value, list):
            supported = [normalize_arch(str(item)) for item in arch_value]
            if target not in supported and "all" not in supported:
                return None
            selected_data = data.copy()
            selected_data["arch"] = target if target in supported else "all"
            return selected_data, selected_data["arch"]
        if arch_value:
            selected = normalize_arch(str(arch_value))
            return (data.copy(), selected) if selected in {target, "all"} else None
        selected_data = data.copy()
        selected_data["arch"] = target
        return selected_data, target

    selected_key = None
    for candidate in (target, "all", "any", "noarch"):
        if candidate in variants:
            selected_key = candidate
            break
    if selected_key is None:
        return None

    selected_arch = normalize_arch(selected_key)
    selected_data = {key: value for key, value in data.items() if key != "architectures"}
    variant = variants[selected_key]
    if isinstance(variant, str):
        selected_data["url"] = variant
    elif isinstance(variant, dict):
        selected_data.update(variant)
    else:
        return None
    selected_data["arch"] = normalize_arch(str(selected_data.get("arch") or selected_arch))
    return selected_data, selected_data["arch"]
