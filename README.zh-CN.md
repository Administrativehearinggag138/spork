# Spork

Spork 是一个受 Scoop 启发的 Linux 第三方包管理工具，重点面向 apt/dpkg 系统的 DEB 软件包发现、下载和安装流程。

它借鉴了 Scoop 这个 Windows 包管理器的 bucket 和 manifest 工作流，但不会替代 Linux 发行版自己的包管理器。

关键词：Linux package manager、DEB package manager、Debian package manager、Ubuntu package manager、apt package manager、dpkg、Scoop-style package manager、bucket manifest package manager。

```text
Spork 负责发现软件，系统包管理器负责安装软件。
```

[English](README.md)

## 项目状态

Spork 是一个开源项目，目前仍处于早期开发阶段。当前命令已经可以用于本地测试和实验，但 manifest、bucket 和包管理器适配器仍可能继续调整。

## 项目目标

Linux 已经有成熟的包管理器，Spork 不打算重新实现一套安装系统。

Spork 只做一个轻量的第三方软件发现层：

- bucket 描述系统仓库之外的软件来源。
- manifest 描述软件包、版本、主页、下载地址等元数据。
- 安装、升级、删除、依赖解析和系统状态仍交给系统包管理器处理。

这个边界让 Spork 保持简单，也更符合 Linux 的软件管理方式。

## 功能

- 类 Scoop 的 bucket 和 app manifest。
- 从 bucket 构建本地应用索引。
- 通过系统包管理器适配器执行安装、升级、删除、清理和自动删除。
- 支持只下载软件包，不安装。
- 支持搜索、查看信息、查看主页、查看 manifest、查看依赖。
- 支持按安装时检测到的 CPU 架构过滤 bucket 中的不同构建。
- 支持英文和中文输出。
- 用户级安装，默认目录为 `~/.spork`。

## 支持的包管理器

当前支持的适配器名称：

- `apt`
- `apt-get`
- `dnf`
- `yum`
- `zypper`
- `pacman`

Debian 和 Ubuntu 环境会保留 `apt install --simulate` 预检查行为。

## 安装

```bash
curl -fsSL https://raw.githubusercontent.com/Enkialon/spork/main/scripts/install.sh | sh
spork checkup
spork update
```

安装器是用户级的，会初始化以下目录：

```text
~/.spork/
  apps/
    spork/
      current/        # Spork 源码 checkout
  shims/
    spork -> ~/.spork/apps/spork/current/scripts/spork
  config/
    config.json
    buckets.json
    trusted-buckets.json
  buckets/
    main/             # 默认 bucket checkout
  cache/
    index/
    downloads/
  state/
    installed.json

~/.local/bin/
  spork -> ~/.spork/apps/spork/current/scripts/spork
```

安装器会在可用时创建用户级命令链接 `~/.local/bin/spork`，并更新常见 shell profile，让新的 SSH 终端可以在任意目录直接运行 `spork`。

安装器会检查 `python3`、`git`、`sudo` 以及当前包管理器所需的基础命令。它会根据 `/etc/os-release` 和系统可用命令检测包管理器，并把结果写入 `config.json` 的 `packageManager` 字段。

默认情况下，安装器会从网络下载 Spork 源码：

```text
https://github.com/Enkialon/spork.git
```

如果要安装自己的 fork 或指定分支/tag：

```bash
curl -fsSL https://raw.githubusercontent.com/Enkialon/spork/main/scripts/install.sh \
  | SPORK_REPO_URL=https://github.com/<owner>/spork.git SPORK_REF=<branch-or-tag> sh
```

安装器也会添加默认 bucket：

```text
main -> https://github.com/Enkialon/spork-bucket.git
```

如果要在安装时换成自己的 bucket：

```bash
curl -fsSL https://raw.githubusercontent.com/Enkialon/spork/main/scripts/install.sh \
  | SPORK_DEFAULT_BUCKET_NAME=main SPORK_DEFAULT_BUCKET_URL=https://github.com/<owner>/<bucket>.git sh
```

## 快速开始

先做一次不会安装软件的本地环境检查：

```bash
./scripts/spork checkup
```

安装后可以直接使用：

```bash
spork checkup
spork update
spork search <query>
spork info <app-id>
```

## 常用命令

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

`spork update` 会先用 `git pull --ff-only` 更新 Spork 自身，再更新 git bucket，最后从 `bucket/*.json` 重建本地应用索引。它不会执行 bucket 里的脚本。可以使用 `--no-self-update` 或 `--no-bucket-update` 跳过对应阶段。

## Bucket 结构

Spork bucket 采用接近 Scoop 的约定，把应用 manifest 放在 `bucket/` 目录：

```text
bucket/
  code.json
  gh.json
bucket.json
```

每个 `bucket/*.json` 都是 Spork 可以直接消费的元数据。仓库里的自动化可以更新这些文件，但客户端只会在拉取 bucket 后读取 JSON。

单架构条目可以继续使用顶层的 `arch`、`url` 和 `sha256` 字段。多架构条目可以使用 `architectures`，`spork update` 会按安装时检测到的 CPU 架构选择对应构建，不支持该架构的应用会被跳过。常见别名会规范化成 Debian 风格名称，例如 `amd64`、`arm64`、`mips64el`、`loongarch64`：

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

## 配置

查看或修改包管理器：

```bash
spork config get packageManager
spork config set packageManager apt
spork config set packageManager dnf
spork config set packageManager zypper
spork config set packageManager pacman
```

选择输出语言：

```bash
spork --lang en checkup
spork config set language zh
spork config set language en
spork config set language auto
```

临时环境变量覆盖：

```bash
SPORK_LANG=en spork checkup
SPORK_LANGUAGE=zh spork list
SPORK_DOWNLOAD_TIMEOUT_SECONDS=30 spork download <app-id>
SPORK_PACKAGE_MANAGER=dnf spork checkup
SPORK_HOME=/tmp/spork-dev spork checkup
```

## 源码结构

Spork 使用 Python 项目常见的 `src/` 布局：

```text
src/spork/
  package_managers/
    apt.py
    dnf.py
    pacman.py
    zypper.py
```

新增包管理器适配器时，把实现放到 `src/spork/package_managers/`，再在 `src/spork/package_managers/__init__.py` 注册。

## Spork 不做什么

Spork 不会把被管理的软件安装到 `~/.spork`。这个目录只保存 bucket、元数据、状态和下载缓存。真正的软件安装和删除仍然交给配置的系统包管理器。

## 卸载

```bash
./scripts/uninstall.sh
./scripts/uninstall.sh --keep-data
```

## 贡献

Spork 是开源项目，欢迎实用、清晰、可测试的贡献：

- 改进包管理器适配器。
- 改进 bucket 自动化。
- 改进 bucket 和 manifest 校验。
- 编写或维护公开 bucket。
- 改进文档。

请保持项目边界清晰：Spork 负责发现和描述软件，系统包管理器负责安装。

## 致谢

Spork 深受 Scoop 启发。Scoop 简单直接的 bucket 模型、可读的 manifest 和实用的命令行体验，对这个项目影响很大。

向 Scoop 项目和所有贡献者致敬。
