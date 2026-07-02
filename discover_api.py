import requests
import json
import time

def discover():
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://m.zuche.com/',
        'Origin': 'https://m.zuche.com',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'szzcCooki=E0868D56C813961A08FB4F59103BF90B; realName=%E5%BC%A0***; lctuid=a0f3a6a513c8b8d9bcabdd5ec35b23f6; preferred_language=zh; CAR_UID=25428f76-286a-4acc-ae2f-94bf2cb1d6bf1771863202232; LOGIN_MOBILE=17723080119; ENCRYPT_MEMBER_ID=1pjIEYmkOVVgJfcqEeGtKg==_1771864836019'
    }

    uris = [
        '/resource/carrctapi/order/cityList/v1',
        '/resource/carrctapi/order/getCityList/v1',
        '/resource/carrctapi/order/chooseCar/v1',
        '/resource/carrctapi/common/cityList/v1',
        '/resource/carrctapi/base/cityList/v1',
    ]

    params = {
        'cid': '500100'
    }

    results = []

    for uri in uris:
        url = f"https://m.zuche.com/api/gw.do?uri={uri}"
        print(f"Trying {uri}...")
        r = requests.post(url, headers=headers, data={'data': json.dumps(params)}, timeout=10)
        results.append({
            'uri': uri,
            'status': r.status_code,
            'body': r.text[:500]
        })
        time.sleep(1)

    with open('d:/discovery_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    discover()
