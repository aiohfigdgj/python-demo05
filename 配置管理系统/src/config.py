"""配置管理系统：支持 dev / prod / test 三套配置，可运行时热切换。

设计要点：
1. 配置存放于 config/*.yaml，按环境拆分
2. 敏感信息（API Key）用 ${ENV_NAME} 占位，运行时从环境变量注入，
   代码与配置文件中绝不出现真实密钥
3. 配置优先级：显式指定(CLI/参数) > 环境变量(MY_AGENT_ENV) > 默认值(dev)
4. 热切换：调用 get_config("prod") 或 manager.switch_env("prod")
   后立即生效，无需重启进程
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"

# 识别 ${VAR_NAME} 占位符
_ENV_PATTERN = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")

# 环境名别名，容忍 development/production 等写法
_ENV_ALIASES = {
    "dev": "dev",
    "development": "dev",
    "prod": "prod",
    "production": "prod",
    "test": "test",
}


def normalize_env(name: str) -> str:
    """把用户输入的环境名统一为 dev/prod/test。"""
    return _ENV_ALIASES.get(name, name)


def _resolve(value):
    """把 ${VAR_NAME} 解析为环境变量值；不是占位符则原样返回。"""
    if isinstance(value, str):
        m = _ENV_PATTERN.match(value)
        if m:
            return os.getenv(m.group(1))  # 环境变量未设置时返回 None
    return value


def _resolve_deep(node):
    """递归解析 dict/list 中的 ${VAR} 占位符。"""
    if isinstance(node, dict):
        return {k: _resolve_deep(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_deep(item) for item in node]
    return _resolve(node)


class Config:
    """一份环境配置，支持点号路径读取，如 config.get("weather.provider")。"""

    def __init__(self, env: str, data: dict):
        self.env = env
        self._data = data

    def get(self, key: str, default=None):
        """按点号路径取值：get("a.b.c")。缺失时返回 default。"""
        current = self._data
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def as_dict(self) -> dict:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"<Config env={self.env}>"


class ConfigManager:
    """配置管理器：负责加载与热切换。"""

    DEFAULT_ENV = "dev"

    def __init__(self, env: str | None = None):
        # 启动时读取 .env（存在才加载）
        load_dotenv(PROJECT_ROOT / ".env")
        self.env = normalize_env(env or os.getenv("MY_AGENT_ENV", self.DEFAULT_ENV))
        self._config: Config | None = None
        self._load()

    def _load(self) -> Config:
        """加载当前环境的配置。"""
        path = CONFIG_DIR / f"{self.env}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        self._config = Config(self.env, _resolve_deep(raw))
        return self._config

    def switch_env(self, env: str) -> Config:
        """热切换：运行时切换到另一套配置，立即生效。"""
        self.env = normalize_env(env)
        return self._load()

    def current(self) -> Config:
        """返回当前配置。"""
        return self._config


# ---------------- 模块级单例，供全项目共用 ----------------
_manager: ConfigManager | None = None


def get_manager() -> ConfigManager:
    """获取全局配置管理器（懒加载单例）。"""
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager


def get_config(env: str | None = None) -> Config:
    """获取配置；传入 env 时会热切换到该环境。

    用法：
        cfg = get_config()          # 当前环境
        cfg = get_config("prod")    # 热切换到 prod 并返回
    """
    manager = get_manager()
    if env is not None and normalize_env(env) != manager.env:
        return manager.switch_env(env)
    return manager.current()
