"""Writer Agent：按主题撰写短文（规则式生成，模拟大模型输出）。

写作流水线 Writer → Reviewer → Revise。
职责边界：Writer 只负责"写"，不负责"评价"——但对主题合规性有第一道预审。

"""
from __future__ import annotations

import logging

from .llm import LLMClient

log = logging.getLogger(__name__)

# 明显不适合的主题关键词（教学演示用——真实生产环境需要更完善的方案）
REFUSED_KEYWORDS = (
    # 色情 / 暴力
    "性爱", "色情", "裸聊", "约炮", "强奸", "乱伦",
    "杀人方法", "自杀方法", "自制炸弹", "毒品制作",
    # 违法 / 赌博
    "毒品", "赌博", "洗钱", "黑客攻击", "破解WiFi密码",
    # 政治 / 歧视
    "种族灭绝",
)

# 主题分类：按关键词匹配 → 不同模板（mock 降级时使用）
TOPIC_CATEGORIES = {
    "学习": "学习技术",
    "历史": "历史人文",
    "美食": "生活美食",
    "技术": "工程技术",
    "编程": "学习技术",
    "Python": "学习技术",
    "算法": "学习技术",
    "机器学习": "学习技术",
    "数据库": "工程技术",
    "AI": "工程技术",
    "哲学": "历史人文",
    "文学": "历史人文",
    "文化": "历史人文",
    "菜": "生活美食",
    "咖啡": "生活美食",
    "茶": "生活美食",
    "奶茶": "生活美食",
    "汉堡": "生活美食",
}

# 每类主题对应的差异化模板（mock 降级时使用）
TEMPLATES = {
    "学习技术": (
        "{topic}可以从以下几个角度系统学习：\n"
        "1. 基础概念：搞清楚核心定义与关键术语\n"
        "2. 动手实践：边学边敲代码或做笔记\n"
        "3. 项目应用：用所学做一个小项目巩固"
    ),
    "历史人文": (
        "理解{topic}可以从三条线出发：\n"
        "1. 时间线：关键事件按年代梳理\n"
        "2. 人物线：核心人物的决策与影响\n"
        "3. 评价线：后世的多角度评价与争议"
    ),
    "生活美食": (
        "品味{topic}的几个关键点：\n"
        "1. 选材：原料新鲜度决定上限\n"
        "2. 做法：火候与时间把握基本功\n"
        "3. 场景：和谁吃、在哪吃同样重要"
    ),
    "工程技术": (
        "实践{topic}需要关注：\n"
        "1. 原理：了解底层机制而非只背 API\n"
        "2. 工具：选对工具能少走弯路\n"
        "3. 场景：在真实业务里验证假设"
    ),
}


def classify_topic(topic: str) -> str:
    """根据关键词把主题归类，找不到就返回 'default'。"""
    for keyword, category in TOPIC_CATEGORIES.items():
        if keyword in topic:
            return category
    return "default"


class WriterAgent:
    """写手：优先用真实 LLM 写作，没配 key 时降级到分类模板。"""

    def __init__(self, name: str = "writer", llm: LLMClient | None = None):
        self.name = name
        self.llm = llm or LLMClient()
        self._revision_hint = ""  # 来自 Reviewer 的修改意见

    def should_refuse(self, topic: str) -> str | None:
        """主题预审：返回 None 表示可以通过，返回字符串说明拒绝原因。"""
        topic = topic.strip()
        if len(topic) < 2:
            return "主题过短（少于 2 个字），请换个更有意义的主题"
        for word in REFUSED_KEYWORDS:
            if word in topic:
                return f"主题包含敏感内容（{word}），不适合写作"
        return None

    def set_revision(self, comments: list[str]) -> None:
        """接收 Reviewer 的意见，下一轮写作时参考。"""
        self._revision_hint = "；".join(comments)

    def write(self, topic: str, mode: str = "essay") -> dict:
        """生成草稿，返回 {"topic", "mode", "text", "word_count"}。

        mode: essay=短文 / outline=大纲 / summary=总结
        有 LLM → 真实模型生成；否则 → mock 分类模板。
        """
        text = self._compose(topic, mode)
        log.info(
            "Writer 生成草稿 topic=%s mode=%s 引擎=%s 字数=%s",
            topic, mode, "llm" if self.llm.is_available() else "mock", len(text),
        )
        return {"topic": topic, "mode": mode, "text": text, "word_count": len(text)}

    def _compose(self, topic: str, mode: str = "essay") -> str:
        # ---- v3：真实 LLM（配置了 LLM_API_KEY 时）----
        if self.llm.is_available():
            return self.llm.generate(self._build_prompt(topic, mode))

        # ---- v2：mock 降级（按模式 + 分类给差异化模板）----
        if mode == "outline":
            return (
                f"《{topic}》大纲\n"
                f"一、背景：为什么要关注{topic}\n"
                f"二、核心要点：三个关键角度\n"
                f"三、实践建议：怎么落地"
            )
        if mode == "summary":
            return (
                f"【{topic}】总结\n"
                f"- 核心结论：{topic}值得持续关注\n"
                f"- 关键信息：三点速览\n"
                f"- 行动建议：先小步实践"
            )
        # essay：按分类给差异化模板
        category = classify_topic(topic)
        body = TEMPLATES.get(category, f"{topic}是值得深入了解的话题，建议从多个角度展开。")
        text = (
            f"关于「{topic}」的短文\n"
            f"概述：{topic}是一个{('值得深入研究' if category != 'default' else '有意思')}的话题。\n"
            f"要点：\n{body}"
        )
        if self._revision_hint:
            text += (
                f"\n结论：综上所述，关于{topic}的学习是一个持续积累的过程。"
                f"本次修订针对：{self._revision_hint}。"
            )
        return text

    def _build_prompt(self, topic: str, mode: str = "essay") -> str:
        """按模式拼 LLM prompt（真实模型使用）。"""
        mode_prompts = {
            "outline": (
                f"请为「{topic}」写一份中文大纲，第一行用《{topic}》大纲做标题，"
                f"用 一、二、三 分节，每节 2 行以内，包含背景、核心要点、实践建议，"
                f"最后给出{self._revision_hint or '一点学习建议'}。"
            ),
            "summary": (
                f"请用 150 字以内总结「{topic}」，第一行用【{topic}】总结做标题，"
                f"用 - 列表给出：核心结论、关键信息、行动建议三条，"
                f"并附上{self._revision_hint or '一句延伸思考'}。"
            ),
            "essay": (
                f"请写一篇 200 字以内的中文短文，主题是「{topic}」，"
                f"必须包含「概述、要点、结论」三个部分，"
                f"并给出{self._revision_hint or '三点具体建议'}。"
            ),
        }
        return mode_prompts.get(mode, mode_prompts["essay"])