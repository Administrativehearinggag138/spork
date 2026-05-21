import os
from typing import Any

_LANG = "zh"

MESSAGES: dict[str, dict[str, str]] = {
    "zh": {
        "error": "错误",
        "error_prefix": "错误：{message}",
        "unsupported": "该命令不适合 Debian/apt 模型，Spork 不实现：{command}",
        "unsupported_detail": "原因：{reason}",
        "done": "完成。",
        "cancelled": "已取消。",
        "not_found_app": "未找到应用：{app_id}",
        "config_updated": "已更新配置：{key}={value}",
        "config_key_missing": "配置项不存在：{key}",
        "downloaded": "已下载：{path}",
        "exported": "已导出：{path}",
        "imported": "已导入配置和 bucket。应用列表只作为安装计划，不会自动安装。",
        "held": "已锁定更新：{app_id}",
        "unheld": "已解除更新锁定：{app_id}",
        "already_held": "已锁定：{app_id}",
        "not_held": "未锁定：{app_id}",
        "skip_held": "跳过已锁定应用：{app_id}",
        "homepage_missing": "该应用没有 homepage 字段。",
        "which_not_found": "未找到可执行文件：{name}",
        "cleanup_plan": "即将清理下载缓存：{size}",
        "continue": "继续吗？",
    },
    "en": {
        "error": "Error",
        "error_prefix": "Error: {message}",
        "unsupported": "This command does not fit the Debian/apt model and is not implemented by Spork: {command}",
        "unsupported_detail": "Reason: {reason}",
        "done": "Done.",
        "cancelled": "Cancelled.",
        "not_found_app": "App not found: {app_id}",
        "config_updated": "Updated config: {key}={value}",
        "config_key_missing": "Unknown config key: {key}",
        "downloaded": "Downloaded: {path}",
        "exported": "Exported: {path}",
        "imported": "Imported config and buckets. App entries are treated as an install plan and are not installed automatically.",
        "held": "Held updates for: {app_id}",
        "unheld": "Unheld updates for: {app_id}",
        "already_held": "Already held: {app_id}",
        "not_held": "Not held: {app_id}",
        "skip_held": "Skipping held app: {app_id}",
        "homepage_missing": "This app has no homepage field.",
        "which_not_found": "Executable not found: {name}",
        "cleanup_plan": "Download cache to clean: {size}",
        "continue": "Continue?",
    },
}


def normalize_language(value: str | None) -> str:
    if not value:
        return "zh" if os.environ.get("LANG", "").lower().startswith("zh") else "en"
    value = value.lower().replace("_", "-")
    if value.startswith("zh"):
        return "zh"
    if value.startswith("en"):
        return "en"
    return "en"


def set_language(value: str | None) -> None:
    global _LANG
    _LANG = normalize_language(value)


def t(message_id: str, **kwargs: Any) -> str:
    text = MESSAGES.get(_LANG, MESSAGES["en"]).get(message_id, MESSAGES["en"].get(message_id, message_id))
    return text.format(**kwargs)
