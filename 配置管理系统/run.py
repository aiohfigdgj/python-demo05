"""项目启动器：配置管理系统交互演示（热切换 + 配置驱动的行为变化）。

用法：
    python run.py              # ★ 交互模式
    python run.py dev          # 单次模式：查看指定环境的关键配置
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml  # noqa: E402

from src.config import ConfigManager  # noqa: E402
from src.toolbox import query_weather  # noqa: E402


def show_config(cfg) -> None:
    """打印当前环境完整配置。"""
    print(f"\n--- 环境: {cfg.env}（完整配置）---")
    print(yaml.safe_dump(cfg.as_dict(), allow_unicode=True, sort_keys=False))


def interactive() -> int:
    manager = ConfigManager()
    while True:
        cfg = manager.current()
        print("\n" + "=" * 46)
        print(f"当前环境: {cfg.env}")
        print(f"  天气数据源: {cfg.get('weather.provider')}  日志级别: {cfg.get('app.log_level')}")
        print("=" * 46)
        print(" 1. 热切换环境（dev / prod / test）")
        print(" 2. 查看当前配置")
        print(" 3. 查天气（用当前环境的数据源！）")
        print(" 0. 退出")
        choice = input("> ").strip()

        if choice == "0":
            print("拜拜~")
            return 0
        elif choice == "1":
            env = input("切换到哪个环境? [dev/prod/test]: ").strip()
            try:
                manager.switch_env(env)
                print(f"✔ 已热切换到 {manager.current().env}（无需重启进程）")
            except Exception as exc:
                print(f"✘ 切换失败: {exc}")
        elif choice == "2":
            show_config(manager.current())
        elif choice == "3":
            city = input("城市（回车默认深圳）: ").strip() or "深圳"
            data = query_weather(city, manager.current())
            if data["temp"] is not None:
                print(f"[{manager.current().env}][{data['source']}] {data['city']} "
                      f"{data['weather']} {data['temp']}℃ 湿度{data['humidity']}%")
            else:
                print(f"[{manager.current().env}][{data['source']}] {data['weather']}")
        else:
            print("没这个选项\n")


if __name__ == "__main__":
    # 单次模式：run.py dev → 打印该环境配置
    if len(sys.argv) > 1:
        m = ConfigManager(sys.argv[1])
        show_config(m.current())
        sys.exit(0)
    sys.exit(interactive())