# 任务07 · 配置管理系统

> 支持 dev / prod / test 三套配置**热切换**。

## 核心能力

1. **三套配置**：`config/dev.yaml`（模拟数据）、`prod.yaml`（真实 wttr.in）、
   `test.yaml`（模拟 + 隔离路径）
2. **无硬编码密钥**：敏感信息用 `${LLM_API_KEY}` 占位，
   运行时从环境变量注入——代码与配置文件里零密钥
3. **热切换**：`get_config("prod")` / `switch_env("prod")` 运行时立即生效，
   **无需重启进程**
4. **优先级**：显式指定(CLI/参数) > 环境变量 `MY_AGENT_ENV` > 默认值 `dev`
5. **环境隔离**：三套环境的缓存文件/知识库路径各自独立，互不污染

## 目录结构

```
07-配置管理系统/
├── config/
│   ├── dev.yaml        # 开发：mock 模拟数据
│   ├── prod.yaml       # 生产：wttr.in 真实接口 + 独立缓存
│   ├── test.yaml       # 测试：mock + 隔离存储
│   └── .env.example    # 环境变量示例（密钥放这里，不进代码）
├── src/
│   ├── config.py       # Config / ConfigManager / 热切换 / ${ENV} 注入
│   ├── toolbox.py      # 配置驱动的工具演示（查天气：mock vs wttr）
│   └── demo.py         # 一次性演示：三环境热切换
├── tests/
│   ├── test_config.py  # 配置加载/热切换/注入/优先级
│   └── test_toolbox.py # 配置驱动行为测试
├── pytest.ini
└── requirements.txt
```

## 运行

```bash
pip install -r requirements.txt
python -m pytest          # 测试（20 个全通过）
python run.py             # ★ 交互模式（推荐）
python run.py prod        # 单次：查看指定环境配置
```

## 交互演示（重点：配置驱动行为）

```text
当前环境: dev
  天气数据源: mock  日志级别: DEBUG
 1. 热切换环境（dev / prod / test）
 2. 查看当前配置
 3. 查天气（用当前环境的数据源！）   ← 关键
 0. 退出
> 3
城市: 深圳
[dev][mock] 深圳 晴 28℃ 湿度65%      ← dev 用模拟数据

> 1 → 切到 prod
> 3
城市: 深圳
[prod][wttr] 深圳 Sunny 31℃ 湿度79%  ← 同一个命令，真实接口！
```

**同一条"查天气"命令，环境不同行为不同**——这就是热切换的价值：不用重启，
配置一变，行为立刻跟着变。

## 演示输出

```
=== 配置管理系统演示：dev / prod / test 热切换 ===
--- 环境: dev ---
  天气数据源   : mock
  缓存文件     : data/weather_cache.json
  日志级别     : DEBUG
  LLM 密钥     : None（未设置时为 None）
--- 环境: prod ---
  天气数据源   : wttr
  缓存文件     : data/weather_cache_prod.json
...
结论：无需重启进程，get_config(env) 即热切换，密钥来自环境变量而非硬编码。
```

