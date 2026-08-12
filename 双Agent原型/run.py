"""项目启动器：Writer + Reviewer 双 Agent 写作流水线（交互式三层菜单）。

菜单结构：
    第一层：引擎选择（真实大模型 / mock）
    第二层：输出格式选择（短文 / 大纲 / 总结）
    第三层：主题输入循环

任意一层输入 "0" 或 "退出" 都返回上一层；最深层退出整个程序。
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.flow import run_writer_reviewer_flow  # noqa: E402
from src.llm import LLMClient  # noqa: E402

EXIT_WORDS = ("退出", "exit", "quit", "q")

# 输出格式菜单
MODES = {
    "1": {"key": "essay", "name": "写短文（概述+要点+结论）"},
    "2": {"key": "outline", "name": "写大纲（背景+要点+建议）"},
    "3": {"key": "summary", "name": "写总结（结论+信息+行动）"},
}
MODE_NAMES = {"essay": "写短文", "outline": "写大纲", "summary": "写总结"}


def _is_exit(s: str) -> bool:
    """判断输入是否表示"退出当前层"。"""
    return s == "0" or s.lower() in EXIT_WORDS


def run_once(topic: str, mode: str, llm: LLMClient | None) -> None:
    """跑一次写作流水线（用指定 LLM 客户端）。"""
    result = run_writer_reviewer_flow(topic, mode=mode, llm_client=llm)

    print(f"主题：{topic}（模式：{MODE_NAMES.get(mode, mode)}）")

    if result.get("refused"):
        print(f"✘ 拒绝：{result['refused_reason']}")
        print("-" * 40)
        return

    print(f"最终状态: {'✔ 审查通过' if result['passed'] else '✘ 未在轮次内通过'}")
    for r in result["rounds"]:
        print(f"  第{r['round']}轮: passed={r['passed']} score={r['score']} 意见={r['comments']}")
    print("\n最终稿：")
    print(result["final_text"])
    print("-" * 40)


def show_api_info(llm: LLMClient) -> None:
    """选完引擎后展示 API 配置状态。"""
    print()
    print(llm.format_status())
    print()


# =================== 三层菜单 ===================
def loop_engine() -> str | None:
    """第一层：选引擎（真实大模型 / mock / 退出）。返回 use_llm 或 None（退出）。"""
    while True:
        print("┌────────────────────────────────────────┐")
        print("│  引擎选择                              │")
        print("│  1. 真实大模型（按 .env / 环境变量配置）│")
        print("│  2. mock 规则模板（无需 key、无网络）   │")
        print("│  0 / 退出 → 结束                       │")
        print("└────────────────────────────────────────┘")
        choice = input("> ").strip()
        if _is_exit(choice):
            return None
        if choice == "1":
            return "llm"
        if choice == "2":
            return "mock"
        print("没这个选项\n")


def loop_mode(use_llm: str) -> bool:
    """第二层：选输出格式。返回 False 表示返回引擎菜单。"""
    while True:
        print("┌────────────────────────────────────────┐")
        print(f"  当前引擎：{use_llm}")
        print("│  请选择输出格式                        │")
        for key, info in MODES.items():
            print(f"│  {key}. {info['name']}")
        print("│  0 / 退出 → 返回引擎选择               │")
        print("└────────────────────────────────────────┘")
        choice = input("> ").strip()
        if _is_exit(choice):
            return False
        if choice not in MODES:
            print("没这个选项\n")
            continue
        mode = MODES[choice]["key"]
        # 选了格式后进主题循环
        loop_topic(mode, use_llm)
        # 主题循环退出后回到这里（继续选格式）


def loop_topic(mode: str, use_llm: str) -> None:
    """第三层：输入主题循环。输入 0/退出 返回上一层。"""
    # 根据引擎选择创建 LLMClient（显式 provider 覆盖 env）
    llm = LLMClient(provider=use_llm)
    print(f"\n当前：引擎={use_llm}，格式={MODE_NAMES[mode]}")
    print("输入主题开始写作（输入「退出」或 0 返回上层）\n")

    while True:
        try:
            topic = input("主题> ").strip()
        except EOFError:
            return
        if _is_exit(topic):
            print()
            return
        if not topic:
            continue
        run_once(topic, mode=mode, llm=llm)


def interactive() -> int:
    """交互模式入口。"""
    print("=" * 42)
    print("  双 Agent 写作流水线 · 交互演示")
    print("=" * 42)

    while True:
        use_llm = loop_engine()
        if use_llm is None:
            print("拜拜~")
            return 0

        # 选了真实大模型 → 显示 API 配置信息
        if use_llm == "llm":
            show_api_info(LLMClient(provider="llm"))

        loop_mode(use_llm)
        # 循环回到引擎菜单


if __name__ == "__main__":
    # 单次模式：run.py "主题" [模式]   默认 essay + llm（看 env）
    if len(sys.argv) > 1:
        mode = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in MODE_NAMES else "essay"
        run_once(sys.argv[1], mode=mode, llm=LLMClient())
        sys.exit(0)

    sys.exit(interactive())