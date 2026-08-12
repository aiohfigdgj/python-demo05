# 知识库：JSON 文件存储，支持增 / 删 / 查 / 关键词搜索。

from __future__ import annotations

import json
import time
from pathlib import Path


class KnowledgeStore:
    """一个极简的知识库：条目列表持久化到单个 JSON 文件。"""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._entries: list[dict] = self._load()

    # ---------- 读取 / 保存 ----------
    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, ensure_ascii=False, indent=2)
        tmp.replace(self.path)

    # ---------- 业务操作 ----------
    def add(self, title: str, content: str, tags: list[str] | None = None) -> dict:
        """新增一条知识，返回条目。"""
        entry = {
            "id": self._next_id(),
            "title": title,
            "content": content,
            "tags": tags or [],
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._entries.append(entry)
        self._save()
        return entry

    def search(self, keyword: str) -> list[dict]:
        """按关键词在标题 / 内容 / 标签中搜索（不区分大小写）。"""
        kw = keyword.strip().lower()
        if not kw:
            return []
        return [
            e
            for e in self._entries
            if kw in e["title"].lower()
            or kw in e["content"].lower()
            or any(kw in tag.lower() for tag in e.get("tags", []))
        ]

    def list_all(self) -> list[dict]:
        return list(self._entries)

    def get(self, entry_id: int) -> dict | None:
        for e in self._entries:
            if e["id"] == entry_id:
                return e
        return None

    def delete(self, entry_id: int) -> bool:
        """按 id 删除，成功返回 True，不存在返回 False。"""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e["id"] != entry_id]
        if len(self._entries) == before:
            return False
        self._save()
        return True

    def count(self) -> int:
        return len(self._entries)

    def _next_id(self) -> int:
        return max((e["id"] for e in self._entries), default=0) + 1
