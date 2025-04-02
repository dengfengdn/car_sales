import pandas as pd

df=pd.read_csv("car_rank.csv",header=1,names=['日期','id','车型','制造商','价格范围','销量'])

try:
    df["日期"] = pd.to_datetime(df["日期"].astype(str), format="%Y%m")
    df["日期"] = pd.to_datetime(df["日期"], format="%Y-%m").dt.to_period("M").dt.to_timestamp()
except Exception as e:
    print(e)


df["日期"] = df["日期"].dt.strftime("%Y-%m")
df.to_csv("processed_data.csv", index=False,encoding='utf-8-sig')
