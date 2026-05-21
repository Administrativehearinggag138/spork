import re
import urllib.parse
import urllib.request

from spork.config import now_iso


def resolve(manifest: dict) -> dict:
    source = manifest["source"]
    with urllib.request.urlopen(source["pageUrl"], timeout=60) as response:
        html = response.read().decode("utf-8", errors="replace")
    url_match = re.search(source["urlRegex"], html)
    if not url_match:
        raise ValueError(f"no deb url matched for {manifest['id']}")
    url = url_match.group(1) if url_match.groups() else url_match.group(0)
    url = urllib.parse.urljoin(source["pageUrl"], url)
    version = "unknown"
    version_regex = source.get("versionRegex")
    if version_regex:
        match = re.search(version_regex, url) or re.search(version_regex, html)
        if match:
            version = match.group(1) if match.groups() else match.group(0)
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
