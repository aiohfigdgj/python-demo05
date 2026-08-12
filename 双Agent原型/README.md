# 任务06 · 双 Agent 原型（Writer + Reviewer）

> Writer + Reviewer 工作流原型：写作 → 审查 → 修订循环。

## 工作流

```
┌─────────┐   草稿    ┌─────────┐
│ Writer  │ ────────▶ │ Reviewer│
└─────────┘           └────┬────┘
     ▲                     │ 通过？──是──▶ 定稿 ✔
     │ 修订意见（comments）  │ 否
     └─────────────────────┘

↑ 流水线前先经过【主题预审】，不合规直接拒绝（不再写作）
```

## 主题预审（安全护栏 / Day5 安全意识）

`Writer.should_refuse(topic)` 在写之前先检查主题是否适合，明显不合适的主题（色情/暴力/违法等）
直接拒绝、给出原因，不会进入流水线。生产环境的 Agent 不能对任何输入都照做——这是
**安全意识**的最小实现。

## 目录结构

```
06-双Agent原型/
├── src/
│   ├── writer.py     # Writer：按主题写作，可接收意见修订（LLM/mock 双引擎）
│   ├── reviewer.py   # Reviewer：检查字数/结构/敏感词，打分给意见
│   ├── llm.py        # LLM 客户端（OpenAI 兼容接口，无 key 自动降级 mock）
│   └── flow.py       # 流水线编排（含命令行直接运行）
├── .env.example   # LLM 配置示例（密钥走环境变量，零硬编码）
├── tests/
│   ├── test_flow.py  # 流水线/预审/差异化内容测试
│   └── test_llm.py   # LLM 客户端测试（Mock 成功/失败/降级）
├── pytest.ini
└── requirements.txt
```

## 运行

```bash
pip install -r requirements.txt
python run.py                     # ★ 交互模式：先选模式（短文/大纲/总结），再输入主题
python run.py "机器学习"          # 单次模式（默认写短文）
python run.py "机器学习" outline  # 单次模式（指定 essay/outline/summary）
python -m pytest                  # 测试（25 个全通过）
# 等价写法：python -m src.flow "主题"
```

### 三种模式

| 模式 | 输出 | 适合 |
|------|------|------|
| `essay`（短文） | 概述 + 要点 + 结论 | 科普短文 |
| `outline`（大纲） | 背景 + 核心要点 + 实践建议 | 学习计划/文章框架 |
| `summary`（总结） | 核心结论 + 关键信息 + 行动建议 | 资料速读/汇报 |

Reviewer 会**按模式检查结构**：大纲稿不要求"概述"，总结稿不要求"结论段落"——模式不同，审查标准不同。

## 接入真实 LLM（可选加分项）

Writer 支持 **mock / llm 双引擎**，通过环境变量切换，密钥零硬编码：

```bash
# 复制示例并配置（06-双Agent原型/.env.example → 项目根 .env）
LLM_PROVIDER=llm                  # mock（默认）| llm（真实模型）
LLM_API_KEY=sk-xxxx               # 你的 API Key
LLM_BASE_URL=https://api.openai.com/v1   # 可换 DeepSeek/智谱等兼容服务
LLM_MODEL=gpt-3.5-turbo           # 按服务调整

python run.py                     # 启动时显示当前引擎
```

- **没配 key** → 自动降级 mock 分类模板，程序照常运行（优雅降级）
- **配了 key** → Writer 用真实大模型生成，Reviewer 照常审查修订
- 请求失败也不会 crash，返回提示信息

对应学习计划 Q5："能接 API 加分"——架构支持了，接不接看你的 key。

## 多 Agent 设计原则（Day5 要点）

1. **职责边界清晰**：Writer 只写不评，Reviewer 只评不改
2. **输入输出 schema 统一**：
   - 草稿：`{"topic", "text", "word_count"}`
   - 评审：`{"passed", "score", "comments", "word_count"}`
3. **明确停止条件**：审查通过 或 达到 max_rounds
4. **为什么需要多 Agent**：写作需要"产出能力"与"批判能力"，单 Agent
   难以同时兼顾深度专家型和广度通用型——分工让每个角色更专注

## 实测效果

```
最终状态: ✔ 审查通过
  第1轮: passed=False score=85.0 意见=['包含结论段落']
  第2轮: passed=True score=100.0 意见=['内容完整，可以定稿']
```
