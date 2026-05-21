import tempfile
import urllib.request
from pathlib import Path

from spork import dpkg
from spork.config import now_iso


def resolve(manifest: dict) -> dict:
    source = manifest["source"]
    url = source["url"]
    version = source.get("version")
    if not version and source.get("versionStrategy") == "dpkg-deb-control":
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "app.deb"
            with urllib.request.urlopen(url, timeout=120) as response:
                target.write_bytes(response.read())
            version = dpkg.deb_field(str(target), "Version")
    if not version:
        version = "unknown"
    return {
        "schemaVersion": 1,
        "id": manifest["id"],
        "name": manifest["name"],
        "description": manifest.get("description"),
        "package": manifest["package"],
        "version": version,
        "arch": manifest.get("arch", "amd64"),
        "url": url,
        "sha256": manifest.get("sha256"),
        "homepage": manifest.get("homepage"),
        "updatedAt": now_iso(),
    }
