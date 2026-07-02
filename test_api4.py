"""
继续调试 chooseCar 接口的正确调用方式
从 JS 分析: n.data=f.a.stringify({data:JSON.stringify(r)})
即 qs.stringify({data: JSON.stringify(params)})
所以请求体是: data=%7B%22pickupTime%22%3A...%7D (URL编码的JSON字符串)
"""
import requests
import json
import time
import urllib.parse

output = open('d:/shenzhou_test4_result.txt', 'w', encoding='utf-8')

def log(msg):
    print(msg)
    output.write(msg + '\n')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://m.zuche.com/',
    'Origin': 'https://m.zuche.com',
})

# 先访问首页获取 cookies
session.get('https://m.zuche.com/', timeout=10)

params = {
    'pickupTime': '2026-02-26 10:00',
    'returnTime': '2026-02-27 10:00', 
    'pickupLat': '39.9042',
    'pickupLon': '116.4074',
    'returnLat': '39.9042',
    'returnLon': '116.4074',
}

ts = str(int(time.time() * 1000))

# 方式1: application/x-www-form-urlencoded (浏览器默认表单格式)
log("=== 方式1: form-urlencoded data=JSON.stringify(params) ===")
url1 = f"https://m.zuche.com/api/random/gw.do?v={ts}&uri=/resource/carrctapi/order/chooseCar/v1"
r1 = session.post(url1, data={'data': json.dumps(params, separators=(',', ':'))}, timeout=10)
try:
    log(json.dumps(r1.json(), ensure_ascii=False, indent=2)[:1000])
except:
    log(r1.text[:500])

# 方式2: 不用 random，使用普通 gw.do
log("\n=== 方式2: 普通gw.do + form-urlencoded ===")
url2 = f"https://m.zuche.com/api/gw.do?uri=/resource/carrctapi/order/chooseCar/v1"
r2 = session.post(url2, data={'data': json.dumps(params, separators=(',', ':'))}, timeout=10)
try:
    log(json.dumps(r2.json(), ensure_ascii=False, indent=2)[:1000])
except:
    log(r2.text[:500])

# 方式3: Content-Type application/json 
log("\n=== 方式3: JSON body ===")
r3 = session.post(url2, json={'data': json.dumps(params, separators=(',', ':'))}, timeout=10)
try:
    log(json.dumps(r3.json(), ensure_ascii=False, indent=2)[:1000])
except:
    log(r3.text[:500])

# 方式4: 直接发 JSON 参数 (不wrapped)
log("\n=== 方式4: 直接JSON参数 ===")
r4 = session.post(url2, json=params, timeout=10)
try:
    log(json.dumps(r4.json(), ensure_ascii=False, indent=2)[:1000])
except:
    log(r4.text[:500])

# 方式5: 带 Content-Type: application/x-www-form-urlencoded 明确指定
log("\n=== 方式5: 显式设置 content-type + qs format ===")
headers5 = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://m.zuche.com/',
    'Origin': 'https://m.zuche.com',
}
body5 = 'data=' + urllib.parse.quote(json.dumps(params, separators=(',', ':')))
r5 = session.post(url2, data=body5, headers=headers5, timeout=10)
try:
    log(json.dumps(r5.json(), ensure_ascii=False, indent=2)[:1000])
except:
    log(r5.text[:500])

# 方式6: 用 random + cookie 方式, chooseCar 需要登录?
log("\n=== 方式6: 带 cid 参数 ===")
params_with_cid = params.copy()
params_with_cid['cid'] = '500100'
url6 = f"https://m.zuche.com/api/gw.do?uri=/resource/carrctapi/order/chooseCar/v1"
r6 = session.post(url6, data={'data': json.dumps(params_with_cid, separators=(',', ':'))}, timeout=10)
try:
    log(json.dumps(r6.json(), ensure_ascii=False, indent=2)[:1000])
except:
    log(r6.text[:500])

# 最重要：试试访问 testDrive 系列接口获取更多信息
log("\n=== testDrive intentionModelList ===")
url7 = "https://m.zuche.com/api/gw.do?uri=/resource/carrctapi/testDrive/intentionModelList/v1"
r7 = session.post(url7, data={'data': json.dumps({}, separators=(',', ':'))}, timeout=10)
try:
    result = r7.json()
    log(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
except:
    log(r7.text[:500])

# 试试 PC 端
log("\n=== PC端 chooseCar ===")
session2 = requests.Session()
session2.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.zuche.com/',
    'Origin': 'https://www.zuche.com',
})
session2.get('https://www.zuche.com/', timeout=10)

url8 = f"https://www.zuche.com/api/gw.do?uri=/resource/carrctapi/order/chooseCar/v1"
r8 = session2.post(url8, data={'data': json.dumps(params, separators=(',', ':'))}, timeout=10)
try:
    result = r8.json()
    log(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
except:
    log(f"Status: {r8.status_code} Body: {r8.text[:500]}")

log("\n\nCookies (mobile):")
for c in session.cookies:
    log(f"  {c.name} = {c.value}")

log("\nCookies (PC):")
for c in session2.cookies:
    log(f"  {c.name} = {c.value}")

output.close()
