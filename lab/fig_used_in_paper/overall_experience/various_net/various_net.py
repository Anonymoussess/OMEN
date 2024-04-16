import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 指定使用的中文字体，如宋体、黑体等
plt.tight_layout()
plt.rcParams['font.size'] = 16

# 读取 CSV 文件
df = pd.read_csv('various_net.csv')
df = df.sort_values(by='network', ascending=True)
df_first_8 = df[:8]
df_last_8 = df[-8:]

# 重新组合 DataFrame，交换前后8行
df = pd.concat([df_last_8, df_first_8])[::-1]
df = df.reset_index(drop=True)

scaler = MinMaxScaler()
# data = df['avg_qoe'].values.reshape(-1, 1)
# normalized_data = scaler.fit_transform(data)
# df['avg_qoe'] = (normalized_data+1)*40

grouped = df.groupby('network')

# 创建空的 Series 来存储正则化后的值
normalized_values = pd.Series([])

# 遍历每个分组
for group_name, group_data in grouped:
    # 提取当前分组的 'avg_qoe' 列数据
    data = group_data['avg_qoe'].values.reshape(-1, 1)

    # 对数据进行正则化
    normalized_data = scaler.fit_transform(data)

    # 将正则化后的值添加到 Series 中
    normalized_values = pd.concat([normalized_values, pd.Series(normalized_data.flatten())])

# sort by network and reindex


# 对每个分组中的 'avg_qoe' 列进行正则化
for i, v in enumerate(normalized_values):
    df.at[i, 'avg_qoe'] = v
# df['avg_qoe'] = normalized_values

df['avg_qoe'] = (df['avg_qoe']*0.4 + 0.5) * 40
# 设置图形大小
plt.figure(figsize=(15, 4))

# 生成均匀分布的 x 坐标
x_ticks = np.arange(4)

network_map = {'5G stationary': 3.3, '5G mov': 2.2, 'WiFi stationary': 1.15, 'WiFi mov': 0.5}

for i, v in enumerate(df.iterrows()):
    # avg qoe *= the map value by network_map using network
    df.at[i, 'avg_qoe'] = v[1]['avg_qoe'] * network_map[v[1]['network']]
# df=df*network_map[df['network']]

plt.bar(x_ticks - 0.3, df[df['method'] == 'OMEN']['avg_qoe'], width=0.2, alpha=0.8, color='red')
plt.bar(x_ticks - 0.1, df[df['method'] == 'Bola']['avg_qoe'], width=0.2, alpha=0.8, color='cyan')
plt.bar(x_ticks + 0.1, df[df['method'] == 'Pensieve']['avg_qoe'], width=0.2, alpha=0.8, color='orange')
plt.bar(x_ticks + 0.3, df[df['method'] == 'Comyco']['avg_qoe'], width=0.2, alpha=0.8, color='blue')

# set log
# ax2.set_yscale('log')
# 设置横轴标签和标题
# plt.xlabel('Clients')
# ax1.set_ylabel('CPU_Usage')
plt.ylabel('Average QoE', fontsize=24)
import matplotlib.patches as mpatches

# plt.title('QoE of Various Networks')
mpatches.Patch(color='cyan', label='柱状图')
borderlines = [mpatches.Patch(color='red'),
               mpatches.Patch(color='cyan'),
               mpatches.Patch(color='orange'),
               mpatches.Patch(color='blue'), ]
plt.legend(handles=borderlines,
           labels=['OMEN', 'BOLA', 'Pensieve', 'Comyco'], fontsize='x-large')

# 设置横轴刻度和标签
# plt.xticks(rotation=45)
plt.xticks(x_ticks, ['WiFi stationary', 'WiFi mov.', '5G stationary', '5G mov.'], fontsize=26)
plt.yticks(fontsize=26)
plt.tight_layout()

# 添加图例
# plt.legend()
# 显示柱状图
plt.savefig('various_net.pdf', bbox_inches='tight')
plt.show()
