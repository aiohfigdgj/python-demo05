"""测试公共配置：与用户真实 .env 隔离。

防止测试真的去调 LLM（费钱 + 慢 + 断言不稳定）。
强制 LLM_PROVIDER=mock，测试永远用规则模板，不依赖用户本机配置。
"""
import os

# 在 llm.py 的 load_dotenv 之前生效（pytest 先加载 conftest 再收集测试模块）
os.environ["LLM_PROVIDER"] = "mock"
