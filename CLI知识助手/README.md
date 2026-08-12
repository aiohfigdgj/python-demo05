# 任务02 · CLI 知识助手

> 支持命令行参数（argparse），无硬编码敏感信息。

## 功能

### ① 对话模式（推荐，有"自主性"）

```bash
python run.py        # 没参数 → 直接进入对话模式
```

输入自然语言，程序自己判断干什么：

```
> 添加：Python / 是一门编程语言 / 编程,python
✔ 已导入 #1: Python（标签: ['编程', 'python']）
> 什么是 Python？
共 1 条结果：
  #1 [Python] 是一门编程语言
> 列表
共 1 条知识：
  #1 Python | 标签: ['编程', 'python']
> 删除：1
✔ 已删除 #1
> 退出
```

支持的说法：`添加：标题 / 内容 / 标签`、`什么是X？`/`查：X`/`搜索 X`、
`列表`、`删除：id`、`帮助`、`退出`——意图解析在 `src/intent.py`。

### ② 参数模式（验收要求：argparse 命令行参数）

```
python -m src.main import --title "Python" --content "简介" --tags "编程,python"
python -m src.main query  --keyword python
python -m src.main list
python -m src.main delete --id 3
```

## 目录结构

```
02-CLI知识助手/
├── run.py                   # 🚀 启动器：没参数 = 对话模式
├── src/
│   ├── main.py              # argparse 参数解析 + 命令分发 + 对话循环
│   ├── intent.py            # 意图解析（自然语言 → 动作，自主性核心）
│   └── knowledge_store.py   # 知识库（JSON 存储，增删查/关键词搜索）
├── config/.env.example      # 环境变量示例（敏感信息走这里，不进代码）
├── tests/
│   ├── test_cli.py          # 存储/中文/边界 + CLI 参数解析测试
│   └── test_intent.py       # 意图解析测试（不同输入 → 正确动作）
├── pytest.ini
└── requirements.txt
```

## 无硬编码敏感信息怎么做到的

1. **代码里没有任何密钥**：知识助手是纯本地规则，未来接 LLM 的密钥
   通过 `${LLM_API_KEY}` 环境变量注入（见 `config/.env.example`）
2. **路径也不写死**：知识库文件位置可用环境变量 `MY_KNOWLEDGE_FILE` 覆盖
3. **优先级**：环境变量 > 代码默认值——这正是 Day2 的
   "配置优先级：CLI > 环境变量 > 配置文件 > 默认值" 思想的落地

## 运行

```bash
pip install -r requirements.txt

# ★ 最简单：run.py 启动器（没参数 = 打印帮助）
python run.py import --title "Python" --content "Python 是一门简洁易学的编程语言" --tags "编程,python"
python run.py query --keyword 编程
python run.py list
python run.py delete --id 1

# 等价写法（工程规范：包模式）
python -m src.main import --title "Python" --content "..." --tags "编程"

python -m pytest        # 测试
```
