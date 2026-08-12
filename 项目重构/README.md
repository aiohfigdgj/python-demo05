# 任务01 · 项目重构

> 把"之前项目"（天气小工具）重构为规范目录结构。

## 重构前 vs 重构后

| | 位置 | 说明 |
|---|------|------|
| 重构前 | `legacy/old_weather_v1.py` | 原始版本：交互菜单、缓存、校验全在一个文件 |
| 重构后 | `src/` | 按 数据层 / 业务层 / 展示层 分层 |

## 目录结构（重构后）

```
01-项目重构/
├── legacy/old_weather_v1.py   # 重构前旧版（对照）
├── src/
│   ├── main.py                # 展示层 + 入口（argparse 参数化）
│   ├── weather.py             # 业务层（城市校验 + 带缓存的查询流程）
│   └── tools/
│       ├── cache.py           # 数据层（JSON 缓存 + TTL）
│       └── fetcher.py         # 数据源层（mock / wttr.in）
├── config/config.json         # 配置（数据源/超时/缓存参数，不再硬编码）
├── tests/test_refactor.py     # 测试（校验/缓存/接口 Mock/异常分级）
├── pytest.ini
└── requirements.txt
```

## 重构改进对照

| 旧版问题 | 新版改进 |
|---------|---------|
| 缓存路径/有效期/请求头硬编码 | `config/config.json` 配置驱动 |
| 交互菜单 input() 循环，无法脚本化 | `--city / --cities / --cache / --clear-cache` 参数 |
| 业务+展示全挤一个文件 | 数据层 / 业务层 / 展示层分离 |
| print 输出 | logging 分级 + 请求耗时/状态码 |
| 数据源写死 | `--provider mock|wttr` 可切换 |

功能**全部保留**：单城市、批量表格、缓存查看与清除、城市名校验、
低温提醒、交互菜单模式（`--interactive`）。

## 快速开始

```bash
pip install -r requirements.txt

# 真实接口（wttr.in，免费无需密钥）
python -m src.main --city 深圳
# 模拟数据（调试用，不访问网络）
python -m src.main --provider mock --city 深圳
# 批量查询
python -m src.main --cities "深圳,北京,上海"
# 缓存管理
python -m src.main --cache
python -m src.main --clear-cache
# 旧版交互菜单体验
python -m src.main --interactive

# 测试
python -m pytest
```

> 💡 **不想用 `-m`？直接用 `run.py` 启动器**（推荐）：
> ```bash
> python run.py                    # 没参数 = 进入交互菜单
> python run.py --city 深圳        # 等价于 python -m src.main --city 深圳
> python run.py --cache
> ```
> PyCharm 里右键 `run.py` → Run 即可，无需任何配置。
