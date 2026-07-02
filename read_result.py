"""读取分析结果"""
with open('d:/shenzhou_gw_analysis.txt', 'rb') as f:
    raw = f.read()
text = raw.decode('utf-16-le', errors='replace')

# 写成 utf-8
with open('d:/shenzhou_gw_result.txt', 'w', encoding='utf-8') as f:
    f.write(text)

# 打印关键部分
lines = text.split('\n')
for line in lines:
    line = line.strip()
    if line:
        print(line)
