import hashlib
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

from . import paths
from .errors import DownloadError


def filename_from_url(url: str, app_id: str) -> str:
    parsed = urllib.parse.urlparse(url)
    name = Path(urllib.parse.unquote(parsed.path)).name
    return name or f"{app_id}.deb"


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(app: dict, timeout: int) -> Path:
    target_dir = paths.downloads_dir() / app["id"]
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename_from_url(app["url"], app["id"])
    try:
        with urllib.request.urlopen(app["url"], timeout=timeout) as response:
            with target.open("wb") as handle:
                shutil.copyfileobj(response, handle)
    except Exception as exc:
        raise DownloadError(f"下载失败：{app['url']}") from exc
    expected = app.get("sha256")
    if expected:
        actual = sha256sum(target)
        if actual.lower() != expected.lower():
            raise DownloadError(
                "sha256 校验失败，已拒绝安装：\n\n"
                f"  文件：{target}\n  期望：{expected}\n  实际：{actual}"
            )
    return target
