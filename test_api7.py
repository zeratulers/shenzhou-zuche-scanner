import requests
import json
import urllib.parse

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://m.zuche.com/',
    'Origin': 'https://m.zuche.com',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': 'szzcCooki=E0868D56C813961A08FB4F59103BF90B; realName=%E5%BC%A0***; lctuid=a0f3a6a513c8b8d9bcabdd5ec35b23f6; preferred_language=zh; CAR_UID=25428f76-286a-4acc-ae2f-94bf2cb1d6bf1771863202232; LOGIN_MOBILE=17723080119; ENCRYPT_MEMBER_ID=1pjIEYmkOVVgJfcqEeGtKg==_1771864836019'
}

params = {
    'pickupTime': '2026-02-26 10:00',
    'returnTime': '2026-02-27 10:00',
    'pickupLat': '29.5630',
    'pickupLon': '106.5516',
    'returnLat': '29.5630',
    'returnLon': '106.5516',
}

# Try CID in query string
uri = "/resource/carrctapi/order/chooseCar/v1"
url = f"https://m.zuche.com/api/gw.do?uri={uri}&cid=500100"

print(f"URL: {url}")
r = requests.post(url, headers=headers, data={'data': json.dumps(params)})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

# Try cid as separate top-level field
url2 = f"https://m.zuche.com/api/gw.do?uri={uri}"
print(f"URL: {url2} with separate fields")
r2 = requests.post(url2, headers=headers, data={
    'cid': '500100',
    'data': json.dumps(params)
})
print(f"Status: {r2.status_code}")
print(f"Response: {r2.text[:500]}")
