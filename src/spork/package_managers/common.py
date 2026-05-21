import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..errors import AptError, DpkgError


def run_command(args: list[str], failure_message: str) -> None:
    try:
        subprocess.run(args, check=True)
    except FileNotFoundError as exc:
        raise AptError(f"命令不可用：{args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise AptError(failure_message) from exc


def capture_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def has_command(command: str) -> bool:
    return shutil.which(command) is not None


@dataclass(frozen=True)
class PackageManager:
    name: str
    package_query: str | None
    install_command: str
    dependency_command: str | None = None

    def required_commands(self) -> list[str]:
        commands = [self.install_command, "sudo"]
        if self.package_query:
            commands.append(self.package_query)
        if self.dependency_command:
            commands.append(self.dependency_command)
        return list(dict.fromkeys(commands))

    def missing_commands(self) -> list[str]:
        return [command for command in self.required_commands() if not has_command(command)]

    def install_plan(self, path: Path) -> list[str]:
        return [f"sudo {self.install_command} install {path}"]

    def remove_plan(self, package: str, purge: bool = False) -> str:
        op = "purge" if purge else "remove"
        return f"sudo {self.install_command} {op} {package}"

    def autoremove_plan(self) -> str:
        return f"sudo {self.install_command} autoremove"

    def preinstall_file(self, path: Path) -> None:
        return None

    def install_file(self, path: Path) -> None:
        run_command(["sudo", self.install_command, "install", str(path)], "安装失败，请检查上方包管理器输出。")

    def remove_package(self, package: str) -> None:
        run_command(["sudo", self.install_command, "remove", package], "卸载失败，请检查上方包管理器输出。")

    def purge_package(self, package: str) -> None:
        self.remove_package(package)

    def autoremove(self) -> None:
        run_command(["sudo", self.install_command, "autoremove"], "自动清理失败，请检查上方包管理器输出。")

    def installed_version(self, package: str) -> str | None:
        raise DpkgError(f"{self.name} 适配器暂不支持查询已安装版本。")

    def compare_versions(self, left: str, op: str, right: str) -> bool:
        if op != "lt":
            raise DpkgError(f"{self.name} 适配器暂不支持版本比较操作：{op}")
        return left < right

    def depends(self, package: str) -> None:
        raise AptError(f"{self.name} 适配器暂不支持 depends。")
