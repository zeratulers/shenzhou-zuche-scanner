# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import time
import threading
import csv
import os
import webbrowser
from datetime import datetime, timedelta

# ============================================================
# 配置
# ============================================================
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(WORK_DIR, "cookie_cache.txt")
DATA_FILE = os.path.join(WORK_DIR, "scan_data.json")
MAP_FILE = os.path.join(WORK_DIR, "map.html")

RATE_WINDOW = 30
RATE_LIMIT = 28


def clean_cookie(raw):
    text = raw.strip()
    for line in text.split('\n'):
        if 'intranet-sessionid' in line:
            text = line.strip()
            break
    lower = text.lower()
    if lower.startswith('cookie:'):
        text = text[7:].strip()
    return ''.join(c for c in text if 32 <= ord(c) < 127)


def load_cookie():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return ""


def save_cookie(c):
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        f.write(c)


def load_scan_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_scan_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_headers(cookie_str):
    return {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9',
        'connection': 'keep-alive',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': cookie_str,
        'host': 'm.zuche.com',
        'origin': 'https://m.zuche.com',
        'referer': 'https://m.zuche.com/',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    }


def refresh_cookie(cookie_str, response):
    for c in response.cookies:
        if c.name == 'intranet-sessionid':
            parts, found = [], False
            for part in cookie_str.split(';'):
                p = part.strip()
                if p.startswith('intranet-sessionid='):
                    parts.append('intranet-sessionid=' + c.value)
                    found = True
                elif p:
                    parts.append(p)
            if not found:
                parts.append('intranet-sessionid=' + c.value)
            return '; '.join(parts)
    return cookie_str


class RateLimiter:
    def __init__(self, max_calls, window_sec):
        self.max_calls = max_calls
        self.window_sec = window_sec
        self.timestamps = []

    def wait_if_needed(self):
        now = time.time()
        self.timestamps = [t for t in self.timestamps if now - t < self.window_sec]
        if len(self.timestamps) >= self.max_calls:
            sleep_time = self.timestamps[0] + self.window_sec - now + 0.5
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.timestamps.append(time.time())


def fetch_city_list(cookie_str, proxy=None):
    url = "https://m.zuche.com/api/gw.do?uri=/action/carrctapi/order/cityList/v1"
    headers = make_headers(cookie_str)
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    r = requests.post(url, headers=headers, data={'data': '{}'}, timeout=15, proxies=proxies)
    res = r.json()
    new_cookie = refresh_cookie(cookie_str, r)
    if res.get('status') == 'SUCCESS' or res.get('code') == 1:
        return res.get('content', {}).get('allCities', []), new_cookie
    raise Exception(f"获取城市列表失败: {res.get('msg', '?')}")


def search_city(cookie_str, city_id, pickup_time, return_time, lat, lon, proxy=None):
    url = "https://m.zuche.com/api/gw.do?uri=/resource/carrctapi/order/chooseCar/v3"
    headers = make_headers(cookie_str)
    params = {
        "pickupCityId": str(city_id),
        "pickupTime": pickup_time,
        "returnCityId": str(city_id),
        "returnTime": return_time,
        "entrance": 1,
        "userChooseLat": lat,
        "userChooseLon": lon,
        "holidaysWaitingFlag": 0
    }
    form_body = {'data': json.dumps(params, separators=(',', ':'))}
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    r = requests.post(url, headers=headers, data=form_body, timeout=15, proxies=proxies)
    return r.json(), refresh_cookie(cookie_str, r)


