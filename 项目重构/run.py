# 项目启动器：右键运行此文件即可，等价于 `python -m src.main`。

import sys
from pathlib import Path

# 把项目根目录加入 sys.path，让 src.main 能找到兄弟模块
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from src.main import main  # noqa: E402

if __name__ == "__main__":
    # 没参数 → 进入交互菜单（保留旧版体验）
    if len(sys.argv) == 1:
        sys.argv.append("--interactive")
    sys.exit(main())