"""数据层：JSON 文件缓存（单一职责：存取 + TTL 过期）。

从旧版 weather-tool 的缓存逻辑中抽离成独立模块，可复用、可测试。
职责边界：只负责"存什么、什么时候过期"，不关心数据从哪来。
"""
from __future__ import annotations

import json
import time
from pathlib import Path


class JsonCache:
    """把任意键值对持久化到 JSON 文件，带 TTL 过期控制。"""

    def __init__(self, path: str | Path, ttl: int = 3600):
        self.path = Path(path)
        self.ttl = ttl  # 有效期（秒）

    def get(self, key: str) -> dict | None:
        """取缓存。未命中或已过期返回 None；命中返回 {"data": ..., "age": 秒}。"""
        if not self.path.exists():
            return None
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None  # 缓存损坏视作未命中
        entry = data.get(key)
        if not entry:
            return None
        age = time.time() - entry.get("ts", 0)
        if age >= self.ttl:
            return None  # 过期视作未命中
        return {"data": entry.get("data"), "age": age}

    def set(self, key: str, value) -> None:
        """写入缓存（自动带上当前时间戳）。"""
        data = {}
        if self.path.exists():
            try:
                with open(self.path, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}
        data[key] = {"ts": time.time(), "data": value}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # 先写临时文件再替换，避免中途写坏主文件
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self.path)

    def all(self) -> dict:
        """查看全部缓存条目（不判断过期）。"""
        if not self.path.exists():
            return {}
        try:
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def clear(self) -> bool:
        """清除缓存文件；有文件返回 True，本来就没有返回 False。"""
        if self.path.exists():
            self.path.unlink()
            return True
        return False

    def __len__(self) -> int:
        return len(self.all())
