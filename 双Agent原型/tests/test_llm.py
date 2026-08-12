"""测试：LLM 客户端（mock 降级 / 真实 API Mock 成功与失败 / 密钥不硬编码）。"""
from unittest.mock import MagicMock, patch

import pytest

from src.llm import LLMClient


def test_mock_provider_by_default():
    """默认（无环境变量）是 mock 模式，不可用真实 LLM。"""
    client = LLMClient(provider="mock")
    assert client.is_available() is False


def test_mock_generate_returns_template():
    """mock 模式 generate 返回提示性模板，不崩。"""
    client = LLMClient(provider="mock")
    text = client.generate("请写一篇中文短文，主题是「Python 学习」")
    assert "Python 学习" in text
    assert "mock" in text  # 提示当前是 mock


def test_llm_requires_api_key(monkeypatch):
    """llm 模式但没有 key → is_available=False（不硬编码假密钥）。"""
    monkeypatch.delenv("LLM_API_KEY", raising=False)  # 清除 .env 注入的 key
    client = LLMClient(provider="llm")
    assert client.is_available() is False


def test_llm_available_with_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test-123")
    client = LLMClient(provider="llm")
    assert client.is_available() is True


def test_api_generate_success_mocked(monkeypatch):
    """Mock 真实请求：验证成功路径解析。"""
    monkeypatch.setenv("LLM_API_KEY", "sk-test-123")
    fake = MagicMock()
    fake.json.return_value = {"choices": [{"message": {"content": " 这是生成的短文。  "}}]}
    with patch("src.llm.requests.post", return_value=fake) as mock_post:
        client = LLMClient(provider="llm")
        text = client.generate("请写一篇短文")
    mock_post.assert_called_once()
    assert text == "这是生成的短文。"  # strip 后无首尾空格


def test_api_generate_failure_degrades(monkeypatch):
    """请求失败不 crash，返回提示信息。"""
    monkeypatch.setenv("LLM_API_KEY", "sk-test-123")
    with patch("src.llm.requests.post", side_effect=Exception("网络超时")):
        client = LLMClient(provider="llm")
        text = client.generate("请写一篇短文")
    assert "LLM 调用失败" in text


def test_llm_request_uses_env_key(monkeypatch):
    """请求头里用的 key 来自环境变量（无硬编码）。"""
    monkeypatch.setenv("LLM_API_KEY", "sk-from-env")
    fake = MagicMock()
    fake.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    with patch("src.llm.requests.post", return_value=fake) as mock_post:
        LLMClient(provider="llm").generate("hi")
    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer sk-from-env"
