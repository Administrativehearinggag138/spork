import platform
import shutil
import sys

from . import paths
from .bucket import list_buckets
from .package_managers import get_package_manager


def _ok(value: bool) -> str:
    return "OK" if value else "FAIL"


def run_doctor() -> list[dict[str, str]]:
    paths.ensure_dirs()
    checks: list[dict[str, str]] = []
    checks.append({"item": "system", "status": "OK", "detail": platform.system()})
    arch = platform.machine()
    checks.append({"item": "arch amd64", "status": _ok(arch in {"x86_64", "amd64"}), "detail": arch})
    checks.append({"item": "python", "status": "OK", "detail": sys.version.split()[0]})
    manager = get_package_manager()
    checks.append({"item": "package manager", "status": "OK", "detail": manager.name})
    for command in ["git", *manager.required_commands()]:
        checks.append({"item": command, "status": _ok(shutil.which(command) is not None), "detail": shutil.which(command) or ""})
    for name, path in (
        ("config dir writable", paths.config_dir()),
        ("share dir writable", paths.data_dir()),
        ("cache dir writable", paths.cache_dir()),
    ):
        checks.append({"item": name, "status": _ok(path.exists() and path.is_dir()), "detail": str(path)})
    checks.append({"item": "buckets", "status": "OK", "detail": str(len(list_buckets()))})
    checks.append({"item": "merged index", "status": _ok(paths.merged_index_file().exists()), "detail": str(paths.merged_index_file())})
    return checks
