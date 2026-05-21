import shutil
from pathlib import Path

from . import paths


def _size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())


def downloads_size() -> int:
    return _size(paths.downloads_dir())


def clean_downloads() -> int:
    size = downloads_size()
    if paths.downloads_dir().exists():
        shutil.rmtree(paths.downloads_dir())
    paths.downloads_dir().mkdir(parents=True, exist_ok=True)
    return size


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GiB"
