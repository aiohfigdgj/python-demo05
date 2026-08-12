"""测试：意图解析（对话模式的"自主性"核心）。

覆盖：添加/查询/删除/列表/帮助/退出/听不懂 各种说法。
"""
import pytest

from src.intent import parse_intent


def test_parse_add():
    intent = parse_intent("添加：Python / 是一门编程语言 / 编程,python")
    assert intent["action"] == "import"
    assert intent["title"] == "Python"
    assert intent["content"] == "是一门编程语言"
    assert intent["tags"] == ["编程", "python"]


def test_parse_add_variants():
    assert parse_intent("新增：二分查找 / O(log n) / 算法")["action"] == "import"
    assert parse_intent("导入：递归 / 函数调用自身")["action"] == "import"
    # 没有标签也 OK
    intent = parse_intent("添加：递归 / 函数调用自身")
    assert intent["action"] == "import"
    assert intent["tags"] == []


@pytest.mark.parametrize(
    "text,keyword",
    [
        ("什么是 Python？", "Python"),
        ("查：算法", "算法"),
        ("搜索 二分查找", "二分查找"),
        ("介绍一下递归", "递归"),
        ("帮我查 数据结构", "数据结构"),
    ],
)
def test_parse_query(text, keyword):
    intent = parse_intent(text)
    assert intent["action"] == "query"
    assert intent["keyword"] == keyword


def test_parse_list():
    for text in ("列表", "列出", "全部", "list"):
        assert parse_intent(text)["action"] == "list"


def test_parse_delete():
    intent = parse_intent("删除：3")
    assert intent["action"] == "delete"
    assert intent["id"] == 3
    assert parse_intent("删掉 id=7")["id"] == 7


def test_parse_delete_without_id():
    intent = parse_intent("删除")
    assert intent["action"] == "unknown"


def test_parse_help_and_exit():
    assert parse_intent("帮助")["action"] == "help"
    assert parse_intent("退出")["action"] == "exit"
    assert parse_intent("q")["action"] == "exit"


def test_parse_unknown():
    intent = parse_intent("今天天气真不错")
    assert intent["action"] == "unknown"
