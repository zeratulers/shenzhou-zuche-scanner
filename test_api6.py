import requests
import json
import time

def test():
    # Headers exactly as a mobile browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
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
        'cid': '500100' # Add CID as found in JS
    }

    # The format is literally data={"..."}
    body = {
        'data': json.dumps(params, separators=(',', ':'), ensure_ascii=False)
    }

    url = "https://m.zuche.com/api/gw.do?uri=/resource/carrctapi/order/chooseCar/v1"
    
    print(f"Testing URL: {url}")
    r = requests.post(url, headers=headers, data=body, timeout=15)
    
    print(f"Status: {r.status_code}")
    try:
        data = r.json()
        print("Response (JSON):")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        # If success, save it
        if data.get('status') == 'SUCCESS':
            with open('d:/choosecar_success.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        print("Response (Text):")
        print(r.text[:1000])

if __name__ == '__main__':
    test()
