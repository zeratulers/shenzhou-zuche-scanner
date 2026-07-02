"""
深入分析神州租车 /api/gw.do 网关接口
"""
import requests
import re
import json

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
    'Accept': '*/*',
    'Referer': 'https://m.zuche.com/',
})

# 先下载 commons.js 找 gw.do 的调用方式
print("=== 下载 JS 文件分析 gw.do 调用方式 ===")
for js_name in ['commons', 'home', 'runtime~home']:
    url = f'https://h.zuchecdn.com/scripts/{js_name}.js?v=2026020515'
    try:
        r = session.get(url, timeout=30)
        text = r.text
        
        # 找 gw.do 相关代码
        # 寻找 gw.do 附近的代码段
        for m in re.finditer(r'gw\.do', text):
            start = max(0, m.start() - 300)
            end = min(len(text), m.end() + 300)
            snippet = text[start:end]
            print(f"\n--- {js_name}.js (pos {m.start()}) ---")
            print(snippet)
            print("---")
            
        # 找 cid 相关
        for m in re.finditer(r'["\']cid["\']', text):
            start = max(0, m.start() - 200)
            end = min(len(text), m.end() + 200)
            snippet = text[start:end]
            print(f"\n--- {js_name}.js cid (pos {m.start()}) ---")
            print(snippet)
            print("---")
            
    except Exception as e:
        print(f"Error downloading {js_name}: {e}")

# 试不同的 cid/aid 组合
print("\n\n=== 测试不同参数组合 ===")

session.headers['Content-Type'] = 'application/json'

test_cases = [
    # 带 cid 参数
    {'url': 'https://m.zuche.com/api/gw.do', 'method': 'POST', 
     'data': {'uri': 'city/list', 'cid': '1'}},
    {'url': 'https://m.zuche.com/api/gw.do', 'method': 'POST', 
     'data': {'cid': 'h5', 'aid': 'chooseCar', 'data': {}}},
    {'url': 'https://m.zuche.com/api/gw.do', 'method': 'POST', 
     'data': {'cid': 'h5', 'uri': 'chooseCar/cityList'}},
    # random 版本
    {'url': 'https://m.zuche.com/api/random/gw.do', 'method': 'POST',
     'data': {'uri': 'city/list'}},
    {'url': 'https://m.zuche.com/api/random/gw.do?v=1', 'method': 'POST',
     'data': {}},
    {'url': 'https://m.zuche.com/api/random/gw.do?v=1', 'method': 'GET',
     'data': None},
    # 带 uri 参数在 query string
    {'url': 'https://m.zuche.com/api/gw.do?cid=h5&aid=chooseCar', 'method': 'POST',
     'data': {}},
    {'url': 'https://m.zuche.com/api/gw.do?cid=ZUCHE_H5', 'method': 'POST',
     'data': {'uri': 'city/list'}},
]

for tc in test_cases:
    try:
        if tc['method'] == 'GET':
            r = session.get(tc['url'], timeout=10)
        else:
            r = session.post(tc['url'], json=tc['data'], timeout=10)
        
        body = r.text[:200]
        print(f"\n{tc['method']} {tc['url']}")
        if tc.get('data'):
            print(f"  Data: {json.dumps(tc['data'])}")
        print(f"  Status: {r.status_code}")
        print(f"  Response: {body}")
    except Exception as e:
        print(f"\nERR {tc['url']}: {str(e)[:100]}")
