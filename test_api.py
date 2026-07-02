"""
测试神州租车 H5 前端实际使用的 API 接口
"""
import requests
import json

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://m.zuche.com/',
    'Origin': 'https://m.zuche.com',
    'Content-Type': 'application/json',
})

base_urls = [
    'https://m.zuche.com',
    'https://icar.zuche.com',
]

api_paths = [
    # 选车
    ('/resource/carrctapi/order/chooseCar/v1', 'POST', {
        'pickupTime': '2026-02-26 10:00',
        'returnTime': '2026-02-27 10:00',
        'pickupLat': '39.9042',
        'pickupLon': '116.4074',
        'returnLat': '39.9042',
        'returnLon': '116.4074',
    }),
    # 城市
    ('/business/city', 'GET', None),
    ('/business/city', 'POST', {}),
    # 通用网关
    ('/api/gw.do', 'POST', {'uri': 'city/list'}),
    ('/api/gw.do?uri=city/list', 'GET', None),
    ('/api/gw.do?uri=city/list', 'POST', {}),
    # 网点
    ('/deptlist', 'GET', None),
]

results = []

for base in base_urls:
    for path, method, data in api_paths:
        url = base + path
        try:
            if method == 'GET':
                r = session.get(url, timeout=10)
            else:
                r = session.post(url, json=data, timeout=10)
            
            ct = r.headers.get('Content-Type', '')
            body = r.text[:300]
            is_json = 'json' in ct or body.strip().startswith('{') or body.strip().startswith('[')
            
            result = f"{r.status_code} {method} {url}"
            result += f"\n  Content-Type: {ct}"
            result += f"\n  Is JSON: {is_json}"
            result += f"\n  Body: {body}"
            result += "\n"
            results.append(result)
            
            if is_json and r.status_code == 200:
                print(f"*** HIT! {method} {url}")
            else:
                print(f"    {r.status_code} {method} {url}")
                
        except Exception as e:
            results.append(f"ERR {method} {url}\n  {str(e)[:150]}\n")
            print(f"ERR {method} {url}: {str(e)[:80]}")

with open('d:/shenzhou_api_test2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print(f"\nDone! Results in d:/shenzhou_api_test2.txt")
