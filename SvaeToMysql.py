import pandas as pd
import mysql.connector
from mysql.connector import Error

# 配置 MySQL 连接参数
config = {
    "host": "localhost",  # 本地 MySQL 地址
    "user": "root",  # 用户名（根据实际修改）
    "password": "Yzy@123456",  # 密码（根据实际修改）
    "database": "car_info"  # 数据库名称（提前创建或自动创建）
}

# CSV 文件路径
csv_file = "car_data_all.csv"


def main():
    try:
        # 读取 CSV 文件
        df = pd.read_csv(csv_file)
        # 将 "日期" 列转换为日期格式，转换成每月第一天
       # df["日期"] = pd.to_datetime(df["日期"], format="%Y-%m").dt.to_period("M").dt.to_timestamp()

        # 连接 MySQL 数据库
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 如果数据库不存在，则创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS car_info")
        conn.database = "car_info"  # 切换到目标数据库

        # 创建数据表（根据 CSV 列定义字段类型）
        create_table_query = """
               CREATE TABLE IF NOT EXISTS `car_data` (
  
"""
        cursor.execute(create_table_query)

        # 插入数据（批量插入）
        # 注意：这里明确指定了插入字段顺序，与 CSV 文件中的列顺序一一对应：
        # CSV 顺序：日期, id, 车型, 制造商, 价格范围, 销量
        insert_query = """
                INSERT INTO `car_data` (
  
)
VALUES (
  
);

                """

        # 将 DataFrame 转换为元组列表
        data = [tuple(row) for row in df.itertuples(index=False, name=None)]

        # 执行批量插入
        cursor.executemany(insert_query, data)
        conn.commit()
        print(f"成功插入 {cursor.rowcount} 条数据！")

    except Error as e:
        print("MySQL 错误:", e)
        if conn.is_connected():
            conn.rollback()  # 回滚事务
    except Exception as ex:
        print("其他错误:", ex)
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("数据库连接已关闭")


if __name__ == "__main__":
    main()