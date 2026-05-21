import os
from typing import Any

_LANG = "zh"

MESSAGES: dict[str, dict[str, str]] = {
    "zh": {
        "error": "错误",
        "error_prefix": "错误：{message}",
        "done": "完成。",
        "cancelled": "已取消。",
        "not_found_app": "未找到应用：{app_id}",
        "config_updated": "已更新配置：{key}={value}",
        "config_key_missing": "配置项不存在：{key}",
        "downloaded": "已下载：{path}",
        "homepage_missing": "该应用没有 homepage 字段。",
        "continue": "继续吗？",
    },
    "en": {
        "error": "Error",
        "error_prefix": "Error: {message}",
        "done": "Done.",
        "cancelled": "Cancelled.",
        "not_found_app": "App not found: {app_id}",
        "config_updated": "Updated config: {key}={value}",
        "config_key_missing": "Unknown config key: {key}",
        "downloaded": "Downloaded: {path}",
        "homepage_missing": "This app has no homepage field.",
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
