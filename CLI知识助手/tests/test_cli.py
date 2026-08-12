# 测试：CLI 知识助手（知识库增删查 / 中文 / 文件不存在 / 持久化）。

import pytest

from src.knowledge_store import KnowledgeStore
from src.main import build_parser, main


# ---------------- 知识库存储 ----------------
def test_add_and_count(tmp_path):
    store = KnowledgeStore(tmp_path / "kb.json")
    assert store.count() == 0
    store.add("Python", "Python 是一门编程语言", ["编程"])
    store.add("测试", "pytest 是测试框架", ["编程", "测试"])
    assert store.count() == 2


def test_search_chinese_content(tmp_path):
    store = KnowledgeStore(tmp_path / "kb.json")
    store.add("Python", "Python 是一门简洁的编程语言", ["编程", "python"])
    store.add("深圳", "深圳大学龙虾工作室", ["学校"])

    assert len(store.search("编程")) == 1
    assert len(store.search("深圳大学")) == 1
    assert len(store.search("python")) == 1  # 大小写不敏感
    assert len(store.search("不存在的词")) == 0


def test_search_empty_keyword(tmp_path):
    store = KnowledgeStore(tmp_path / "kb.json")
    store.add("A", "内容A")
    assert store.search("  ") == []


def test_chinese_content_persisted(tmp_path):
    """中文写入 JSON 后仍可读回（ensure_ascii=False）。"""
    path = tmp_path / "kb.json"
    store = KnowledgeStore(path)
    store.add("中文标题", "中文内容：测试", ["标签一"])
    raw = path.read_text(encoding="utf-8")
    assert "中文标题" in raw  # 文件里直接可见中文，不是 \uXXXX

    store2 = KnowledgeStore(path)  # 模拟重启
    assert store2.count() == 1
    assert store2.list_all()[0]["title"] == "中文标题"


def test_file_not_exist_handling(tmp_path):
    """文件不存在时：列表为空、可正常添加。"""
    store = KnowledgeStore(tmp_path / "不存在的目录" / "kb.json")
    assert store.count() == 0
    assert store.list_all() == []
    store.add("新建", "自动创建目录与文件")
    assert store.count() == 1


def test_delete_existing_and_missing(tmp_path):
    store = KnowledgeStore(tmp_path / "kb.json")
    entry = store.add("将被删除", "内容")
    assert store.delete(entry["id"]) is True
    assert store.count() == 0
    assert store.delete(999) is False


# ---------------- CLI 参数解析 ----------------
def test_parser_requires_action():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_parser_import_requires_title_and_content():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["import"])  # 缺 --title / --content


def test_parser_accepts_valid_import():
    args = build_parser().parse_args(
        ["import", "--title", "Python", "--content", "简介", "--tags", "编程,python"]
    )
    assert args.action == "import"
    assert args.title == "Python"


# ---------------- CLI 主流程（用临时知识库文件）----------------
def test_cli_import_query_list_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_KNOWLEDGE_FILE", str(tmp_path / "kb.json"))

    assert main(["import", "--title", "二分查找", "--content", "算法复杂度 O(log n)", "--tags", "算法"]) == 0
    assert main(["import", "--title", "Python", "--content", "简洁的编程语言", "--tags", "编程"]) == 0

    # query
    assert main(["query", "--keyword", "算法"]) == 0

    # list
    assert main(["list"]) == 0

    # 删除不存在的 id 不应报错（argparse 的 argv 元素必须是字符串）
    assert main(["delete", "--id", "999"]) == 0
