import requests
from bs4 import BeautifulSoup
import re
import csv
url = "https://www.dongchedi.com/sales"
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0'
}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")
# 提取页面标题中的日期
title_text = soup.find('title').get_text(strip=True)
match = re.search(r'(\d{4}年\d{2}月)', title_text)
date_str = match.group(1) if match else "未知日期"

# 找到所有车辆信息所在的列表项（根据实际页面结构调整选择器）
car_items = soup.find_all("li", class_="list_item__3gOKl")

# 存储解析后的数据，每一项都是一个列表，包括日期和其他信息
data_list = []

for item in car_items:
    # 提取车辆名称
    name_tag = item.find("a", target="_blank")
    vehicle_name = name_tag.get_text(strip=True) if name_tag else "未知"


    manuf_spec_tag = item.find("span", class_="tw-text-12")
    manuf_spec_text = manuf_spec_tag.get_text(strip=True) if manuf_spec_tag else ""
    parts = manuf_spec_text.split('/')
    manufacturer = parts[0] if len(parts) > 0 else "未知"
    car_level = parts[1] if len(parts) > 1 else "未知"

    # 提取价格区间
    price_tag = item.find("p", class_="tw-leading-22")
    price_range = price_tag.get_text(strip=True) if price_tag else "未知"

    # 提取销量（假设销量在 class 包含 "tw-text-18" 的 <p> 标签中）
    sales_tag = item.find("p", class_=re.compile(r"tw-text-18"))
    sales = sales_tag.get_text(strip=True) if sales_tag else "未知"

    # 将每一项数据整理成一个列表，首项为日期
    data_list.append([date_str, vehicle_name, manufacturer, car_level, price_range, sales])
   # print(data_list)
# 将数据写入 CSV 文件
csv_file = "cars.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    # 写入标题行
    writer.writerow(["日期", "车辆名称", "制造商", "车型规格", "价格区间", "销量"])
    # 写入所有数据行
    writer.writerows(data_list)

print(f"数据已写入 {csv_file}")
