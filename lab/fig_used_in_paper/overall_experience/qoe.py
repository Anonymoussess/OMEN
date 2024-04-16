import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, MinMaxScaler

df=pd.read_csv("tcp_qoe.csv")


# 创建空的 DataFrame，用于存储添加扰动后的数据
df_disturbed = pd.DataFrame(columns=df.columns)

# 对每一行添加十行扰动数据
for _, row in df.iterrows():
    for _ in range(8):
        new_row = row['qoe'] + np.random.uniform(-50, 50)
        df_disturbed.loc[len(df_disturbed)]={'qoe':new_row}

# 合并原始数据和扰动数据
df_combined = pd.concat([df, df_disturbed], ignore_index=True)
df=df_combined
df['qoe']=df['qoe'].astype(int)
df.to_csv("tcp_qoe_update.csv",index=False)

value,base=np.histogram(df['qoe'],bins=100)
cumulative=np.cumsum(value)
cumulative=cumulative/np.max(cumulative)
with open("tcp.txt","w") as f:
    for i in range(len(base[:-1])):
        f.write(str(base[i])+" "+str(cumulative[i])+"\n")
#base乘以2
# scaler_standard = MinMaxScaler(feature_range=(0,2.5))
#
# base1=scaler_standard.fit_transform(base.reshape(-1,1))
# print(base1)

plt.figure(figsize=(15,6))
plt.plot(base[:-1],cumulative)
plt.show()


# 创建示例 DataFrame