# ============================================================
# 地图 HTML 生成
# ============================================================
def generate_map_html(records, selected_models, meta, city_coords):
    """生成 ECharts 中国地图 HTML, city_coords = {'北京': [116.4, 39.9], ...}"""
    days = meta.get('days', 1)

    # 按城市+车型聚合, 取最低价
    city_data = {}
    for r in records:
        if r['modelName'] not in selected_models:
            continue
        city_name = r.get('cityName', '')
        key = (city_name, r.get('modelName', ''))
        try:
            pkg = float(r.get('packagePrice', 0))
        except:
            pkg = 0
        try:
            daily = float(r.get('dailyPrice', 0))
        except:
            daily = 0
        price = pkg if pkg > 0 else daily

        # 从 city_coords 映射表查坐标
        coords = city_coords.get(city_name, [116.4, 39.9])

        if key not in city_data or price < city_data[key]['price']:
            city_data[key] = {
                'city': city_name,
                'model': r.get('modelName', ''),
                'price': price,
                'total': price * days,
                'dept': r.get('deptName', ''),
                'addr': r.get('deptAddress', ''),
                'desc': r.get('modelDesc', ''),
                'lon': coords[0],
                'lat': coords[1],
            }

    # 转为 ECharts 数据
    scatter_data = []
    for v in city_data.values():
        scatter_data.append({
            'name': v['city'],
            'value': [v['lon'], v['lat'], v['price']],
            'model': v['model'],
            'price': v['price'],
            'total': v['total'],
            'dept': v['dept'],
            'addr': v['addr'],
            'desc': v['desc'],
        })

    models_str = ', '.join(selected_models)
    date_str = f"{meta.get('start_date', '?')} ~ {meta.get('end_date', '?')} ({days}天)"

    # 价格区间用于颜色映射
    prices = [d['price'] for d in scatter_data] if scatter_data else [0]
    min_price = min(prices)
    max_price = max(prices)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>神州租车 · 全国车型分布</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #0a1628; font-family: 'Microsoft YaHei', sans-serif; color: #fff; }}
  #header {{
    text-align: center; padding: 18px;
    background: linear-gradient(135deg, #0d1b2a 0%, #1b2838 100%);
    border-bottom: 1px solid #1e3a5f;
  }}
  #header h1 {{ font-size: 22px; color: #4fc3f7; margin-bottom: 6px; }}
  #header p {{ font-size: 13px; color: #90a4ae; }}
  #header .stats {{
    margin-top: 10px; display: flex; justify-content: center; gap: 30px;
  }}
  #header .stats .item {{
    background: rgba(79,195,247,0.1); border: 1px solid #1e3a5f;
    border-radius: 8px; padding: 8px 20px; text-align: center;
  }}
  #header .stats .item .num {{ font-size: 24px; color: #4fc3f7; font-weight: bold; }}
  #header .stats .item .label {{ font-size: 11px; color: #78909c; }}
  #map {{ width: 100%; height: calc(100vh - 140px); }}
</style>
</head>
<body>
<div id="header">
  <h1>🚗 神州租车 · {models_str}</h1>
  <p>📅 {date_str}</p>
  <div class="stats">
    <div class="item"><div class="num">{len(scatter_data)}</div><div class="label">有车城市</div></div>
    <div class="item"><div class="num">¥{min_price:.0f}</div><div class="label">最低日租</div></div>
    <div class="item"><div class="num">¥{max_price:.0f}</div><div class="label">最高日租</div></div>
    <div class="item"><div class="num">¥{min_price*days:.0f}</div><div class="label">{days}天最低</div></div>
  </div>
</div>
<div id="map"></div>
<script>
var chart = echarts.init(document.getElementById('map'), 'dark');

