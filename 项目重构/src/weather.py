"""业务层：城市校验 + 带缓存的查询入口。

分层说明：
- 数据层：tools/cache.py（缓存存取）、tools/fetcher.py（数据来源）
- 业务层：本模块（校验规则 + 查询流程编排）
- 展示层：main.py（命令行输入输出）
"""
from __future__ import annotations

import logging
import re

from .tools.cache import JsonCache
from .tools.fetcher import fetch

log = logging.getLogger(__name__)

# 城市名校验：只允许中文/英文/数字/空格/连字符（保留旧版规则）
_CITY_PATTERN = re.compile(r"^[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9\s-]{0,19}$")


def check_city(city: str) -> str:
    """城市名校验：不合法直接抛 ValueError。"""
    city = city.strip()
    if not _CITY_PATTERN.match(city):
        raise ValueError(f"城市名 {city!r} 不合法")
    return city


def get_weather(city: str, config: dict) -> dict:
    """带缓存的天气查询（对外主入口）。

    config 需包含: provider / timeout / cache_file / cache_ttl
    流程：校验城市名 → 查缓存（没过期直接用）→ 未命中调接口并回写缓存。
    """
    city = check_city(city)
    cache = JsonCache(
        path=config.get("cache_file", "data/weather_cache.json"),
        ttl=config.get("cache_ttl", 3600),
    )
    entry = cache.get(city)
    if entry is not None:
        log.info("天气命中缓存 city=%s 缓存龄=%s秒", city, int(entry["age"]))
        data = dict(entry["data"])
        data["source"] = "cache"
        return data

    data = fetch(city, provider=config.get("provider", "wttr"), timeout=config.get("timeout", 8))
    cache.set(city, data)
    return data
