import csv
import requests
import re
import os
from time import sleep
from bs4 import BeautifulSoup

# ================== 配置区 ==================
base_url = "https://www.dongchedi.com/auto/params-carIds-x-{id}"
input_csv = "car_rank.csv"
output_dir = "car_data"
retry_times = 3
request_timeout = 10
# ============================================

def get_unique_ids():
    unique_ids = set()
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                unique_ids.add(int(row.get('id', '').strip()))
            except (KeyError, ValueError):
                pass

    if os.path.exists(output_dir):
        for fname in os.listdir(output_dir):
            if fname.endswith('.csv'):
                with open(os.path.join(output_dir, fname), 'r', encoding='utf-8') as f:
                    done_ids = {int(row.get('ID', '').strip()) for row in csv.DictReader(f) if row.get('ID', '').strip().isdigit()}
                    unique_ids -= done_ids
    return sorted(unique_ids)

def parse_models_config(soup):
    models = []
    try:
        header = soup.find('div', class_='table_head__FNAvn')
        if not header:
            return models

        model_cols = header.select('div.table_is-head-col__1sAQG:not(:first-child)')
        if not model_cols:
            return models

        # 初始化车型数据
        models = [{"型号": "未知车型", "价格": "N/A"} for _ in model_cols]

        # 提取车型名称
        for idx, col in enumerate(model_cols):
            name_tag = col.select_one('a.cell_car__28WzZ, div.cell_car__28WzZ')
            if name_tag:
                models[idx]["型号"] = re.sub(r'[\ue600-\ue6ff●○※]', '', name_tag.get_text(strip=True))

        # 提取官方指导价
        price_row = soup.find('div', class_='cell_official-price__1O2th')
        if price_row:
            price_cells = price_row.find_parent('div', class_='table_row__yVX1h').select('div.cell_official-price__1O2th')
            for idx, cell in enumerate(price_cells[:len(models)]):
                price_text = re.sub(r'[^\d\.万]', '', cell.get_text(strip=True))
                models[idx]["价格"] = price_text + '万' if price_text else "N/A"

        # 提取其他配置信息（包括能源类型）
        config_sections = soup.select('div.table_root__14vH_:not(:first-child)')
        for section in config_sections:
            for row in section.select('div.table_row__yVX1h[data-row-anchor]'):
                label_tag = row.select_one('.cell_label__ZtXlw')
                if not label_tag:
                    continue
                label = label_tag.get_text(strip=True)
                cells = row.select('div.cell_normal__37nRi')
                for idx, cell in enumerate(cells[:len(models)]):
                    text = re.sub(r'[\ue600-\ue6ff●○※]', '', cell.get_text(' ', strip=True))
                    models[idx][label] = text

        # 提取能源类型
        energy_found = False
        # 方法1：基于原有 class 和 label 查找
        for label_div in soup.find_all('div', class_='table_is-label__1wIhd'):
            label_tag = label_div.find('label', class_='cell_label__ZtXlw')
            if label_tag and "能源类型" in label_tag.get_text():
                parent_row = label_div.find_parent('div', class_='table_row__yVX1h')
                if parent_row:
                    energy_cells = parent_row.find_all('div', class_='cell_normal__37nRi')
                    for idx, cell in enumerate(energy_cells[:len(models)]):
                        energy_text = re.sub(r'[\ue600-\ue6ff●○※]', '', cell.get_text(strip=True))
                        models[idx]["能源类型"] = energy_text
                    energy_found = True
                    break

        # 方法2：若未找到，则尝试基于 data-row-anchor 定位（例如 P3.html 中可能使用 fuel_form）
        if not energy_found:
            fuel_row = soup.find('div', {'data-row-anchor': 'fuel_form'})
            if fuel_row:
                energy_cells = fuel_row.find_all('div', class_='cell_normal__37nRi')
                for idx, cell in enumerate(energy_cells[:len(models)]):
                    energy_text = cell.get_text(strip=True)
                    models[idx]["能源类型"] = energy_text
                energy_found = True

        # 方法3：若仍未找到，则尝试基于文本匹配查找包含“能源类型”字样的行
        if not energy_found:
            energy_row = soup.find(lambda tag: tag.name == "div" and "能源类型" in tag.get_text())
            if energy_row:
                parent = energy_row.find_parent('div', class_='table_row__yVX1h')
                if parent:
                    energy_cells = parent.find_all('div', class_='cell_normal__37nRi')
                    for idx, cell in enumerate(energy_cells[:len(models)]):
                        energy_text = re.sub(r'[\ue600-\ue6ff●○※]', '', cell.get_text(strip=True))
                        models[idx]["能源类型"] = energy_text

        # 默认设置为未知
        for model in models:
            if "能源类型" not in model or not model["能源类型"]:
                model["能源类型"] = "未知"
            print(f"车型：{model.get('型号', '未知')}，能源类型：{model.get('能源类型', '未知')}")

    except Exception as e:
        print(f"解析异常: {str(e)}")
        return []

    return models

