"""数据源层：负责"从哪里拿天气数据"。

- mock：本地模拟数据（开发调试用，不访问网络）
- wttr：真实接口 wttr.in（免费，无需密钥）——与旧版工具一致的数据源

出各种错就抛异常（TimeoutError / ConnectionError / LookupError），
由业务层或展示层统一接住（与旧版设计一致）。
"""
from __future__ import annotations

import logging
import time
from urllib.parse import quote

import requests

log = logging.getLogger(__name__)

# 模拟数据源：开发调试用
MOCK_WEATHER = {
    "深圳": {"temp": "28", "weather": "晴", "humidity": "65"},
    "北京": {"temp": "22", "weather": "多云", "humidity": "45"},
    "上海": {"temp": "25", "weather": "小雨", "humidity": "80"},
    "广州": {"temp": "30", "weather": "雷阵雨", "humidity": "88"},
}


def fetch(city: str, provider: str = "wttr", timeout: int = 8) -> dict:
    """按数据源名称取数据，返回统一格式 dict（含 source 标记）。"""
    if provider == "mock":
        return _fetch_mock(city)
    return _fetch_wttr(city, timeout)


def _fetch_mock(city: str) -> dict:
    log.info("天气[mock] city=%s", city)
    info = MOCK_WEATHER.get(city, {"temp": None, "weather": "未知", "humidity": None})
    return {
        "city": city,
        "temp": info["temp"],
        "weather": info["weather"],
        "humidity": info["humidity"],
        "source": "mock",
    }


def _fetch_wttr(city: str, timeout: int) -> dict:
    """真实接口：wttr.in。超时 / 断网 / 城市不存在分别抛对应异常。"""
    url = f"https://wttr.in/{quote(city)}?format=j1"
    start = time.time()
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.Timeout as exc:
        log.error("wttr.in 请求超时 city=%s", city)
        raise TimeoutError("请求超时了，是不是网络不好") from exc
    except requests.exceptions.ConnectionError as exc:
        log.error("wttr.in 连接失败 city=%s", city)
        raise ConnectionError("连不上网，检查下网络") from exc
    except (requests.exceptions.HTTPError, ValueError) as exc:
        # 城市名不对时 wttr.in 返回的不是 JSON，当成没这个城市
        raise LookupError(f"找不到城市 {city}，换个写法试试") from exc

    cond = data.get("current_condition") or [{}]
    if not cond or not cond[0].get("temp_C"):
        raise LookupError(f"查不到 {city} 的天气")

    elapsed = time.time() - start
    log.info("wttr.in 请求成功 city=%s 耗时=%.2fs 状态码=%s", city, elapsed, r.status_code)
    return {
        "city": city,
        "temp": cond[0]["temp_C"],
        "weather": (cond[0].get("weatherDesc") or [{}])[0].get("value", "?"),
        "humidity": cond[0].get("humidity", "?"),
        "source": "wttr",
    }
