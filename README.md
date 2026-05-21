# Spork

Spork is a Scoop-style third-party package manager for Linux, focused on DEB package discovery, download, and install workflows for apt/dpkg-based systems.

It borrows the bucket-and-manifest workflow from [Scoop](https://scoop.sh/), the Windows package manager, but keeps Linux package installation in the hands of the system package manager.

Keywords: Linux package manager, DEB package manager, Debian package manager, Ubuntu package manager, apt package manager, dpkg, Scoop-style package manager, bucket manifest package manager.

```text
Spork finds packages. Your system package manager installs packages.
```

[中文文档](README.zh-CN.md)

## Status

Spork is an open source project in early development. The command surface is usable for local testing and experimentation, but manifests, buckets, and package-manager adapters should still be treated as evolving interfaces.

## Why Spork Exists

Linux already has mature package managers. Spork does not try to replace them.

Instead, Spork provides a lightweight third-party discovery layer:

- Buckets describe software entries outside the system repository.
- Manifests point to package files, metadata, homepages, and versions.
- The configured package manager handles install, update, uninstall, dependency resolution, and system state.

This keeps Spork small and makes the boundary explicit.

## Features

- Scoop-style buckets and app manifests.
- Local app index built from configured buckets.
- Install, update, uninstall, purge, and autoremove through a system package manager adapter.
- Download-only mode for package files.
- App search, info, homepage, manifest display, and dependency inspection.
- CPU architecture filtering for buckets that publish multiple builds.
- English and Chinese output selection.
- User-scoped installation under `~/.spork`.

## Supported Package Managers

Spork currently supports these adapter names:

- `apt`
- `apt-get`
- `dnf`
- `yum`
- `zypper`
- `pacman`

Debian and Ubuntu installs keep the existing `apt install --simulate` preflight behavior.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/Enkialon/spork/main/scripts/install.sh | sh
spork checkup
spork update
```

The installer is user-scoped. It initializes this layout:

```text
~/.spork/
  apps/
    spork/
      current/        # Spork source checkout
  shims/
    spork -> ~/.spork/apps/spork/current/scripts/spork
  config/
    config.json
    buckets.json
    trusted-buckets.json
  buckets/
    main/             # default bucket checkout
  cache/
    index/
    downloads/
  state/
    installed.json

~/.local/bin/
  spork -> ~/.spork/apps/spork/current/scripts/spork
```

The installer creates a user command link at `~/.local/bin/spork` when that path is available, and updates common shell profiles so new SSH shells can find `spork` from any directory.

The installer checks for the base commands Spork needs, including `python3`, `git`, `sudo`, and the command set required by the detected package manager. It detects the package manager from `/etc/os-release` and available commands, then writes it to `config.json` as `packageManager`.

By default, the installer downloads Spork from the network:

```text
https://github.com/Enkialon/spork.git
```

Override the source repository or checkout ref if you maintain a fork:

```bash
curl -fsSL https://raw.githubusercontent.com/Enkialon/spork/main/scripts/install.sh \
  | SPORK_REPO_URL=https://github.com/<owner>/spork.git SPORK_REF=<branch-or-tag> sh
```

The installer also adds the default bucket:

```text
main -> https://github.com/Enkialon/spork-bucket.git
```

Override it during installation if you maintain your own bucket:

```bash
curl -fsSL https://raw.githubusercontent.com/Enkialon/spork/main/scripts/install.sh \
  | SPORK_DEFAULT_BUCKET_NAME=main SPORK_DEFAULT_BUCKET_URL=https://github.com/<owner>/<bucket>.git sh
```

## Quick Start

Run a local environment check without installing anything:

```bash
./scripts/spork checkup
```

After installing:

```bash
spork checkup
spork update
spork search <query>
spork info <app-id>
```

## Common Commands

```bash
spork bucket list
spork bucket add extras <bucket-url>
spork bucket rm extras
spork bucket update
spork update

spork list
spork list --available
spork search <query>
spork info <app-id>
spork cat <app-id>
spork home <app-id>
spork depends <app-id>

spork download <app-id>
spork install <app-id>
spork update <app-id>
spork status
spork uninstall <app-id>
spork purge <app-id>
spork autoremove
spork cache clean
spork checkup
spork create my-app ./bucket/my-app.json --url https://example.com/my-app.deb
```

`spork update` updates Spork itself with `git pull --ff-only`, updates git buckets, then rebuilds the local app index from `bucket/*.json`. It does not execute bucket scripts. Use `--no-self-update` or `--no-bucket-update` to skip either phase.

## Bucket Layout

Spork buckets follow the Scoop convention of storing app manifests under `bucket/`:

```text
bucket/
  code.json
  gh.json
bucket.json
```

Each `bucket/*.json` file is directly consumable metadata. Automation may update these files in the bucket repository, but clients only read JSON after pulling the bucket.

Single-architecture entries can use top-level `arch`, `url`, and `sha256` fields. Multi-architecture entries can use `architectures`; Spork uses the CPU architecture detected during installation and skips unsupported apps. Common aliases are normalized to Debian-style names such as `amd64`, `arm64`, `mips64el`, and `loongarch64`:

```json
{
  "schemaVersion": 1,
  "id": "my-app",
  "name": "My App",
  "package": "my-app",
  "version": "1.0.0",
  "homepage": "https://example.com",
  "updatedAt": "2026-05-21T00:00:00Z",
  "architectures": {
    "amd64": {
      "url": "https://example.com/my-app_1.0.0_amd64.deb",
      "sha256": "..."
    },
    "arm64": {
      "url": "https://example.com/my-app_1.0.0_arm64.deb",
      "sha256": "..."
    }
  }
}
```

## Configuration

Inspect or change the configured package manager:

```bash
spork config get packageManager
spork config set packageManager apt
spork config set packageManager dnf
spork config set packageManager zypper
spork config set packageManager pacman
```

Select output language:

```bash
spork --lang en checkup
spork config set language zh
spork config set language en
spork config set language auto
```

Temporary environment overrides:

```bash
SPORK_LANG=en spork checkup
SPORK_LANGUAGE=zh spork list
SPORK_DOWNLOAD_TIMEOUT_SECONDS=30 spork download <app-id>
SPORK_PACKAGE_MANAGER=dnf spork checkup
SPORK_HOME=/tmp/spork-dev spork checkup
```

## Source Layout

Spork uses the standard Python `src/` layout:

```text
src/spork/
  package_managers/
    apt.py
    dnf.py
    pacman.py
    zypper.py
```

New package-manager adapters should be added under `src/spork/package_managers/` and registered in `src/spork/package_managers/__init__.py`.

## What Spork Does Not Do

Spork does not install managed apps under `~/.spork`. It stores buckets, metadata, state, and downloaded package files there. Actual app installation and removal still go through the configured system package manager.

## Uninstall

```bash
./scripts/uninstall.sh
./scripts/uninstall.sh --keep-data
```

## Contributing

Spork is open source and welcomes practical contributions:

- Improve package-manager adapters.
- Improve bucket automation.
- Improve bucket and manifest validation.
- Write or maintain public buckets.
- Improve documentation.

Keep changes small, testable, and aligned with the project boundary: Spork should discover and describe packages, while the system package manager should own installation.

## Acknowledgements

Spork is deeply inspired by Scoop. Scoop's simple bucket model, readable manifests, and practical command-line experience had a strong influence on this project.

Respect and thanks to the Scoop project and its contributors.
