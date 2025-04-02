import requests
import pandas as pd
import time
import os


def getHTML(url):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None


def parse_json(data, month):
    if not data or "data" not in data:
        return []

    car_list = data["data"]["list"]
    result = []
    for car in car_list:
        info = {
            "时间": month,
            "id": car.get("series_id"),
            "车型": car.get("series_name", ""),
            "制造商": car.get("brand_name", ""),
            "价格区间": car.get("price", ""),
            "销量": car.get("count", 0)
        }
        result.append(info)
    return result


def save_csv(data, filename):
    if not data:
        return

    df = pd.DataFrame(data)
    # 这里直接写入，不使用追加模式
    df.to_csv(filename, mode='a', index=False, header=not os.path.exists(filename), encoding="utf-8-sig")
    print(f"数据已保存至 {filename}")


if __name__ == '__main__':
    month_list = [202202,202203, 202204, 202205, 202206, 202207, 202208, 202209, 202210, 202211, 202212, 202301, 202302,
                  202303, 202304, 202305, 202306, 202307, 202308, 202309, 202310, 202311, 202312, 202401, 202402,
                  202403, 202404, 202405, 202406, 202407, 202408, 202409, 202410, 202411, 202412, 202501, 202502]

    '''filename = f"car_rank_{month}.csv"
    # 删除旧文件，确保每次运行都是新文件
    if os.path.exists(filename):
        os.remove(filename)'''

    # offset 每次增加 10，从 0 到 490（共50页，每页10条数据
    for month in month_list:
        for offset in range(0, 500, 10):
            url = (
                    'https://www.dongchedi.com/motor/pc/car/rank_data?'
                    'aid=1839&app_name=auto_web_pc&city_name=%E9%93%B6%E5%B7%9D&count=10'
                    '&offset=' + str(offset) +
                    '&month=' + str(month) +
                    '&new_energy_type=&rank_data_type=11&brand_id=&price=&manufacturer=&series_type=&nation=0'
            )
            content = getHTML(url)
            result = parse_json(content, month)
            save_csv(result, f"car_rank.csv")
            print('保存成功，第 offset = ' + str(offset) + ' 的数据')
            #time.sleep(0.5)
