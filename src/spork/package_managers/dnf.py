from pathlib import Path

from ..errors import AptError
from .common import PackageManager, capture_command, run_command


class DnfPackageManager(PackageManager):
    def __init__(self, command: str = "dnf") -> None:
        super().__init__(command, "rpm", command, command)

    def install_plan(self, path: Path) -> list[str]:
        return [f"sudo {self.install_command} install {path}"]

    def remove_plan(self, package: str, purge: bool = False) -> str:
        if purge:
            raise AptError(f"{self.install_command} 适配器暂不支持 purge。")
        return f"sudo {self.install_command} remove {package}"

    def purge_package(self, package: str) -> None:
        raise AptError(f"{self.install_command} 适配器暂不支持 purge。")

    def installed_version(self, package: str) -> str | None:
        result = capture_command(["rpm", "-q", "--qf", "%{VERSION}-%{RELEASE}", package])
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None

    def depends(self, package: str) -> None:
        run_command([self.install_command, "repoquery", "--requires", "--resolve", package], f"{self.install_command} depends 执行失败。")
