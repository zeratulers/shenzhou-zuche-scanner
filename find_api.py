"""
扫描神州租车 H5 前端 JS 文件，查找 API 端点
"""
import requests
import re

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
    'Accept': '*/*',
    'Referer': 'https://m.zuche.com/'
})

js_urls = [
    'https://h.zuchecdn.com/scripts/home.js?v=2026020515',
    'https://h.zuchecdn.com/scripts/commons.js?v=2026020515',
    'https://h.zuchecdn.com/scripts/runtime~home.js?v=2026020515',
    'https://h.zuchecdn.com/lib/base.min.js?v=2026020515',
]

all_paths = []

for url in js_urls:
    print(f"Downloading: {url}")
    try:
        r = session.get(url, timeout=30)
        text = r.text
        print(f"  Size: {len(text)} chars")
        
        # 搜索所有 URL/path 模式
        patterns = re.findall(r'["\'](((?:/|https?://)[^\s"\'<>]{5,120}))["\')]', text)
        
        keywords = ['city', 'dept', 'car', 'store', 'vehicle', 'choose', 
                     'query', 'search', 'list', 'branch', 'shop', 'order', 
                     'api', 'gateway', 'resource', 'openapi', 'rent', 'book',
                     'price', 'offer', 'model']
        
        for p, _ in patterns:
            if any(kw in p.lower() for kw in keywords):
                all_paths.append(p)
                
    except Exception as e:
        print(f"  Error: {e}")

unique_paths = sorted(set(all_paths))

print(f"\n{'='*60}")
print(f"Total unique API-like paths found: {len(unique_paths)}")
print(f"{'='*60}\n")

with open('d:/shenzhou_apis_found.txt', 'w', encoding='utf-8') as f:
    for p in unique_paths:
        print(p)
        f.write(p + '\n')

print(f"\nSaved to d:/shenzhou_apis_found.txt")
