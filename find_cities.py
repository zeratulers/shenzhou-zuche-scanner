# -*- coding: utf-8 -*-
"""从神州租车 H5 页面 JS 或 API 获取完整的开放城市列表"""
import requests
import json
import re

proxy = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
}

results = []

# 方法1: 直接访问 H5 首页看有没有城市数据
try:
    r = requests.get("https://m.zuche.com/", headers=headers, timeout=10, proxies=proxy)
    html = r.text
    # 搜索城市相关的 JSON 数据
    city_matches = re.findall(r'cityId["\s:]+(\d+)[^}]*?cityName["\s:]+["\']([^"\']+)', html)
    if city_matches:
        results.append(f"Method1: Found {len(city_matches)} cities in HTML")
        for cid, name in city_matches[:5]:
            results.append(f"  {name} = {cid}")
    else:
        results.append("Method1: No city data in HTML")
except Exception as e:
    results.append(f"Method1 Error: {e}")

# 方法2: 尝试更多 API uri
cookie = "szzcCooki=E0868D56C813961A08FB4F59103BF90B; realName=%E5%BC%A0***; aliyungf_tc=3d2c0047b6d48fabed3633c4efc8d1cd010d1161e4bff9c07cb61cc16ae22711; acw_tc=0a01823a17718648346488537e250091a7bd06aed583f53588445db2584df4; lctuid=a0f3a6a513c8b8d9bcabdd5ec35b23f6; preferred_language=zh; CAR_UID=25428f76-286a-4acc-ae2f-94bf2cb1d6bf1771863202232; LOGIN_MOBILE=17723080119; ENCRYPT_MEMBER_ID=1pjIEYmkOVVgJfcqEeGtKg==_1771865691215; intranet-sessionid=c05a6a0e-82dc-4400-90d3-05cd632c6ac4"

api_headers = {
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/x-www-form-urlencoded',
    'cookie': cookie,
    'origin': 'https://m.zuche.com',
    'referer': 'https://m.zuche.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
}

more_uris = [
    "/resource/carrctapi/order/cityList/v1",
    "/resource/carrctapi/order/openCity/v1",
    "/resource/carrctapi/dept/cityList/v1",
    "/resource/carrctapi/dept/openCityList/v1",
    "/resource/carrctapi/rent/cityList/v1",
    "/resource/carrctapi/index/cityList/v1",
    "/resource/carrctapi/chooseCar/cityList/v1",
]

for uri in more_uris:
    url = f"https://m.zuche.com/api/gw.do?uri={uri}"
    try:
        r = requests.post(url, headers=api_headers, data={'data': '{}'}, timeout=8, proxies=proxy)
        res = r.json()
        status = res.get('status', '?')
        msg = res.get('msg', '')[:80]
        content = res.get('content')
        line = f"  {uri} -> {status} | {msg}"
        if content:
            if isinstance(content, list):
                line += f" | list[{len(content)}]"
            elif isinstance(content, dict):
                line += f" | keys={list(content.keys())[:5]}"
        results.append(line)
        if status == 'SUCCESS':
            with open("d:/city_api_success.json", "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
            results.append("    >>> SAVED!")
    except Exception as e:
        results.append(f"  {uri} -> ERR: {e}")

# 方法3: 暴力枚举 cityId 1-200，看哪些有数据
results.append("\nMethod3: Brute-force cityId 1-200...")
valid_cities = {}
for cid in range(1, 201):
    url = "https://m.zuche.com/api/gw.do?uri=/resource/carrctapi/order/chooseCar/v3"
    params = {
        "pickupCityId": str(cid),
        "pickupTime": "2026-02-26 12:00",
        "returnCityId": str(cid),
        "returnTime": "2026-02-28 12:00",
        "entrance": 1,
        "userChooseLat": "39.514295",
        "userChooseLon": "116.414348",
        "holidaysWaitingFlag": 0
    }
    try:
        r = requests.post(url, headers=api_headers, data={'data': json.dumps(params, separators=(',', ':'))},
                          timeout=8, proxies=proxy)
        res = r.json()
        if res.get('status') == 'SUCCESS':
            depts = res.get('content', {}).get('deptHangModels', [])
            if depts:
                # 从第一个 dept 拿 cityId 确认
                dept_city = depts[0].get('cityId', cid)
                # 从返回数据拿不到城市名, 但能确认这个 cityId 有效
                valid_cities[cid] = len(depts)
                results.append(f"  cityId={cid} -> {len(depts)} depts VALID")
    except:
        pass

results.append(f"\nTotal valid cityIds: {len(valid_cities)}")
results.append(f"Valid IDs: {sorted(valid_cities.keys())}")

with open("d:/city_full_discovery.txt", "w", encoding="utf-8") as f:
    for line in results:
        f.write(line + "\n")

with open("d:/valid_city_ids.json", "w", encoding="utf-8") as f:
    json.dump(valid_cities, f, indent=2)

print(f"Done! Found {len(valid_cities)} valid cities. Check d:/city_full_discovery.txt")
