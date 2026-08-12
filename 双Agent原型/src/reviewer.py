"""Reviewer Agent：审查 Writer 的草稿，返回评分、意见与是否通过。

多 Agent 分工中的"审查者"角色——
职责边界清晰：Reviewer 只评审，不修改原文；输入输出 schema 统一。
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

# 最低字数要求（教学演示阈值）
MIN_WORDS = 30

# 敏感词表（教学演示用简化规则）
BAD_WORDS = ["广告推销", "代写论文"]


class ReviewerAgent:
    """审查者：对草稿做规则检查（字数 / 结构 / 敏感词）。"""

    def __init__(self, name: str = "reviewer"):
        self.name = name

    def review(self, draft: dict, mode: str = "essay") -> dict:
        """审查草稿，返回 {"passed", "score", "comments", "word_count"}。

        mode 决定检查哪些结构：essay=概述/结论，outline=大纲结构，summary=总结结构。
        """
        text = draft.get("text", "")
        word_count = draft.get("word_count", len(text))
        checks = {
            "字数达标(≥30)": word_count >= MIN_WORDS,
            "无敏感词": not self._contains_bad_words(text),
        }
        # 按模式检查结构
        if mode == "outline":
            checks["包含大纲标题"] = "大纲" in text or "《" in text
            checks["包含分节结构"] = "一、" in text or "1." in text or "1、" in text
        elif mode == "summary":
            checks["包含总结标题"] = "总结" in text or "【" in text
            checks["包含结论"] = "结论" in text or "核心" in text
        else:  # essay 及默认
            checks["包含概述段落"] = "概述" in text
            checks["包含结论段落"] = "结论" in text

        passed = all(checks.values())
        comments = [name for name, ok in checks.items() if not ok] or ["内容完整，可以定稿"]
        score = 40 + 60 * sum(checks.values()) / len(checks)
        log.info(
            "Reviewer 评审结果 mode=%s passed=%s score=%.1f comments=%s",
            mode, passed, score, comments,
        )
        return {
            "passed": passed,
            "score": score,
            "comments": comments,
            "word_count": word_count,
        }

    def _contains_bad_words(self, text: str) -> bool:
        return any(word in text for word in BAD_WORDS)
