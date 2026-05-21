import subprocess
from pathlib import Path

from .errors import DebupError
from .output import warn


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_toplevel(root: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise DebupError("git 不可用，请先安装 git。") from exc
    except subprocess.CalledProcessError:
        return None
    return Path(result.stdout.strip()).resolve()


def update_self() -> Path | None:
    root = project_root()
    git_root = _git_toplevel(root)
    if git_root is None:
        warn(f"Spork 当前目录不是 git 工作树，已跳过自身更新：{root}")
        return None

    print(f"更新 Spork 自身：{git_root}")
    try:
        subprocess.run(["git", "-C", str(git_root), "pull", "--ff-only"], check=True)
    except subprocess.CalledProcessError as exc:
        raise DebupError("Spork 自身更新失败：git pull --ff-only 执行失败。") from exc
    return git_root
