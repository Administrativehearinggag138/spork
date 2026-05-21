from .fixed_url import resolve as resolve_fixed_url
from .github_release import resolve as resolve_github_release
from .html_regex import resolve as resolve_html_regex


def resolve_manifest(manifest: dict) -> dict:
    source = manifest.get("source") or {}
    source_type = source.get("type")
    if source_type == "github-release":
        return resolve_github_release(manifest)
    if source_type == "fixed-url":
        return resolve_fixed_url(manifest)
    if source_type == "html-regex":
        return resolve_html_regex(manifest)
    raise ValueError(f"unsupported provider: {source_type}")
