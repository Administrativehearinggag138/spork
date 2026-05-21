import argparse
from pathlib import Path
import sys
import traceback

from . import __version__
from . import cache
from .branding import BRAND_NAME, CLI_NAME
from .bucket import add_bucket, list_buckets, remove_bucket, update_bucket
from .commands import (
    cat_command,
    cleanup_command,
    config_command,
    create_command,
    depends_command,
    download_command,
    export_command,
    hold_command,
    home_command,
    import_command,
    unsupported,
    which_command,
)
from .config import ensure_initial_files, load_config
from .doctor import run_doctor
from .errors import DebupError
from .i18n import set_language, t
from .index import all_apps, find_app, search_apps, update_index
from .installer import check, install, upgrade
from .output import confirm, print_json, table
from .remover import autoremove, remove
from .self_update import update_self
from .state import list_installed


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--debug", action="store_true", help="输出 traceback")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--no-color", action="store_true", help="保留参数，当前实现不输出颜色")
    parser.add_argument("--lang", choices=["auto", "zh", "en"], help="输出语言")


def _add_json(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="输出 JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=CLI_NAME, description=f"{BRAND_NAME}: Scoop-style third-party Linux package manager.")
    parser.add_argument("--version", action="version", version=f"{BRAND_NAME} ({CLI_NAME}) {__version__}")
    _add_common(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    bucket = sub.add_parser("bucket", help="管理 bucket")
    bucket_sub = bucket.add_subparsers(dest="bucket_command", required=True)
    bucket_add = bucket_sub.add_parser("add")
    bucket_add.add_argument("name")
    bucket_add.add_argument("source")
    bucket_add.add_argument("-y", "--yes", action="store_true")
    bucket_list = bucket_sub.add_parser("list")
    _add_json(bucket_list)
    bucket_remove = bucket_sub.add_parser("remove")
    bucket_remove.add_argument("name")
    bucket_remove.add_argument("--delete-files", action="store_true")
    bucket_update = bucket_sub.add_parser("update")
    bucket_update.add_argument("name", nargs="?")

    update = sub.add_parser("update", help="更新 Spork、自身 bucket 和本地索引")
    update.add_argument("--no-bucket-update", action="store_true")
    update.add_argument("--no-self-update", action="store_true")

    list_cmd = sub.add_parser("list", help="列出应用")
    list_cmd.add_argument("--installed", action="store_true", help=f"只列出 {BRAND_NAME} 记录的已安装应用")
    _add_json(list_cmd)
    search = sub.add_parser("search", help="搜索应用")
    search.add_argument("keyword")
    _add_json(search)
    info = sub.add_parser("info", help="显示应用信息")
    info.add_argument("app_id")
    _add_json(info)
    check_cmd = sub.add_parser("check", help="检查可升级软件")
    _add_json(check_cmd)
    status_cmd = sub.add_parser("status", help="检查可升级软件")
    _add_json(status_cmd)
    checkup_cmd = sub.add_parser("checkup", help="检查环境")
    _add_json(checkup_cmd)

    config_cmd = sub.add_parser("config", help="读写配置")
    config_sub = config_cmd.add_subparsers(dest="config_command", required=True)
    config_list = config_sub.add_parser("list")
    _add_json(config_list)
    config_get = config_sub.add_parser("get")
    config_get.add_argument("key")
    _add_json(config_get)
    config_set = config_sub.add_parser("set")
    config_set.add_argument("key")
    config_set.add_argument("value")

    cat_cmd = sub.add_parser("cat", help="显示应用索引 JSON")
    cat_cmd.add_argument("app_id")
    download_cmd = sub.add_parser("download", help="下载应用 deb 到缓存，不安装")
    download_cmd.add_argument("app_id")

    export_cmd = sub.add_parser("export", help=f"导出 bucket、配置和 {BRAND_NAME} 管理状态")
    export_cmd.add_argument("path", nargs="?")
    export_cmd.add_argument("--config", action="store_true", help="包含 config.json")
    import_cmd = sub.add_parser("import", help="导入 bucket 和配置，不自动安装应用")
    import_cmd.add_argument("path")
    import_cmd.add_argument("--config", action="store_true", help="导入 config")

    for name, held in (("hold", True), ("unhold", False)):
        hold_parser = sub.add_parser(name, help="锁定或解除应用升级")
        hold_parser.add_argument("app_id")
        hold_parser.set_defaults(held=held)

    home_cmd = sub.add_parser("home", help="显示应用主页")
    home_cmd.add_argument("app_id")
    depends_cmd = sub.add_parser("depends", help="显示包管理器依赖信息")
    depends_cmd.add_argument("app_id")
    depends_cmd.add_argument("--package")
    cleanup_cmd = sub.add_parser("cleanup", help=f"清理 {BRAND_NAME} 下载缓存")
    cleanup_cmd.add_argument("-y", "--yes", action="store_true")
    create_cmd = sub.add_parser("create", help="创建 fixed-url app manifest 模板")
    create_cmd.add_argument("app_id")
    create_cmd.add_argument("path")
    create_cmd.add_argument("--name")
    create_cmd.add_argument("--package")
    create_cmd.add_argument("--url")
    create_cmd.add_argument("--version")
    which_cmd = sub.add_parser("which", help="查找 PATH 中的可执行文件")
    which_cmd.add_argument("name")

    for unsupported_name in ("alias", "prefix", "reset", "shim", "virustotal"):
        sub.add_parser(unsupported_name, help="不适用于 Debian/apt 模型")

    install_cmd = sub.add_parser("install", help="安装应用")
    install_cmd.add_argument("app_id")
    install_cmd.add_argument("-y", "--yes", action="store_true")

    upgrade_cmd = sub.add_parser("upgrade", help="升级应用")
    upgrade_cmd.add_argument("app_id", nargs="?")
    upgrade_cmd.add_argument("-y", "--yes", action="store_true")
    upgrade_cmd.add_argument("--stop-on-error", action="store_true")

    for name in ("remove", "uninstall", "purge"):
        cmd = sub.add_parser(name)
        cmd.add_argument("app_id")
        cmd.add_argument("-y", "--yes", action="store_true")
        cmd.add_argument("--package")
    autoremove_cmd = sub.add_parser("autoremove")
    autoremove_cmd.add_argument("-y", "--yes", action="store_true")

    cache_cmd = sub.add_parser("cache")
    cache_sub = cache_cmd.add_subparsers(dest="cache_command", required=True)
    cache_clean = cache_sub.add_parser("clean")
    cache_clean.add_argument("-y", "--yes", action="store_true")

    doctor_cmd = sub.add_parser("doctor")
    _add_json(doctor_cmd)
    return parser


def cmd_bucket(args: argparse.Namespace) -> None:
    if args.bucket_command == "add":
        entry = add_bucket(args.name, args.source, yes=args.yes)
        print(f"已添加 bucket：{entry['name']}")
    elif args.bucket_command == "list":
        rows = list_buckets()
        if getattr(args, "json", False):
            print_json(rows)
        else:
            table(rows, [("name", "NAME"), ("type", "TYPE"), ("source", "SOURCE"), ("trusted", "TRUSTED")])
    elif args.bucket_command == "remove":
        remove_bucket(args.name, delete_files=args.delete_files)
        print(f"已删除 bucket：{args.name}")
    elif args.bucket_command == "update":
        updated = update_bucket(args.name)
        print(f"已更新 {len(updated)} 个 git bucket。")


def cmd_info(args: argparse.Namespace) -> None:
    app = find_app(args.app_id)
    if args.json:
        print_json(app)
        return
    for key in ("id", "name", "description", "package", "version", "arch", "bucket", "homepage", "url", "sha256"):
        print(f"{key}: {app.get(key) or ''}")


def cmd_cache_clean(args: argparse.Namespace) -> None:
    size = cache.downloads_size()
    print(f"即将清理下载缓存：{cache.human_size(size)}")
    if not confirm("继续吗？", yes=args.yes):
        print("已取消。")
        return
    cleaned = cache.clean_downloads()
    print(f"已清理：{cache.human_size(cleaned)}")


def dispatch(args: argparse.Namespace) -> None:
    ensure_initial_files()
    config = load_config()
    set_language(args.lang or config.get("language") or "auto")
    if args.command == "bucket":
        cmd_bucket(args)
    elif args.command == "update":
        if not args.no_self_update:
            update_self()
        merged = update_index(no_bucket_update=args.no_bucket_update)
        print(f"索引更新完成：{len(merged.get('apps', []))} 个应用。")
    elif args.command == "list":
        rows = list_installed() if args.installed else all_apps()
        if args.json:
            print_json(rows)
        else:
            table(rows, [("id", "ID"), ("name", "NAME"), ("package", "PACKAGE"), ("version", "VERSION"), ("bucket", "BUCKET")])
    elif args.command == "search":
        rows = search_apps(args.keyword)
        if args.json:
            print_json(rows)
        else:
            table(rows, [("id", "ID"), ("name", "NAME"), ("package", "PACKAGE"), ("version", "VERSION"), ("bucket", "BUCKET")])
    elif args.command == "info":
        cmd_info(args)
    elif args.command in {"check", "status"}:
        rows = check()
        if args.json:
            print_json(rows)
        else:
            table(rows, [("id", "ID"), ("package", "PACKAGE"), ("installed", "INSTALLED"), ("latest", "LATEST"), ("bucket", "BUCKET")])
    elif args.command == "install":
        install(args.app_id, yes=args.yes)
    elif args.command == "upgrade":
        upgrade(args.app_id, yes=args.yes, stop_on_error=args.stop_on_error)
    elif args.command in {"remove", "uninstall", "purge"}:
        remove(args.app_id, yes=args.yes, package=args.package, purge=args.command == "purge")
    elif args.command == "autoremove":
        autoremove(yes=args.yes)
    elif args.command == "cache":
        if args.cache_command == "clean":
            cmd_cache_clean(args)
    elif args.command in {"doctor", "checkup"}:
        rows = run_doctor()
        if args.json:
            print_json(rows)
        else:
            table(rows, [("item", "ITEM"), ("status", "STATUS"), ("detail", "DETAIL")])
    elif args.command == "config":
        config_command(args)
    elif args.command == "cat":
        cat_command(args.app_id)
    elif args.command == "download":
        download_command(args.app_id)
    elif args.command == "export":
        export_command(Path(args.path) if args.path else None, include_config=args.config)
    elif args.command == "import":
        import_command(Path(args.path), include_config=args.config)
    elif args.command in {"hold", "unhold"}:
        hold_command(args.app_id, args.held)
    elif args.command == "home":
        home_command(args.app_id)
    elif args.command == "depends":
        depends_command(args.app_id, package=args.package)
    elif args.command == "cleanup":
        cleanup_command(yes=args.yes)
    elif args.command == "create":
        create_command(args.app_id, Path(args.path), args.name, args.package, args.url, args.version)
    elif args.command == "which":
        which_command(args.name)
    elif args.command in {"alias", "prefix", "reset", "shim", "virustotal"}:
        unsupported(args.command)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        dispatch(args)
        return 0
    except DebupError as exc:
        print(t("error_prefix", message=exc), file=sys.stderr)
        if getattr(args, "debug", False):
            traceback.print_exc()
        return 1
    except Exception:
        if getattr(args, "debug", False):
            traceback.print_exc()
        else:
            print(t("error_prefix", message="执行失败，可使用 --debug 查看 traceback。"), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
