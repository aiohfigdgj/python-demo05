"""双 Agent 写作流水线：Writer → Reviewer →（不通过则）Revise。

    ┌─────────┐   草稿    ┌─────────┐
    │ Writer  │ ────────▶ │ Reviewer│
    └─────────┘           └────┬────┘
         ▲                     │ 通过？──是──▶ 定稿
         │ 修订意见（comments）  │ 否
         └─────────────────────┘

设计原则：
1. 职责边界清晰：Writer 只写、Reviewer 只评
2. 输入输出 schema 统一：草稿 dict {"topic","text","word_count"}，
   评审 dict {"passed","score","comments",...}
3. 明确停止条件：通过 或 达到 max_rounds
"""
from __future__ import annotations

import logging

from .reviewer import ReviewerAgent
from .writer import WriterAgent

log = logging.getLogger(__name__)


def run_writer_reviewer_flow(
    topic: str,
    mode: str = "essay",
    max_rounds: int = 3,
    llm_client=None,
) -> dict:
    """执行写作流水线，返回结果 dict。

    参数：
        topic: 主题
        mode: essay=短文 / outline=大纲 / summary=总结
        max_rounds: 最大修订轮次
        llm_client: 可选，外部注入的 LLM 客户端（不传则 WriterAgent 默认创建）

    返回：
        {
            "passed": bool,          # 是否在轮次内通过审查
            "refused": bool,         # 是否在主题预审阶段被拒绝
            "refused_reason": str,   # 拒绝原因（refused=True 时有值）
            "rounds": [{"round","passed","score","comments"}, ...],
            "final_text": str,       # 最终稿
            "final_word_count": int,
        }

    【安全护栏】写入前先做主题预审；不合适的主题直接拒绝，不进入流水线。
    """
    writer = WriterAgent(llm=llm_client)
    reviewer = ReviewerAgent()

    # 主题预审：不合规直接拒绝，不写作
    refuse_reason = writer.should_refuse(topic)
    if refuse_reason:
        log.warning("流水线 主题被拒绝: %s", refuse_reason)
        return {
            "passed": False,
            "refused": True,
            "refused_reason": refuse_reason,
            "rounds": [],
            "final_text": "",
            "final_word_count": 0,
        }

    draft = None
    rounds_log: list[dict] = []
    passed = False

    for round_no in range(1, max_rounds + 1):
        draft = writer.write(topic, mode=mode)
        review = reviewer.review(draft, mode=mode)
        rounds_log.append(
            {
                "round": round_no,
                "passed": review["passed"],
                "score": round(review["score"], 1),
                "comments": review["comments"],
            }
        )
        log.info(
            "流水线 第%s轮: passed=%s score=%s comments=%s",
            round_no, review["passed"], review["score"], review["comments"],
        )
        if review["passed"]:
            passed = True
            break
        # 未通过：带着意见进入下一轮修订
        writer.set_revision(review["comments"])

    return {
        "passed": passed,
        "refused": False,
        "refused_reason": "",
        "rounds": rounds_log,
        "final_text": draft["text"] if draft else "",
        "final_word_count": draft["word_count"] if draft else 0,
    }


if __name__ == "__main__":
    # 命令行直接运行：python src/flow.py "主题"
    import sys

    topic = sys.argv[1] if len(sys.argv) > 1 else "Python 学习"
    result = run_writer_reviewer_flow(topic)
    print(f"最终状态: {'✔ 审查通过' if result['passed'] else '✘ 未在轮次内通过'}")
    for r in result["rounds"]:
        print(f"  第{r['round']}轮: passed={r['passed']} score={r['score']} 意见={r['comments']}")
    print("\n最终稿：")
    print(result["final_text"])
