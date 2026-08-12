"""测试：Writer + Reviewer 双 Agent 流水线（修订循环 / 停止条件）。"""
from src.flow import run_writer_reviewer_flow
from src.reviewer import ReviewerAgent
from src.writer import WriterAgent


def test_flow_ends_passed():
    """默认最多 3 轮内应通过审查，且最终稿非空。"""
    result = run_writer_reviewer_flow("Python 学习")
    assert result["passed"] is True
    assert result["rounds"], "应有至少一轮评审记录"
    assert result["rounds"][-1]["passed"] is True
    assert result["final_text"]
    assert result["final_word_count"] > 0


def test_flow_uses_revision():
    """第一轮缺结论被拒 → 意见反馈 → 修订后补上结论。"""
    result = run_writer_reviewer_flow("机器学习")
    first_round = result["rounds"][0]
    assert first_round["passed"] is False
    assert "结论" in "".join(first_round["comments"])
    # 修订后的最终稿包含结论段落
    assert "结论：" in result["final_text"]


def test_flow_max_rounds_stops():
    """max_rounds=1 时第一轮不过则直接结束，不继续修订。"""
    result = run_writer_reviewer_flow("数据库", max_rounds=1)
    assert len(result["rounds"]) == 1
    assert result["passed"] is False  # 第一轮必然缺结论


def test_writer_accepts_revision():
    writer = WriterAgent()
    writer.set_revision(["包含结论段落"])
    draft = writer.write("主题")
    assert "结论：" in draft["text"]


def test_reviewer_flags_short_draft():
    reviewer = ReviewerAgent()
    review = reviewer.review({"text": "太短了", "word_count": 3})
    assert review["passed"] is False
    assert "字数" in "".join(review["comments"])


def test_reviewer_passes_good_draft():
    reviewer = ReviewerAgent()
    draft = {"text": "概述：好内容\n要点：细节\n结论：综上", "word_count": 50}
    review = reviewer.review(draft)
    assert review["passed"] is True
    assert review["score"] == 100.0


# ---------------- 主题预审：安全护栏（Day5 安全意识）----------------
def test_writer_should_refuse_sensitive_topics():
    """明显不适合的主题应被预审拒绝。"""
    writer = WriterAgent()
    for bad in ("性爱", "毒品", "裸聊", "约炮"):
        reason = writer.should_refuse(bad)
        assert reason is not None
        assert "敏感" in reason or "不适合" in reason


def test_writer_accepts_normal_topics():
    """正常学习/技术话题应通过预审。"""
    writer = WriterAgent()
    for topic in ("Python 学习", "机器学习算法", "数据库设计"):
        assert writer.should_refuse(topic) is None


def test_writer_refuses_short_topic():
    writer = WriterAgent()
    assert writer.should_refuse("") is not None
    assert writer.should_refuse("A") is not None  # 单字符太短


def test_flow_refuses_sensitive_topic_without_writing():
    """不合法主题 → refused=True，不进入流水线、无最终稿。"""
    result = run_writer_reviewer_flow("性爱")
    assert result["refused"] is True
    assert result["passed"] is False
    assert result["rounds"] == []
    assert result["final_text"] == ""
    assert "敏感" in result["refused_reason"]


def test_flow_normal_topic_works():
    """正常主题：refused=False，正常通过流水线。"""
    result = run_writer_reviewer_flow("Python 学习")
    assert result["refused"] is False
    assert result["passed"] is True


# ---------------- v2 升级：差异化内容 ----------------
def test_writer_different_categories_yield_different_content():
    """不同分类的主题应生成不同内容（v2 升级点）。"""
    writer = WriterAgent()
    a = writer.write("Python 学习")["text"]
    b = writer.write("晚清历史")["text"]
    c = writer.write("汉堡制作")["text"]
    # 三个内容两两不同
    assert a != b
    assert b != c
    assert a != c
    # 各自包含分类特征词
    assert "概念" in a or "代码" in a  # 学习技术类
    assert "时间线" in b or "人物" in b  # 历史人文类
    assert "原料" in c or "火候" in c  # 生活美食类


def test_writer_same_topic_yields_same_content():
    """同一主题输出应稳定（可复现性）。"""
    writer = WriterAgent()
    a = writer.write("机器学习")
    b = writer.write("机器学习")
    assert a["text"] == b["text"]


def test_classify_topic():
    from src.writer import classify_topic

    assert classify_topic("Python 学习") == "学习技术"
    assert classify_topic("晚清历史") == "历史人文"
    assert classify_topic("汉堡制作") == "生活美食"
    assert classify_topic("数据库设计") == "工程技术"
    assert classify_topic("随便聊聊") == "default"


# ---------------- v4 升级：多模式（短文/大纲/总结）----------------
def test_writer_modes_produce_different_content():
    """同一主题，三种模式输出格式不同。"""
    writer = WriterAgent()
    essay = writer.write("Python 学习", mode="essay")["text"]
    outline = writer.write("Python 学习", mode="outline")["text"]
    summary = writer.write("Python 学习", mode="summary")["text"]

    assert essay != outline != summary
    assert "大纲" in outline
    assert "总结" in summary


def test_flow_outline_mode_passes():
    """大纲模式：Reviewer 按大纲结构检查，应通过。"""
    result = run_writer_reviewer_flow("机器学习", mode="outline")
    assert result["refused"] is False
    assert result["passed"] is True
    assert "大纲" in result["final_text"]


def test_flow_summary_mode_passes():
    result = run_writer_reviewer_flow("数据库设计", mode="summary")
    assert result["passed"] is True
    assert "总结" in result["final_text"]


def test_reviewer_mode_specific_checks():
    """Reviewer 按模式检查：outline 不要求"概述"，summary 不要求"结论段落"。"""
    reviewer = ReviewerAgent()
    # 大纲稿：没有"概述"但有大纲结构 → 应通过
    outline_review = reviewer.review(
        {"text": "《主题》大纲\n一、背景\n二、核心要点\n三、实践建议", "word_count": 40},
        mode="outline",
    )
    assert outline_review["passed"] is True
    # 总结稿：没有"概述"但有总结结构 → 应通过
    summary_review = reviewer.review(
        {"text": "【主题】总结\n- 核心结论：\n- 关键信息：\n- 行动建议：", "word_count": 40},
        mode="summary",
    )
    assert summary_review["passed"] is True
