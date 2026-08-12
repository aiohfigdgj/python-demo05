"""配置驱动的工具演示：同一条"查天气"命令，不同环境行为不同。

核心教学点：配置管理系统不只管理"参数"，还决定"行为"——
    dev / test → mock 模拟数据（不访问网络）
    prod       → wttr.in 真实接口（无需密钥）

这样在交互界面里切换环境，立刻能看到行为变化（热切换的价值）。
"""
from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

MOCK_WEATHER = {
    "深圳": {"temp": "28", "weather": "晴", "humidity": "65"},
    "北京": {"temp": "22", "weather": "多云", "humidity": "45"},
    "上海": {"temp": "25", "weather": "小雨", "humidity": "80"},
    "广州": {"temp": "30", "weather": "雷阵雨", "humidity": "88"},
}


def query_weather(city: str, config) -> dict:
    """按当前环境的 weather.provider 查询天气。"""
    provider = config.get("weather.provider", "mock")
    if provider == "wttr":
        return _wttr(city, config)
    return _mock(city)


def _mock(city: str) -> dict:
    log.info("天气[mock] city=%s", city)
    info = MOCK_WEATHER.get(city, {"temp": None, "weather": "未知", "humidity": None})
    return {"city": city, **info, "source": "mock"}


def _wttr(city: str, config) -> dict:
    """真实接口 wttr.in（免费无需密钥），失败优雅降级。"""
    url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
    timeout = config.get("weather.timeout", 8)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cond = data.get("current_condition") or [{}]
        return {
            "city": city,
            "temp": cond[0].get("temp_C"),
            "weather": (cond[0].get("weatherDesc") or [{}])[0].get("value", "?"),
            "humidity": cond[0].get("humidity"),
            "source": "wttr",
        }
    except Exception as exc:
        log.error("wttr.in 请求失败 city=%s: %s", city, exc)
        return {"city": city, "temp": None, "weather": f"请求失败: {exc}", "humidity": None, "source": "error"}
