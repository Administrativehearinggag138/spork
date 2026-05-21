import json
import re
import urllib.request

from spork.config import now_iso


def _base_app(manifest: dict, version: str, url: str) -> dict:
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


def resolve(manifest: dict) -> dict:
    source = manifest["source"]
    repo = source["repo"]
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "spork"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        release = json.load(response)
    tag = release.get("tag_name") or ""
    version_regex = source.get("versionRegex", "^v?(.*)$")
    match = re.search(version_regex, tag)
    version = match.group(1) if match and match.groups() else tag.lstrip("v")
    asset_pattern = re.compile(source["assetPattern"])
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if asset_pattern.search(name):
            return _base_app(manifest, version, asset["browser_download_url"])
    raise ValueError(f"no matching release asset for {manifest['id']}")
