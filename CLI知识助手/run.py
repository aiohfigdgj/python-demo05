"""项目启动器：右键运行此文件即可。

没参数 → 进入【对话模式】（推荐，自主理解你的自然语言输入）；
传参数 → 等价于 python -m src.main <操作> ...
"""
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，让 src.main 能找到兄弟模块
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.main import main  # noqa: E402

if __name__ == "__main__":
    # 没参数 → 对话模式（最直观的入口）
    if len(sys.argv) == 1:
        sys.argv.append("chat")
    sys.exit(main())