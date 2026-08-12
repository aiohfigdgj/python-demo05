"""CLI 知识助手：命令行参数解析 + 知识库管理。

无硬编码敏感信息：代码中不出现任何密钥，密钥等敏感信息一律走环境变量。

用法（在项目根目录运行）：
    python -m src.main import --title "Python" --content "..." --tags "编程,python"
    python -m src.main query --keyword python
    python -m src.main list
    python -m src.main delete --id 3
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .knowledge_store import KnowledgeStore

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 知识库存放位置（默认路径；可通过环境变量 MY_KNOWLEDGE_FILE 覆盖）
DEFAULT_STORE = "data/knowledge.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="knowledge-cli",
        description="CLI 知识助手：导入 / 查询 / 列出 / 删除知识条目",
    )
    parser.add_argument("--verbose", action="store_true", help="输出 DEBUG 日志")

    sub = parser.add_subparsers(dest="action", required=True, metavar="操作")

    # import：导入一条知识
    imp = sub.add_parser("import", help="导入一条知识")
    imp.add_argument("--title", required=True, help="标题（必填）")
    imp.add_argument("--content", required=True, help="内容（必填）")
    imp.add_argument("--tags", default="", help="标签，逗号分隔，如: 编程,python")

    # query：按关键词查询
    q = sub.add_parser("query", help="按关键词查询")
    q.add_argument("--keyword", required=True, help="搜索关键词")

    sub.add_parser("list", help="列出全部条目")

    # delete：按 id 删除
    d = sub.add_parser("delete", help="按 id 删除")
    d.add_argument("--id", type=int, required=True, help="条目 id")

    # chat：对话模式（自主理解输入）
    sub.add_parser("chat", help="对话模式：直接输入自然语言，程序自己判断干什么")

    return parser


# 对话模式的帮助文本
HELP_TEXT = """我可以帮你管理知识库，试试这样说：
  添加：Python / 是一门编程语言 / 编程,python    （导入知识）
  什么是 Python？ / 查：算法 / 搜索 二分查找        （查询知识）
  列表                                           （列出全部）
  删除：3                                        （按编号删除）
  帮助 / 退出"""


def get_store() -> KnowledgeStore:
    """知识库文件路径：环境变量 > 默认值（配置可覆盖，不硬编码死路径）。"""
    path = os.getenv("MY_KNOWLEDGE_FILE", str(PROJECT_ROOT / DEFAULT_STORE))
    return KnowledgeStore(path)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    store = get_store()

    if args.action == "chat":
        return chat(store)

    if args.action == "import":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        entry = store.add(args.title, args.content, tags)
        print(f"✔ 已导入 #{entry['id']}: {entry['title']}（标签: {entry['tags']}）")

    elif args.action == "query":
        results = store.search(args.keyword)
        if not results:
            print(f"未找到与「{args.keyword}」相关的内容")
            return 0
        print(f"共 {len(results)} 条结果：")
        for e in results:
            print(f"  #{e['id']} [{e['title']}] {e['content'][:60]}")

    elif args.action == "list":
        entries = store.list_all()
        if not entries:
            print("知识库为空，请先用 import 导入")
            return 0
        print(f"共 {len(entries)} 条知识：")
        for e in entries:
            print(f"  #{e['id']} {e['title']} | 标签: {e['tags']}")

    elif args.action == "delete":
        ok = store.delete(args.id)
        print(f"✔ 已删除 #{args.id}" if ok else f"✘ 不存在 id={args.id} 的条目")

    return 0


def chat(store: KnowledgeStore) -> int:
    """对话模式：输入自然语言，程序自主判断干什么（不依赖参数）。"""
    from .intent import parse_intent

    print("=" * 40)
    print("  知识助手 · 对话模式")
    print("=" * 40)
    print(HELP_TEXT)
    print("-" * 40)

    while True:
        try:
            text = input("> ").strip()
        except EOFError:  # Ctrl+D / 管道输入结束
            break
        if not text:
            continue

        intent = parse_intent(text)
        action = intent["action"]

        if action == "exit":
            print("拜拜~")
            break
        elif action == "help":
            print(HELP_TEXT)
        elif action == "unknown":
            print(f"没听懂（{intent.get('reason', '输入' + text[:20])}），输入「帮助」看看我能做什么")
        elif action == "import":
            entry = store.add(intent["title"], intent["content"], intent["tags"])
            print(f"✔ 已导入 #{entry['id']}: {entry['title']}（标签: {entry['tags']}）")
        elif action == "query":
            results = store.search(intent["keyword"])
            if not results:
                print(f"未找到与「{intent['keyword']}」相关的内容")
            else:
                print(f"共 {len(results)} 条结果：")
                for e in results:
                    print(f"  #{e['id']} [{e['title']}] {e['content'][:60]}")
        elif action == "list":
            entries = store.list_all()
            if not entries:
                print("知识库为空，先添加一条试试，例如：添加：Python / 是一门语言 / 编程")
            else:
                print(f"共 {len(entries)} 条知识：")
                for e in entries:
                    print(f"  #{e['id']} {e['title']} | 标签: {e['tags']}")
        elif action == "delete":
            ok = store.delete(intent["id"])
            print(f"✔ 已删除 #{intent['id']}" if ok else f"✘ 不存在 id={intent['id']} 的条目")

    return 0


if __name__ == "__main__":
    sys.exit(main())
