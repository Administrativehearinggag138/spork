import json
from typing import Any, Iterable


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def warn(message: str) -> None:
    print(f"警告：{message}")


def table(rows: Iterable[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
    rows = list(rows)
    if not rows:
        print("没有结果。")
        return
    widths: list[int] = []
    for key, title in columns:
        values = [str(row.get(key, "") or "") for row in rows]
        widths.append(max([len(title), *map(len, values)]))
    header = "  ".join(title.ljust(widths[index]) for index, (_, title) in enumerate(columns))
    print(header)
    for row in rows:
        print("  ".join(str(row.get(key, "") or "").ljust(widths[index]) for index, (key, _) in enumerate(columns)))


def confirm(prompt: str, yes: bool = False) -> bool:
    if yes:
        return True
    answer = input(f"{prompt} [y/N] ").strip().lower()
    return answer in {"y", "yes"}
