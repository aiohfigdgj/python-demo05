"""演示：三套环境配置的热切换。

运行：python -m src.demo
"""
from __future__ import annotations

from .config import get_config, get_manager


def show(env: str) -> None:
    """热切换到指定环境并打印关键配置。"""
    cfg = get_config(env)  # 传入 env = 热切换，无需重启
    print(f"--- 环境: {cfg.env} ---")
    print(f"  天气数据源   : {cfg.get('weather.provider')}")
    print(f"  缓存文件     : {cfg.get('weather.cache_file')}")
    print(f"  日志级别     : {cfg.get('app.log_level')}")
    print(f"  LLM 密钥     : {cfg.get('llm.api_key')!r}（未设置时为 None）")


if __name__ == "__main__":
    print("=== 配置管理系统演示：dev / prod / test 热切换 ===\n")
    for env_name in ("dev", "prod", "test"):
        show(env_name)
    print(f"\n当前全局环境: {get_manager().env}")
    print("结论：无需重启进程，get_config(env) 即热切换，密钥来自环境变量而非硬编码。")