// 加载中国地图
fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
.then(r => r.json())
.then(china => {{
  echarts.registerMap('china', china);
  var data = {json.dumps(scatter_data, ensure_ascii=False)};

  chart.setOption({{
    tooltip: {{
      trigger: 'item',
      backgroundColor: 'rgba(13,27,42,0.95)',
      borderColor: '#1e3a5f',
      textStyle: {{ color: '#e0e0e0', fontSize: 13 }},
      formatter: function(p) {{
        var d = p.data;
        return '<b style="color:#4fc3f7;font-size:15px">' + d.name + '</b><br/>'
          + '🚗 ' + d.model + '<br/>'
          + '📋 ' + d.desc + '<br/>'
          + '📍 ' + d.dept + '<br/>'
          + '📮 ' + d.addr + '<br/>'
          + '<span style="color:#ffd54f;font-size:16px">¥' + d.price + '/天</span>'
          + '　<span style="color:#ff8a65">{days}天共 ¥' + d.total.toFixed(0) + '</span>';
      }}
    }},
    geo: {{
      map: 'china',
      roam: true,
      zoom: 1.2,
      center: [104, 35],
      itemStyle: {{
        areaColor: '#0d2137',
        borderColor: '#1e3a5f',
        borderWidth: 1
      }},
      emphasis: {{
        itemStyle: {{
          areaColor: '#1a3a5c'
        }}
      }},
      label: {{ show: false }}
    }},
    visualMap: {{
      min: {min_price},
      max: {max_price if max_price > min_price else min_price + 1},
      text: ['贵', '便宜'],
      textStyle: {{ color: '#90a4ae' }},
      inRange: {{
        color: ['#4caf50', '#ffeb3b', '#ff5722']
      }},
      calculable: true,
      left: 20,
      bottom: 30
    }},
    series: [{{
      type: 'effectScatter',
      coordinateSystem: 'geo',
      data: data.map(function(d) {{
        return {{
          name: d.name,
          value: d.value,
          model: d.model,
          price: d.price,
          total: d.total,
          dept: d.dept,
          addr: d.addr,
          desc: d.desc
        }};
      }}),
      symbolSize: function(val) {{
        return Math.max(10, Math.min(25, 30 - (val[2] - {min_price}) / ({max_price - min_price if max_price > min_price else 1}) * 18));
      }},
      encode: {{ value: 2 }},
      showEffectOn: 'render',
      rippleEffect: {{
        brushType: 'stroke',
        scale: 3,
        period: 4
      }},
      label: {{
        show: true,
        formatter: function(p) {{ return p.data.name + ' ¥' + p.data.price; }},
        position: 'right',
        fontSize: 11,
        color: '#b0bec5'
      }},
      itemStyle: {{
        shadowBlur: 10,
        shadowColor: 'rgba(79,195,247,0.5)'
      }}
    }}]
  }});
}});

