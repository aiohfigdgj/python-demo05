"""意图解析：把用户输入的自然语言翻译成可执行的动作。

这就是"自主性"的最小实现——看懂输入，决定干什么。
规则式意图识别（不调用大模型），与 Day4"工具选择测试"一脉相承。

支持的说法：
    添加：标题 / 内容 / 标签      -> import
    什么是 Python？ / 查：算法    -> query
    列表 / 列出                  -> list
    删除：3                      -> delete
    帮助                          -> help
    退出                          -> exit
    其他                          -> unknown（告诉用户怎么用）
"""
from __future__ import annotations

import re

# 导入动作词（匹配到任一即认为要"添加知识"）
IMPORT_WORDS = ("添加", "新增", "导入", "add", "import", "加入")
# 删除动作词
DELETE_WORDS = ("删除", "删掉", "remove", "del")
# 查询：开头去掉这些词后剩下的就是关键词（长的放前面，优先匹配）
QUERY_PREFIX = r"^(什么是|是什么|介绍一下|介绍|搜索|查找|查一下|帮我查|查|搜|请|帮我)"
# 结尾的标点/语气词清理
_TAIL = r"[：:，,？?。.！!  ]+$"


def parse_intent(text: str) -> dict:
    """解析用户输入，返回 {"action": ..., "args": {...}}。"""
    t = text.strip()
    low = t.lower()

    # ---- 退出 / 帮助 / 列表（整句匹配）----
    if low in ("退出", "exit", "quit", "q", "拜拜"):
        return {"action": "exit"}
    if low in ("帮助", "help", "h", "？", "?"):
        return {"action": "help"}
    if low in ("列表", "列出", "全部", "看看", "list", "ls"):
        return {"action": "list"}

    # ---- 添加知识：添加：标题 / 内容 / 标签 ----
    if any(word in t for word in IMPORT_WORDS):
        return _parse_import(t)

    # ---- 删除：删除：3 ----
    for word in DELETE_WORDS:
        if word in t:
            m = re.search(r"\d+", t)
            if m:
                return {"action": "delete", "id": int(m.group())}
            return {"action": "unknown", "reason": "删除需要指定 id，例如：删除：3"}

    # ---- 查询：什么是 Python？/ 查：算法 ----
    kw = re.sub(QUERY_PREFIX, "", t, count=1)
    kw = re.sub(_TAIL, "", kw).strip("：:，, ")
    if kw and kw != t:  # 去掉过动作词才认为是查询
        return {"action": "query", "keyword": kw}
    if "：" in t or ":" in t:
        return {"action": "query", "keyword": t.split("：", 1)[-1].split(":", 1)[-1].strip()}

    # ---- 兜底：没听懂 ----
    return {"action": "unknown"}


def _parse_import(text: str) -> dict:
    """解析"添加：标题 / 内容 / 标签"格式。"""
    # 取第一个冒号后的内容
    rest = re.split(r"[：:]", text, maxsplit=1)
    rest = rest[1] if len(rest) > 1 else text
    # 去掉可能残留的动作词
    for word in IMPORT_WORDS:
        if rest.startswith(word):
            rest = rest[len(word):]
            break
    parts = [p.strip() for p in re.split(r"[／/｜|]", rest) if p.strip()]
    if len(parts) >= 2:
        tags = parts[2].replace("标签", "").strip() if len(parts) > 2 else ""
        return {
            "action": "import",
            "title": parts[0],
            "content": parts[1],
            "tags": [x.strip() for x in tags.split(",") if x.strip()],
        }
    return {"action": "unknown", "reason": "格式：添加：标题 / 内容 / 标签"}
