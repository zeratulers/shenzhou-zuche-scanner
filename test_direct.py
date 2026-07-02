# -*- coding: utf-8 -*-
import requests
import json
import urllib.parse
import sys

# ====== 你的 Cookie ======
cookie = "szzcCooki=E0868D56C813961A08FB4F59103BF90B; realName=%E5%BC%A0***; aliyungf_tc=3d2c0047b6d48fabed3633c4efc8d1cd010d1161e4bff9c07cb61cc16ae22711; acw_tc=0a01823a17718648346488537e250091a7bd06aed583f53588445db2584df4; lctuid=a0f3a6a513c8b8d9bcabdd5ec35b23f6; preferred_language=zh; CAR_UID=25428f76-286a-4acc-ae2f-94bf2cb1d6bf1771863202232; LOGIN_MOBILE=17723080119; ENCRYPT_MEMBER_ID=1pjIEYmkOVVgJfcqEeGtKg==_1771865691215; intranet-sessionid=c05a6a0e-82dc-4400-90d3-05cd632c6ac4"

# ====== 完全复刻浏览器请求 ======
url = "https://m.zuche.com/api/gw.do?uri=/resource/carrctapi/order/chooseCar/v3"

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'zh-CN,zh;q=0.9',
    'connection': 'keep-alive',
    'content-type': 'application/x-www-form-urlencoded',
    'cookie': cookie,
    'host': 'm.zuche.com',
    'origin': 'https://m.zuche.com',
    'referer': 'https://m.zuche.com/',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
}

# ====== 完全复刻浏览器 payload (参数名和值都一模一样) ======
params = {
    "pickupCityId": "6",
    "pickupTime": "2026-02-26 12:00",
    "returnCityId": "6",
    "returnTime": "2026-02-28 12:00",
    "entrance": 1,
    "userChooseLat": "31.230400",
    "userChooseLon": "121.473700",
    "holidaysWaitingFlag": 0
}

# requests 自动 form-encode
form_body = {'data': json.dumps(params, separators=(',', ':'))}

out = []  # 收集输出

# ====== 测试1: 走代理 ======
out.append("=== TEST 1: PROXY 127.0.0.1:7897 ===")
try:
    r = requests.post(url, headers=headers, data=form_body, timeout=15,
                      proxies={"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"})
    out.append("HTTP: " + str(r.status_code))
    res = r.json()
    out.append("status: " + str(res.get('status')))
    out.append("msg: " + str(res.get('msg')))
    out.append("code: " + str(res.get('code')))
    if res.get('status') == 'SUCCESS':
        depts = res.get('content', {}).get('deptHangModels', [])
        out.append("FOUND " + str(len(depts)) + " depts!")
        for d in depts[:2]:
            out.append("  dept: " + d.get('deptName', '?'))
            models = d.get('models', [])
            out.append("  models: " + str(len(models)))
            for m in models[:3]:
                out.append("    - " + m.get('modelName', '?') + " daily=" + str(m.get('dailyPrice', '?')))
    else:
        out.append("response: " + json.dumps(res, ensure_ascii=False)[:500])
except Exception as e:
    out.append("EXCEPTION: " + str(e))

# ====== 测试2: 直连 ======
out.append("")
out.append("=== TEST 2: DIRECT ===")
try:
    r = requests.post(url, headers=headers, data=form_body, timeout=15)
    out.append("HTTP: " + str(r.status_code))
    res = r.json()
    out.append("status: " + str(res.get('status')))
    out.append("msg: " + str(res.get('msg')))
    if res.get('status') == 'SUCCESS':
        depts = res.get('content', {}).get('deptHangModels', [])
        out.append("FOUND " + str(len(depts)) + " depts!")
    else:
        out.append("response: " + json.dumps(res, ensure_ascii=False)[:500])
except Exception as e:
    out.append("EXCEPTION: " + str(e))

# 写文件
with open("d:/test_v3_result.txt", "w", encoding="utf-8") as f:
    for line in out:
        f.write(line + "\n")
        print(line)
