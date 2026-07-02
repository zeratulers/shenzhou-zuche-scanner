"""
用真实 Cookie 测试神州租车选车接口
"""
import requests
import json
import time

output = open('d:/shenzhou_test5_result.txt', 'w', encoding='utf-8')

def log(msg):
    print(msg)
    output.write(msg + '\n')

cookie_str = 'szzcCooki=E0868D56C813961A08FB4F59103BF90B; realName=%E5%BC%A0***; lctuid=a0f3a6a513c8b8d9bcabdd5ec35b23f6; preferred_language=zh; CAR_UID=25428f76-286a-4acc-ae2f-94bf2cb1d6bf1771863202232; LOGIN_MOBILE=17723080119; ENCRYPT_MEMBER_ID=1pjIEYmkOVVgJfcqEeGtKg==_1771864836019'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://m.zuche.com/',
    'Origin': 'https://m.zuche.com',
    'Cookie': cookie_str,
})

# 先访问首页获取服务端 session cookie
r0 = session.get('https://m.zuche.com/', timeout=10)
log(f"首页访问: {r0.status_code}")

# 把用户 cookie 也加到 session 中
for part in cookie_str.split('; '):
    if '=' in part:
        k, v = part.split('=', 1)
        session.cookies.set(k, v)

ts = str(int(time.time() * 1000))

# 测试1: chooseCar - 北京
log("\n=== 选车: 北京 ===")
params = {
    'pickupTime': '2026-02-26 10:00',
    'returnTime': '2026-02-27 10:00',
    'pickupLat': '39.9042',
    'pickupLon': '116.4074',
    'returnLat': '39.9042',
    'returnLon': '116.4074',
}
url = f"https://m.zuche.com/api/random/gw.do?v={ts}&uri=/resource/carrctapi/order/chooseCar/v1"
r1 = session.post(url, data={'data': json.dumps(params, separators=(',', ':'))}, timeout=15)
try:
    result = r1.json()
    log(json.dumps(result, ensure_ascii=False, indent=2)[:3000])
except:
    log(f"Status: {r1.status_code}, Body: {r1.text[:500]}")

# 测试2: chooseCar - 重庆 (用户取车网点在重庆)
log("\n\n=== 选车: 重庆 ===")
params2 = {
    'pickupTime': '2026-02-26 10:00',
    'returnTime': '2026-02-27 10:00',
    'pickupLat': '29.5630',
    'pickupLon': '106.5516',
    'returnLat': '29.5630',
    'returnLon': '106.5516',
}
ts2 = str(int(time.time() * 1000))
url2 = f"https://m.zuche.com/api/random/gw.do?v={ts2}&uri=/resource/carrctapi/order/chooseCar/v1"
r2 = session.post(url2, data={'data': json.dumps(params2, separators=(',', ':'))}, timeout=15)
try:
    result2 = r2.json()
    log(json.dumps(result2, ensure_ascii=False, indent=2)[:3000])
except:
    log(f"Status: {r2.status_code}, Body: {r2.text[:500]}")

# 测试3: 普通 gw.do 的城市列表
log("\n\n=== 城市列表 ===")
url3 = "https://m.zuche.com/api/gw.do?uri=/resource/carrctapi/order/chooseCar/v1"
r3 = session.post(url3, data={'data': json.dumps(params, separators=(',', ':'))}, timeout=15)
try:
    result3 = r3.json()
    log(json.dumps(result3, ensure_ascii=False, indent=2)[:3000])
except:
    log(f"Status: {r3.status_code}, Body: {r3.text[:500]}")

log("\n\nCookies:")
for c in session.cookies:
    log(f"  {c.name} = {c.value[:60]}")

output.close()
print("Done! Check d:/shenzhou_test5_result.txt")
