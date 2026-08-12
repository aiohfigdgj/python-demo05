"""LLM 客户端：给 Writer 提供"文字生成"能力（统一接口，双实现）。

【无硬编码敏感信息】API Key 只从环境变量读取，代码里零密钥。
【优雅降级】没配 key / 网络失败时自动回落到 mock 模板，程序永远能跑。

Provider 由环境变量决定：
    LLM_PROVIDER = mock | llm     （默认 mock）
    LLM_API_KEY  = sk-xxx         （llm 模式必需）
    LLM_BASE_URL = https://api.openai.com/v1   （可换成国内兼容服务，如 DeepSeek 等）
    LLM_MODEL    = gpt-3.5-turbo  （可按服务调整）
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

# 可选依赖：requests / python-dotenv 都不强制安装——
# 没装也能跑（自动降级 mock），装了就能用真实 LLM 和 .env 自动加载
try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    requests = None  # type: ignore
    _REQUESTS_OK = False
    log.debug("requests 未安装，将无法调用真实 LLM（仅可用 mock）")

try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).resolve().parents[1] / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    log.debug("python-dotenv 未安装，跳过 .env 加载（可用系统环境变量设置密钥）")

# 找"关于「X」的短文"里的主题（mock 模式回显用）
_MOCK_THEME = "关于「{topic}」的短文"


class LLMClient:
    """统一文字生成客户端：mock / 真实 API 两种 provider。"""

    def __init__(self, provider: str | None = None):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "mock")).lower()
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

    def is_available(self) -> bool:
        """真实 LLM 可用 = 配置齐全：llm 模式 + 有 API Key + 有 requests 库。"""
        return self.provider == "llm" and bool(self.api_key) and _REQUESTS_OK

    def status_info(self) -> dict:
        """返回当前 LLM 配置状态（用于界面展示）。"""
        key = self.api_key
        masked = (key[:6] + "***" + key[-4:]) if key else "(未配置)"
        return {
            "provider": self.provider,
            "api_key_configured": bool(key),
            "api_key_masked": masked,
            "base_url": self.base_url,
            "model": self.model,
            "requests_available": _REQUESTS_OK,
            "available": self.is_available(),
        }

    def format_status(self) -> str:
        """把状态格式化为可打印的多行字符串。"""
        s = self.status_info()
        mark = lambda ok: "✓" if ok else "✗"
        lines = [
            "【API 配置状态】",
            f"  {mark(s['provider'] == 'llm')}  Provider : {s['provider']}",
            f"  {mark(s['api_key_configured'])}  API Key  : {s['api_key_masked']}",
            f"  {mark(s['base_url'])}  Base URL : {s['base_url']}",
            f"  {mark(bool(s['model']))}  Model    : {s['model']}",
            f"  {mark(s['requests_available'])}  requests 库: {'已安装' if s['requests_available'] else '未安装'}",
            "",
            f"  →  {'✓ 可以使用真实大模型' if s['available'] else '✗ 无法使用，将降级 mock'}",
        ]
        return "\n".join(lines)

    def generate(self, prompt: str, max_tokens: int = 300) -> str:
        """根据 prompt 生成文字；不可用时降级到 mock。"""
        if not self.is_available():
            reason = []
            if self.provider != "llm":
                reason.append(f"provider={self.provider}")
            if not self.api_key:
                reason.append("无 API_KEY")
            if not _REQUESTS_OK:
                reason.append("未装 requests 库")
            log.info("LLM 不可用（%s），降级 mock", " / ".join(reason))
            return self._mock_generate(prompt)
        return self._api_generate(prompt, max_tokens)

    # ---------------- 真实 API 实现 ----------------
    def _api_generate(self, prompt: str, max_tokens: int) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        log.info("LLM 请求 model=%s", self.model)
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
            log.info("LLM 返回成功，长度=%s", len(text))
            return text
        except Exception as exc:
            log.error("LLM 请求失败: %s", exc)
            # 网络/密钥问题时不 crash，降级给提示
            return f"[LLM 调用失败（{exc}），请检查 LLM_API_KEY / 网络]"

    # ---------------- mock 实现 ----------------
    def _mock_generate(self, prompt: str) -> str:
        """mock：从 prompt 里提取主题，回显一句模板话（演示用）。"""
        topic = prompt.split("主题是「", 1)[-1].split("」", 1)[0] if "主题是「" in prompt else "主题"
        return _MOCK_THEME.format(topic=topic) + "\n（mock 模式：配置 LLM_API_KEY 后使用真实模型生成）"
