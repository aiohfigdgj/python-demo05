"""测试：配置驱动的工具演示（mock / wttr 数据源按配置切换）。"""
from unittest.mock import MagicMock, patch

from src.config import Config
from src.toolbox import MOCK_WEATHER, query_weather

# 构造各环境的"行为配置"
DEV_CFG = Config("dev", {"weather": {"provider": "mock"}})
PROD_CFG = Config("prod", {"weather": {"provider": "wttr", "timeout": 5}})


def test_mock_source_used_in_dev():
    """dev 环境：provider=mock → 返回模拟数据。"""
    data = query_weather("深圳", DEV_CFG)
    assert data["source"] == "mock"
    assert data["weather"] == "晴"


def test_mock_unknown_city():
    data = query_weather("火星", DEV_CFG)
    assert data["weather"] == "未知"
    assert data["temp"] is None


def test_wttr_source_used_in_prod_mocked():
    """prod 环境：provider=wttr → 走真实接口（Mock 网络）。"""
    fake = MagicMock()
    # bytes 字面量只能含 ASCII，中文用字符串 encode
    fake.read.return_value = (
        '{"current_condition": [{"temp_C": "30", "humidity": "70",'
        ' "weatherDesc": [{"value": "晴"}]}]}'
    ).encode("utf-8")
    # with urlopen(...) as resp 拿到的应是 fake 自身
    fake.__enter__.return_value = fake
    with patch("src.toolbox.urllib.request.urlopen", return_value=fake) as mock_open:
        data = query_weather("深圳", PROD_CFG)
    mock_open.assert_called_once()
    assert data["source"] == "wttr"
    assert data["temp"] == "30"


def test_wttr_failure_degrades():
    """真实接口失败：不 crash，返回错误信息。"""
    with patch("src.toolbox.urllib.request.urlopen", side_effect=Exception("网络超时")):
        data = query_weather("深圳", PROD_CFG)
    assert data["source"] == "error"
    assert "失败" in data["weather"]


def test_same_command_different_behavior():
    """同一个城市：dev 与 prod 走不同数据源（配置驱动行为）。"""
    dev = query_weather("深圳", DEV_CFG)
    assert dev["source"] == "mock"
    # prod 配置决定走 wttr；Mock 断网证明它确实没走 mock
    with patch("src.toolbox.urllib.request.urlopen", side_effect=Exception("offline")):
        prod = query_weather("深圳", PROD_CFG)
    assert prod["source"] == "error"  # 走了 wttr 但断网 → error，绝不可能是 mock
