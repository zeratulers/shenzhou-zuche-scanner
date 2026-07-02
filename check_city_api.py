import json, requests

cookie = open('cookie_cache.txt', 'r', encoding='utf-8').read().strip()

headers = {
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/x-www-form-urlencoded',
    'cookie': cookie,
    'host': 'm.zuche.com',
    'origin': 'https://m.zuche.com',
    'referer': 'https://m.zuche.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
}

proxy = 'http://127.0.0.1:7897'
proxies = {'http': proxy, 'https': proxy}

url = "https://m.zuche.com/api/gw.do?uri=/action/carrctapi/order/cityList/v1"
r = requests.post(url, headers=headers, data={'data': '{}'}, timeout=15, proxies=proxies)
res = r.json()

cities = res.get('content', {}).get('allCities', [])

# 输出前3个城市的完整JSON，以及所有城市的字段名
with open('city_fields.json', 'w', encoding='utf-8') as f:
    json.dump(cities[:3], f, ensure_ascii=False, indent=2)

# 打印所有字段名
print("字段名:", list(cities[0].keys()))
print()
# 打印前5个城市的坐标相关字段
for c in cities[:5]:
    name = c.get('cityName', c.get('name', '?'))
    print(f"{name}: ", {k: v for k, v in c.items() if 'lat' in k.lower() or 'lon' in k.lower() or 'lng' in k.lower() or 'x' == k.lower() or 'y' == k.lower()})
