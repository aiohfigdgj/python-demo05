"""【重构前 · 旧版 v1】天气查询工具（交互菜单版）—— 用户真实项目样本。

⚠️ 这个文件保留"重构前"的原始代码，供对照学习，不参与运行。
新版请使用 src/tools/weather.py + src/tools/cache.py。

【问题清单（重构原因）】
1. ❌ 缓存文件路径 / 缓存有效期 / 请求头全部硬编码在文件里
2. ❌ 交互菜单靠 input() 循环 —— 无法脚本化、无法自动化测试
3. ❌ 用 print 输出 —— 无法控制日志级别、无法写入日志文件
4. ❌ 业务逻辑（请求 / 缓存 / 校验 / 展示）全部挤在一个文件
5. ❌ 数据源写死 wttr.in —— 想换数据源要改代码

【重构后的改进】见 src/tools/weather.py：
    数据源 / 缓存路径 / TTL 由 config/*.yaml 驱动（热切换 dev/prod/test）/
    缓存抽离为 tools/cache.py（单一职责）/ print 换成 logging /
    交互菜单改造成 argparse 参数（--city / --cities / --cache / --clear-cache）/
    保留全部功能：单城市、批量、缓存查看与清除、城市名校验、低温提醒。
"""
import json
import os
import re
import time
from urllib.parse import quote

import requests

CACHE_FILE = "weather_cache.json"   # 缓存就存这个文件里
CACHE_TTL = 3600                     # 1小时有效
HEADERS = {"User-Agent": "Mozilla/5.0"}


def check_city(city):
    # 功能5：城市名只允许中文英文数字空格连字符，别的都拦
    if not re.match(r"^[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9\s-]{0,19}$", city.strip()):
        raise ValueError(f"城市名 {city!r} 不合法")
    return city.strip()


def get_from_api(city):
    # 调 wttr.in 接口，拿到温度天气湿度
    # 出各种错就抛异常，让 main 那边接住
    try:
        r = requests.get(f"https://wttr.in/{quote(city)}?format=j1", timeout=8, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.Timeout:
        raise TimeoutError("请求超时了，是不是网络不好")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("连不上网，检查下网络")
    except (requests.exceptions.HTTPError, ValueError):
        # 城市名不对的时候 wttr.in 返回的不是 JSON，就当成没这个城市
        raise LookupError(f"找不到城市 {city}，换个写法试试")

    cond = data.get("current_condition") or [{}]
    if not cond or not cond[0].get("temp_C"):
        raise LookupError(f"查不到 {city} 的天气")
    return {
        "city": city,
        "temp": cond[0]["temp_C"],
        "weather": (cond[0].get("weatherDesc") or [{}])[0].get("value", "?"),
        "humidity": cond[0].get("humidity", "?"),
    }


def get_weather(city):
    # 功能3：先翻缓存，没过期就直接用，省得老调接口
    cache = {}
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
    except Exception:
        pass   # 缓存读不了就当没有，重新拉
    entry = cache.get(city)
    if entry and time.time() - entry["ts"] < CACHE_TTL:
        print(f"用的是缓存，{int(time.time() - entry['ts'])}秒前查过")
        return entry["data"]
    # 没缓存或者过期了，调接口然后存起来
    data = get_from_api(city)
    cache[city] = {"ts": time.time(), "data": data}
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    return data


def query_one(city):
    # 功能1：查一个城市
    city = check_city(city)
    d = get_weather(city)
    print(f"\n【{d['city']}】")
    print(f"温度 {d['temp']}℃  天气 {d['weather']}  湿度 {d['humidity']}%")
    # 功能5：太冷提醒一下
    if int(d["temp"]) < 10:
        print("都10度以下了，记得加衣服！")
    return d


def query_many(cities):
    # 功能2：一次查好几个，打个小表格
    rows = []
    for c in cities:
        try:
            rows.append(get_weather(check_city(c)))
        except Exception as e:
            print(f"{c} 出错了：{e}")   # 单个失败不影响别的
    print(f"\n{'城市':<8}{'温度':<6}{'天气':<10}{'湿度':<6}")
    print("-" * 32)
    for d in rows:
        print(f"{d['city']:<8}{d['temp']+'℃':<6}{d['weather']:<10}{d['humidity']+'%':<6}")
    return rows


def show_cache():
    # 菜单3：看看缓存里存了啥
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
    except Exception:
        print("缓存是空的（还没查过城市）")
        return
    if not cache:
        print("缓存是空的（还没查过城市）")
        return
    print(f"缓存里存了 {len(cache)} 个城市：")
    for city, entry in cache.items():
        d = entry["data"]
        print(f"  {city}：{d['temp']}℃，{d['weather']}（{int(time.time() - entry['ts'])}秒前查的）")


def clear_cache():
    # 菜单4：把缓存文件删了
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print("缓存已清除")
    else:
        print("本来就没缓存")


def main():
    # 主菜单：输数字选功能，输0退出
    print("=" * 28)
    print("     天气查询小工具")
    print("=" * 28)
    while True:
        print("\n请选择功能：")
        print("  1. 查询单个城市")
        print("  2. 批量查询（多个城市，逗号隔开）")
        print("  3. 查看缓存")
        print("  4. 清除缓存")
        print("  0. 退出")
        choice = input("输入数字：").strip()
        if choice == "1":
            city = input("输城市名：").strip()
            try:
                query_one(city)
            except Exception as e:
                print(f"出错：{e}")
        elif choice == "2":
            s = input("输多个城市，用逗号隔开：").strip()
            cities = [x.strip() for x in re.split(r"[，,]", s) if x.strip()]
            if cities:
                query_many(cities)
            else:
                print("没输入城市")
        elif choice == "3":
            show_cache()
        elif choice == "4":
            clear_cache()
        elif choice == "0":
            print("拜拜~")
            break
        else:
            print("没这个选项，再输一次")


if __name__ == "__main__":
    main()
