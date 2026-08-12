"""测试：重构后的天气工具（校验 / 缓存 / 数据源切换 / 异常分级）。"""
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.main import load_config
from src.tools.cache import JsonCache
from src.tools.fetcher import fetch
from src.weather import check_city, get_weather

import json
import time


# 测试用配置：provider=mock + 临时缓存，避免网络请求与文件污染
def make_cfg(tmp_path) -> dict:
    return {
        "provider": "mock",
        "timeout": 5,
        "cache_file": str(tmp_path / "wc.json"),
        "cache_ttl": 3600,
    }


# ---------------- 城市名校验（旧版功能5）----------------
@pytest.mark.parametrize(
    "city,ok",
    [
        ("深圳", True),
        ("New York", True),
        ("Shenzhen-1", True),
        ("深圳南山", True),
        ("", False),
        ("深@圳", False),
        ("a" * 30, False),
        ("123abc", False),
    ],
)
def test_check_city(city, ok):
    if ok:
        assert check_city(city) == city.strip()
    else:
        with pytest.raises(ValueError):
            check_city(city)


# ---------------- 数据源：mock ----------------
def test_mock_fetch():
    data = fetch("深圳", provider="mock")
    assert data["source"] == "mock"
    assert data["weather"] == "晴"


def test_mock_unknown_city():
    data = fetch("火星", provider="mock")
    assert data["weather"] == "未知"
    assert data["temp"] is None


# ---------------- 数据源：wttr.in（Mock 网络）----------------
def test_wttr_success_mocked():
    fake = MagicMock()
    fake.status_code = 200
    fake.json.return_value = {
        "current_condition": [
            {"temp_C": "28", "humidity": "65", "weatherDesc": [{"value": "Sunny"}]}
        ]
    }
    with patch("src.tools.fetcher.requests.get", return_value=fake) as mock_get:
        data = fetch("深圳", provider="wttr")
    mock_get.assert_called_once()
    assert data["source"] == "wttr"
    assert data["temp"] == "28"
    assert data["weather"] == "Sunny"


def test_wttr_timeout_raises():
    with patch("src.tools.fetcher.requests.get", side_effect=requests.exceptions.Timeout()):
        with pytest.raises(TimeoutError):
            fetch("深圳", provider="wttr")


def test_wttr_connection_error_raises():
    with patch("src.tools.fetcher.requests.get", side_effect=requests.exceptions.ConnectionError()):
        with pytest.raises(ConnectionError):
            fetch("深圳", provider="wttr")


def test_wttr_city_not_found_raises():
    with patch("src.tools.fetcher.requests.get", side_effect=requests.exceptions.HTTPError()):
        with pytest.raises(LookupError):
            fetch("不存在城市", provider="wttr")


# ---------------- 缓存（旧版功能3）----------------
def test_cache_hit_second_call(tmp_path):
    cfg = make_cfg(tmp_path)
    first = get_weather("北京", cfg)
    assert first["source"] == "mock"

    second = get_weather("北京", cfg)
    assert second["source"] == "cache"  # 第二次命中缓存
    assert second["temp"] == first["temp"]

    with open(tmp_path / "wc.json", encoding="utf-8") as f:
        cache = json.load(f)
    assert "北京" in cache


def test_cache_expired(tmp_path):
    path = tmp_path / "wc.json"
    cache = JsonCache(path, ttl=10)
    cache.set("深圳", {"temp": "28"})
    # 手工把时间戳改老
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["深圳"]["ts"] = time.time() - 100
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    assert cache.get("深圳") is None


def test_cache_clear(tmp_path):
    cache = JsonCache(tmp_path / "wc.json", ttl=3600)
    cache.set("深圳", {"temp": "28"})
    assert cache.clear() is True
    assert cache.clear() is False


def test_cache_corrupted_file_ok(tmp_path):
    path = tmp_path / "wc.json"
    path.write_text("坏文件{{{", encoding="utf-8")
    cache = JsonCache(path, ttl=3600)
    assert cache.get("深圳") is None
    assert cache.all() == {}


# ---------------- 配置读取 ----------------
def test_load_config_has_required_keys():
    config = load_config()
    assert config["provider"] in ("mock", "wttr")
    assert config["timeout"] > 0
    assert "cache_file" in config
