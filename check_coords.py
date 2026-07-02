import json
data = json.load(open('scan_data.json', 'r', encoding='utf-8'))
for r in data['records'][:3]:
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print("---")