def fetch_data(id):
    url = base_url.format(id=id)
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'referer': base_url.format(id=''),
        'accept-language': 'zh-CN,zh;q=0.9'
    }

    for attempt in range(retry_times):
        try:
            response = requests.get(url, headers=headers, timeout=request_timeout)
            if not response.ok or "参数配置" not in response.text:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            results = parse_models_config(soup)

            for model in results:
                model['ID'] = str(id)  # 添加 ID 字段

            if len(results) > 0 and any(res["型号"] != "未知车型" for res in results):
                return id, results

        except Exception as e:
            print(f"ID {id} 第{attempt + 1}次请求异常：{str(e)}")
            # sleep(0.5 ** attempt)

    return id, None


def main():
    os.makedirs(output_dir, exist_ok=True)
    ids = get_unique_ids()
    if not ids:
        print("没有需要处理的新ID")
        return

    all_data = []  # 存放所有车型数据
    field_set = set()

    print("正在收集字段信息...")
    for idx, id in enumerate(ids, 1):
        print(f"[{idx}/{len(ids)}] 扫描ID: {id}")
        _, results = fetch_data(id)
        if results:
            for model in results:
                # 数据清洗过滤
                if model["型号"] == "未知车型":
                    continue
                if model["价格"] in ["N/A", "万"]:
                    continue

                # 字段值清洗与合并
                keys = list(model.keys())  # 创建静态键列表
                for k in keys:
                    # 合并所有续航里程相关字段
                    if "续航里程" in k and k != "续航里程":
                        if "续航里程" not in model:
                            model["续航里程"] = model[k]
                        del model[k]  # 直接删除旧键
                        continue  # 跳过后续处理

                    # 处理前再次检查键是否存在
                    if k not in model:
                        continue

                    # 删除空值字段
                    if model[k] in ["N/A", "-", ""]:
                        del model[k]

                # 验证有效字段数量（至少保留型号、价格、能源类型）
                valid_fields = sum(1 for v in model.values() if v not in ["N/A", ""])
                if valid_fields < 3:
                    continue

                field_set.update(model.keys())
                all_data.append(model)



    base_fields = ["ID", "型号", "价格", "能源类型"]
    other_fields = sorted([f for f in field_set if f not in base_fields])
    all_fields = base_fields + other_fields

    output_path = os.path.join(output_dir, "car_data_clean.csv")
    print("\n开始写入清洗后数据...")
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=all_fields, extrasaction='ignore')
        writer.writeheader()

        clean_count = 0
        for model in all_data:
            # 最终格式验证
            if all(v not in model for v in ["续航里程", "驱动方式", "电池容量(kWh)"]):
                continue

            # 价格格式统一
            if '万' not in model["价格"] and re.search(r'\d', model["价格"]):
                model["价格"] += "万"

            writer.writerow(model)
            clean_count += 1

    print(f"✅ 有效数据已写入 {output_path}，共 {clean_count} 条记录")


if __name__ == "__main__":
    main()