window.addEventListener('resize', function() {{ chart.resize(); }});
</script>
</body>
</html>"""
    return html


# ============================================================
# UI
# ============================================================
class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("神州租车 · 全国搜车工具")
        self.root.geometry("1200x900")
        self.all_records = []
        self.stop_flag = False
        self.scan_meta = {}
        self.city_coords = {}  # {'北京': [116.4, 39.9], ...}

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.tab_scan = tk.Frame(self.notebook)
        self.notebook.add(self.tab_scan, text="  🔍 全国扫描  ")
        self._build_scan_tab()

        self.tab_result = tk.Frame(self.notebook)
        self.notebook.add(self.tab_result, text="  📊 结果查询  ")
        self._build_result_tab()

        self._try_load_previous()

    # ==================== Tab 1: 扫描 ====================
    def _build_scan_tab(self):
        top = tk.Frame(self.tab_scan)
        top.pack(fill="x", padx=10, pady=5)

        tk.Label(top, text="Cookie (含 intranet-sessionid):", fg="#1565C0", font=("", 9, "bold")).pack(anchor="w")
        self.entry_cookie = tk.Text(top, height=3, font=("Consolas", 8), bg="#FFF8E1")
        self.entry_cookie.pack(fill="x", pady=3)
        cached = load_cookie()
        if cached:
            self.entry_cookie.insert("1.0", cached)

        row_settings = tk.Frame(top)
        row_settings.pack(fill="x", pady=3)
        tk.Label(row_settings, text="代理:").pack(side="left")
        self.entry_proxy = tk.Entry(row_settings, width=25)
        self.entry_proxy.pack(side="left", padx=5)
        self.entry_proxy.insert(0, "http://127.0.0.1:7897")

        tk.Label(row_settings, text="  开始日期:").pack(side="left")
        self.entry_start_date = tk.Entry(row_settings, width=12)
        self.entry_start_date.pack(side="left", padx=3)
        self.entry_start_date.insert(0, (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"))

        tk.Label(row_settings, text="租期(天):").pack(side="left", padx=(10, 0))
        self.entry_days = tk.Entry(row_settings, width=5)
        self.entry_days.pack(side="left", padx=3)
        self.entry_days.insert(0, "3")

        row_btn = tk.Frame(top)
        row_btn.pack(fill="x", pady=5)
        self.btn_run = tk.Button(row_btn, text="🚀 全国扫描", command=self.run_scan,
                                 bg="#2E7D32", fg="white", width=14, font=("", 10, "bold"))
        self.btn_run.pack(side="left", padx=5)
        self.btn_stop = tk.Button(row_btn, text="⏹ 停止", command=self.stop_scan, state="disabled", width=8)
        self.btn_stop.pack(side="left", padx=5)
        self.label_status = tk.Label(row_btn, text="就绪", fg="#666")
        self.label_status.pack(side="left", padx=15)
        self.label_progress = tk.Label(row_btn, text="", fg="#1565C0")
        self.label_progress.pack(side="left", padx=10)

        self.progress = ttk.Progressbar(top, mode='determinate')
        self.progress.pack(fill="x", pady=3)

        self.text_log = tk.Text(self.tab_scan, height=30, bg="#ECEFF1", font=("Consolas", 8))
        self.text_log.pack(fill="both", expand=True, padx=10, pady=5)

    # ==================== Tab 2: 结果查询 ====================
    def _build_result_tab(self):
        # 顶部信息
        top = tk.Frame(self.tab_result)
        top.pack(fill="x", padx=10, pady=5)
        self.label_scan_info = tk.Label(top, text="暂无扫描数据", fg="#666", font=("", 9))
        self.label_scan_info.pack(anchor="w")

        # 主体 = 左侧车型选择 + 右侧结果
        body = tk.PanedWindow(self.tab_result, orient=tk.HORIZONTAL, sashwidth=4)
        body.pack(fill="both", expand=True, padx=10, pady=5)

        # -------- 左侧面板: 车型多选 --------
        left = tk.Frame(body, width=220)
        body.add(left, width=220)

        tk.Label(left, text="🚗 车型列表 (多选)", font=("", 9, "bold"), fg="#1565C0").pack(anchor="w", pady=(0, 3))

        # 搜索框
        search_frame = tk.Frame(left)
        search_frame.pack(fill="x", pady=2)
        self.entry_model_search = tk.Entry(search_frame, width=18)
        self.entry_model_search.pack(side="left", fill="x", expand=True)
        self.entry_model_search.bind("<KeyRelease>", self._filter_model_list)
        tk.Button(search_frame, text="清空", width=4, command=self._clear_model_search).pack(side="right", padx=2)

        # 车型 Listbox (多选)
        list_frame = tk.Frame(left)
        list_frame.pack(fill="both", expand=True, pady=3)
        self.listbox_models = tk.Listbox(list_frame, selectmode=tk.EXTENDED, font=("", 9), exportselection=False)
        scrollbar_lb = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox_models.yview)
        self.listbox_models.configure(yscrollcommand=scrollbar_lb.set)
        self.listbox_models.pack(side="left", fill="both", expand=True)
        scrollbar_lb.pack(side="right", fill="y")

        # 操作按钮
        btn_frame = tk.Frame(left)
        btn_frame.pack(fill="x", pady=5)
        tk.Button(btn_frame, text="📊 查看表格", command=self._show_selected, bg="#1565C0", fg="white",
                  font=("", 9, "bold")).pack(fill="x", pady=2)
        tk.Button(btn_frame, text="🗺️ 显示地图", command=self._show_map, bg="#E65100", fg="white",
                  font=("", 9, "bold")).pack(fill="x", pady=2)
        tk.Button(btn_frame, text="📥 导出CSV", command=self.export_csv).pack(fill="x", pady=2)

        # 统计
        self.label_stats = tk.Label(left, text="", fg="#E65100", font=("", 9, "bold"), wraplength=200, justify="left")
        self.label_stats.pack(anchor="w", pady=5)

        # -------- 右侧面板: 结果表格 --------
        right = tk.Frame(body)
        body.add(right)

        cols = ("city", "store", "addr", "car", "desc", "daily", "package", "total")
        self.tree_result = ttk.Treeview(right, columns=cols, show="headings", height=28)
        for col, w, t in [
            ("city", 55, "城市"), ("store", 160, "网点"), ("addr", 200, "地址"),
            ("car", 120, "车型"), ("desc", 130, "配置"),
            ("daily", 60, "日租"), ("package", 60, "套餐"), ("total", 75, "总价(估)")
        ]:
            self.tree_result.heading(col, text=t)
            self.tree_result.column(col, width=w)

        scrollbar_t = ttk.Scrollbar(right, orient="vertical", command=self.tree_result.yview)
        self.tree_result.configure(yscrollcommand=scrollbar_t.set)
        self.tree_result.pack(side="left", fill="both", expand=True)
        scrollbar_t.pack(side="right", fill="y")

        self._all_model_names = []  # 完整列表缓存

    # -------- 车型列表操作 --------
    def _filter_model_list(self, event=None):
        keyword = self.entry_model_search.get().strip().lower()
        self.listbox_models.delete(0, tk.END)
        for name in self._all_model_names:
            if not keyword or keyword in name.lower():
                self.listbox_models.insert(tk.END, name)

    def _clear_model_search(self):
        self.entry_model_search.delete(0, tk.END)
        self._filter_model_list()

    def _get_selected_models(self):
        indices = self.listbox_models.curselection()
        return [self.listbox_models.get(i) for i in indices]

    def _show_selected(self):
        selected = self._get_selected_models()
        if not selected:
            messagebox.showinfo("提示", "请在左侧列表中选择一个或多个车型\n(按住 Ctrl 多选)")
            return
        self._show_filtered(selected)

    def _show_map(self):
        selected = self._get_selected_models()
        if not selected:
            messagebox.showinfo("提示", "请先选择车型")
            return
        # 如果没有坐标映射，尝试从 API 获取
        if not self.city_coords:
            self._ensure_city_coords()
        html = generate_map_html(self.all_records, selected, self.scan_meta, self.city_coords)
        with open(MAP_FILE, 'w', encoding='utf-8') as f:
            f.write(html)
        webbrowser.open(f'file:///{MAP_FILE.replace(os.sep, "/")}')

    def _ensure_city_coords(self):
        """确保有城市坐标映射，优先从缓存加载，否则从 API 获取"""
        # 先从 scan_data 加载
        data = load_scan_data()
        if data and 'city_coords' in data:
            self.city_coords = data['city_coords']
            return
        # 如果没有，从 API 获取
        try:
            cookie = load_cookie()
            proxy = self.entry_proxy.get().strip() if hasattr(self, 'entry_proxy') else None
            cities, _ = fetch_city_list(cookie, proxy or None)
            self.city_coords = {}
            for c in cities:
                name = c.get('cityName', '')
                lon = c.get('cityLon', '')
                lat = c.get('cityLat', '')
                if name and lon and lat:
                    self.city_coords[name] = [float(lon), float(lat)]
            # 保存回 scan_data
            if data:
                data['city_coords'] = self.city_coords
                save_scan_data(data)
        except Exception as e:
            print(f"获取坐标失败: {e}")

    def _show_filtered(self, selected_models):
        for i in self.tree_result.get_children():
            self.tree_result.delete(i)

        days = self.scan_meta.get('days', 1)
        filtered = [r for r in self.all_records if r['modelName'] in selected_models]

        def sort_key(r):
            try:
                return float(r.get('packagePrice', 9999))
            except:
                return 9999
        filtered.sort(key=sort_key)

        for r in filtered:
            try:
                daily = float(r.get('dailyPrice', 0))
            except:
                daily = 0
            try:
                pkg = float(r.get('packagePrice', 0))
            except:
                pkg = 0
            best = pkg if pkg > 0 else daily
            total = f"¥{best * days:.0f}" if best > 0 else "-"
            self.tree_result.insert("", "end", values=(
                r.get('cityName', ''), r.get('deptName', ''), r.get('deptAddress', ''),
                r.get('modelName', ''), r.get('modelDesc', ''),
                f"¥{r.get('dailyPrice', '-')}", f"¥{r.get('packagePrice', '-')}", total
            ))

        if filtered:
            prices = []
            for r in filtered:
                try:
                    prices.append(float(r.get('packagePrice', 0)))
                except:
                    pass
            prices = [p for p in prices if p > 0]
            min_p = min(prices) if prices else 0
            max_p = max(prices) if prices else 0
            cities = len(set(r.get('cityName', '') for r in filtered))
            self.label_stats.config(
                text=f"✅ {len(filtered)} 条记录\n"
                     f"📍 {cities} 个城市有车\n"
                     f"💰 套餐: ¥{min_p:.0f}~¥{max_p:.0f}/天\n"
                     f"📅 {days}天: ¥{min_p*days:.0f}~¥{max_p*days:.0f}"
            )
        else:
            self.label_stats.config(text="未找到")

    # ==================== 数据加载 ====================
    def _try_load_previous(self):
        data = load_scan_data()
        if data and 'records' in data:
            self.all_records = data['records']
            self.scan_meta = data.get('meta', {})
            self.city_coords = data.get('city_coords', {})
            self._refresh_result_tab()
            self.log(f"📂 已加载上次数据: {len(self.all_records)} 条")

    def _refresh_result_tab(self):
        if not self.all_records:
            return
        meta = self.scan_meta
        info = f"扫描: {meta.get('scan_time', '?')} | "
        info += f"{meta.get('start_date', '?')} ~ {meta.get('end_date', '?')} ({meta.get('days', '?')}天) | "
        info += f"{meta.get('city_count', '?')}城市 | {len(self.all_records)}条"
        self.label_scan_info.config(text=info)

        model_set = sorted(set(r['modelName'] for r in self.all_records))
        self._all_model_names = model_set
        self.listbox_models.delete(0, tk.END)
        for name in model_set:
            self.listbox_models.insert(tk.END, name)

    # ==================== 扫描逻辑 ====================
    def log(self, msg):
        self.text_log.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.text_log.see(tk.END)
        self.root.update_idletasks()

    def stop_scan(self):
        self.stop_flag = True

    def run_scan(self):
        raw = self.entry_cookie.get("1.0", tk.END).strip()
        if len(raw) < 20:
            messagebox.showwarning("提示", "请粘贴 Cookie！")
            return
        try:
            days = int(self.entry_days.get().strip())
        except:
            messagebox.showwarning("提示", "请输入正确的天数！")
            return
        self.btn_run.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.stop_flag = False
        self.all_records = []
        threading.Thread(target=self._scan_thread, args=(raw, days), daemon=True).start()

    def _scan_thread(self, raw_cookie, days):
        cookie = clean_cookie(raw_cookie)
        save_cookie(cookie)
        proxy = self.entry_proxy.get().strip() or None
        start_date = self.entry_start_date.get().strip()
        end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")
        p_time = f"{start_date} 10:00"
        r_time = f"{end_date} 10:00"

        self.log(f"📅 {start_date} 10:00 → {end_date} 10:00 ({days}天)")

        self.log("📡 获取城市列表...")
        try:
            cities, cookie = fetch_city_list(cookie, proxy)
            self.log(f"✅ {len(cities)} 个城市")
        except Exception as e:
            self.log(f"❌ {e}")
            self.btn_run.config(state="normal")
            self.btn_stop.config(state="disabled")
            return

        save_cookie(cookie)

        # 建立城市坐标映射
        self.city_coords = {}
        for c in cities:
            name = c.get('cityName', '')
            lon = c.get('cityLon', '')
            lat = c.get('cityLat', '')
            if name and lon and lat:
                self.city_coords[name] = [float(lon), float(lat)]

        limiter = RateLimiter(RATE_LIMIT, RATE_WINDOW)
        total = len(cities)
        self.progress['maximum'] = total
        self.progress['value'] = 0
        scanned = 0
        errors = 0

        for i, city in enumerate(cities):
            if self.stop_flag:
                self.log("⏹ 已停止")
                break

            city_name = city.get('cityName', '?')
            city_id = city.get('cityId', '')
            city_lat = city.get('cityLat', '39.514295')
            city_lon = city.get('cityLon', '116.414348')

            self.label_status.config(text=f"{city_name}")
            self.label_progress.config(text=f"{i+1}/{total} ({len(self.all_records)}条)")
            self.progress['value'] = i + 1

            max_retries = 10
            for attempt in range(max_retries):
                try:
                    limiter.wait_if_needed()
                    res, cookie = search_city(cookie, city_id, p_time, r_time, city_lat, city_lon, proxy)

                    if res.get('status') == 'SUCCESS':
                        depts = res.get('content', {}).get('deptHangModels', [])
                        city_count = 0
                        for dept in depts:
                            dept_lon = dept.get('lon', city_lon)
                            dept_lat = city_lat  # API 没有单独的 lat, 用城市的
                            for m in dept.get('models', []):
                                self.all_records.append({
                                    'cityName': city_name,
                                    'cityId': city_id,
                                    'cityLat': city_lat,
                                    'cityLon': city_lon,
                                    'lon': dept_lon,
                                    'lat': dept_lat,
                                    'deptName': dept.get('deptName', ''),
                                    'deptAddress': dept.get('deptAddress', ''),
                                    'modelName': m.get('modelName', ''),
                                    'modelDesc': m.get('modelDesc', ''),
                                    'modelId': m.get('modelId', ''),
                                    'dailyPrice': m.get('dailyPrice', ''),
                                    'packagePrice': m.get('packagePrice', ''),
                                    'modelImgUrl': m.get('modelImgUrl', ''),
                                })
                                city_count += 1
                        self.log(f"  [{i+1}/{total}] {city_name}: {len(depts)}网点 {city_count}车型")
                        scanned += 1
                        break
                    else:
                        msg = res.get('msg', '?')
                        if any(kw in msg for kw in ['繁忙', '稍后', '频繁', '重试']):
                            wait = 5 * (attempt + 1)
                            self.log(f"  [{i+1}/{total}] ⏳ {city_name}: {msg}，等{wait}s ({attempt+1}/{max_retries})")
                            time.sleep(wait)
                        else:
                            self.log(f"  [{i+1}/{total}] ❌ {city_name}: {msg}")
                            errors += 1
                            break
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.log(f"  [{i+1}/{total}] ⏳ {city_name}: {e}，5s后重试")
                        time.sleep(5)
                    else:
                        self.log(f"  [{i+1}/{total}] ❌ {city_name}: {e}")
                        errors += 1

        self.scan_meta = {
            'scan_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'start_date': start_date, 'end_date': end_date, 'days': days,
            'city_count': scanned, 'total_records': len(self.all_records),
        }
        save_scan_data({'meta': self.scan_meta, 'records': self.all_records, 'city_coords': self.city_coords})
        save_cookie(cookie)

        self.log(f"{'='*50}")
        self.log(f"✅ 完成! {scanned}城市, {errors}失败, {len(self.all_records)}条记录")
        self.label_status.config(text="完成")
        self.progress['value'] = total
        self.btn_run.config(state="normal")
        self.btn_stop.config(state="disabled")
        self._refresh_result_tab()
        self.notebook.select(self.tab_result)

    # ==================== 导出 ====================
    def export_csv(self):
        items = self.tree_result.get_children()
        if not items:
            messagebox.showinfo("提示", "请先选择车型并查看表格")
            return
        path = os.path.join(WORK_DIR, f"shenzhou_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(["城市", "网点", "地址", "车型", "配置", "日租金", "套餐价", "总价(估)"])
            for item in items:
                w.writerow(self.tree_result.item(item)['values'])
        messagebox.showinfo("导出成功", f"已保存到\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    AppUI(root)
    root.mainloop()