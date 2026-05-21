from spork.arch import normalize_arch, select_architecture


def selected_source(manifest: dict) -> tuple[dict, str]:
    target_arch = normalize_arch(manifest.get("arch"))
    source = manifest["source"]
    if not source.get("architectures"):
        return source, target_arch
    selected = select_architecture(source, target_arch)
    if selected is None:
        raise ValueError(f"no {target_arch} source for {manifest['id']}")
    return selected
