"""展示层 + 入口：argparse 命令行参数（重构自旧版交互菜单）。

旧版：input() 循环菜单，无法脚本化。
新版：全部用参数表达，功能完全保留：

    python -m src.main weather --city 深圳          # 单城市
    python -m src.main weather --cities "深圳,北京"  # 批量表格
    python -m src.main weather --cache              # 查看缓存
    python -m src.main weather --clear-cache        # 清除缓存
    python -m src.main weather --interactive        # 保留旧版交互菜单
    python -m src.main weather --provider mock      # 切换数据源
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

from .weather import check_city, get_weather

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_config() -> dict:
    """读取 config/config.json 作为默认配置（旧版硬编码，现由配置驱动）。"""
    path = PROJECT_ROOT / "config" / "config.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weather-cli",
        description="天气查询工具（重构自旧版 weather-tool）",
    )
    parser.add_argument("--provider", choices=["mock", "wttr"], default=None, help="数据源：mock=模拟 / wttr=真实接口")
    parser.add_argument("--city", default=None, help="查询单个城市")
    parser.add_argument("--cities", default=None, help="批量查询，逗号隔开，如: 深圳,北京")
    parser.add_argument("--cache", action="store_true", help="查看缓存")
    parser.add_argument("--clear-cache", action="store_true", help="清除缓存")
    parser.add_argument("--interactive", action="store_true", help="进入交互菜单模式")
    parser.add_argument("--verbose", action="store_true", help="输出 DEBUG 日志")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    config = load_config()
    if args.provider:
        config["provider"] = args.provider  # 命令行优先级最高

    try:
        if args.clear_cache:
            return _clear_cache(config)
        if args.cache:
            return _show_cache(config)
        if args.interactive:
            return _interactive(config)
        if args.cities:
            return _query_many(args.cities, config)
        return _query_one(args.city or "深圳", config)
    except Exception as exc:
        print(f"出错：{exc}")
        return 1


# ---------------- 各功能实现（对应旧版菜单 1~4）----------------
def _query_one(city: str, config: dict) -> int:
    data = get_weather(city, config)
    print(f"\n【{data['city']}】（来源: {data['source']}）")
    print(f"温度 {data['temp']}℃  天气 {data['weather']}  湿度 {data['humidity']}%")
    if data["temp"] is not None and int(float(data["temp"])) < 10:
        print("都10度以下了，记得加衣服！")
    return 0


def _query_many(cities_text: str, config: dict) -> int:
    cities = [c.strip() for c in re.split(r"[，,]", cities_text) if c.strip()]
    if not cities:
        print("没输入城市")
        return 1
    rows = []
    for city in cities:
        try:
            rows.append(get_weather(city, config))
        except Exception as exc:
            print(f"{city} 出错了：{exc}")  # 单个失败不影响别的
    if rows:
        print(f"\n{'城市':<8}{'温度':<6}{'天气':<10}{'湿度':<6}")
        print("-" * 32)
        for d in rows:
            temp = f"{d['temp']}℃" if d["temp"] is not None else "-"
            humi = f"{d['humidity']}%" if d["humidity"] is not None else "-"
            print(f"{d['city']:<8}{temp:<6}{d['weather']:<10}{humi:<6}")
    return 0


def _show_cache(config: dict) -> int:
    from .tools.cache import JsonCache

    cache = JsonCache(config["cache_file"], config["cache_ttl"])
    entries = cache.all()
    if not entries:
        print("缓存是空的（还没查过城市）")
        return 0
    print(f"缓存里存了 {len(entries)} 个城市：")
    for city, entry in entries.items():
        d = entry.get("data", {})
        age = int(time.time() - entry.get("ts", 0))
        print(f"  {city}：{d.get('temp')}℃，{d.get('weather')}（{age}秒前查的）")
    return 0


def _clear_cache(config: dict) -> int:
    from .tools.cache import JsonCache

    cache = JsonCache(config["cache_file"], config["cache_ttl"])
    print("✔ 缓存已清除" if cache.clear() else "本来就没缓存")
    return 0


def _interactive(config: dict) -> int:
    """交互菜单模式：保留旧版的使用体验，但底层走重构后的新代码。"""
    print("=" * 28)
    print("     天气查询小工具")
    print("=" * 28)
    while True:
        print("\n请选择功能：")
        print("  1. 查询单个城市")
        print("  2. 批量查询（多个城市，逗号隔开）")
        print("  3. 查看缓存")
        print("  4. 清除缓存")
        print("  0. 退出")
        choice = input("输入数字：").strip()
        if choice == "1":
            _query_one(input("输城市名：").strip(), config)
        elif choice == "2":
            _query_many(input("输多个城市，用逗号隔开：").strip(), config)
        elif choice == "3":
            _show_cache(config)
        elif choice == "4":
            _clear_cache(config)
        elif choice == "0":
            print("拜拜~")
            break
        else:
            print("没这个选项，再输一次")
    return 0


if __name__ == "__main__":
    sys.exit(main())
