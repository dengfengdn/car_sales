from idlelib.iomenu import encoding

import pandas as pd

file_path='processed_data.csv'
df=pd.read_csv(file_path,encoding='utf-8')
#print(df.loc[0:3])
df.loc[:,'价格范围']=df['价格范围'].str.replace("万","")
print(df['日期'].isnull)