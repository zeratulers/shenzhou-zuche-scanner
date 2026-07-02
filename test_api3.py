"""
正确格式调用神州租车 H5 网关—结果写入文件
"""
import requests
import json
import time
import sys

# 重定向输出到文件
output_file = open('d:/shenzhou_test3_result.txt', 'w', encoding='utf-8')

def log(msg):
    print(msg)
    output_file.write(msg + '\n')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://m.zuche.com/',
    'Origin': 'https://m.zuche.com',
})

def call_gw(uri, params, use_random=False):
    ts = str(int(time.time() * 1000))
    if use_random:
        url = f"https://m.zuche.com/api/random/gw.do?v={ts}&uri={uri}"
    else:
        url = f"https://m.zuche.com/api/gw.do?uri={uri}"
    
    form_data = {
        'data': json.dumps(params, separators=(',', ':'), ensure_ascii=False)
    }
    r = session.post(url, data=form_data, timeout=10)
    return r

tests = [
    ("空参数 chooseCar", {}, '/resource/carrctapi/order/chooseCar/v1', False),
    ("带cid chooseCar", {'cid': '500100'}, '/resource/carrctapi/order/chooseCar/v1', False),
    ("完整参数 chooseCar", {
        'pickupTime': '2026-02-26 10:00',
        'returnTime': '2026-02-27 10:00', 
        'pickupLat': '39.9042',
        'pickupLon': '116.4074',
        'returnLat': '39.9042',
        'returnLon': '116.4074',
        'cid': '500100'
    }, '/resource/carrctapi/order/chooseCar/v1', False),
    ("完整参数 chooseCar random", {
        'pickupTime': '2026-02-26 10:00',
        'returnTime': '2026-02-27 10:00', 
        'pickupLat': '39.9042',
        'pickupLon': '116.4074',
        'returnLat': '39.9042',
        'returnLon': '116.4074',
    }, '/resource/carrctapi/order/chooseCar/v1', True),
    ("testDrive homePage", {}, '/resource/carrctapi/testDrive/homePage/v1', False),
]

for name, params, uri, use_random in tests:
    log(f"\n{'='*50}")
    log(f"测试: {name}")
    log(f"URI: {uri}, random={use_random}")
    log(f"Params: {json.dumps(params, ensure_ascii=False)}")
    try:
        r = call_gw(uri, params, use_random=use_random)
        try:
            resp = json.dumps(r.json(), ensure_ascii=False, indent=2)
        except:
            resp = r.text[:500]
        log(f"Status: {r.status_code}")
        log(f"Response:\n{resp[:800]}")
    except Exception as e:
        log(f"Error: {e}")

log("\n\nCookies:")
for c in session.cookies:
    log(f"  {c.name} = {c.value}")

output_file.close()
