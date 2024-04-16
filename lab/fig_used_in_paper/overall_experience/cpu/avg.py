

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 指定使用的中文字体，如宋体、黑体等
plt.tight_layout()
plt.rcParams['font.size'] = 20


# 读取 CSV 文件
df = pd.read_csv('avg.csv')
df=df.sort_values(by='File')
df['File']=df['File'].astype(int)
# 设置图形大小
fig,ax1=plt.subplots(figsize=(6,4))
ax2=ax1.twinx()

# 生成均匀分布的 x 坐标
x_ticks = np.arange(len(df))

# 绘制 CPU 占用率柱状图
ax1.bar(x_ticks + 0.15, df['CPU_Usage'], width=0.2, label='CPU Usage',color='#f8d793')

# 绘制 Original_Data_Size 柱状图
ax2.bar(x_ticks - 0.15, df['Original_Data_Size']/df['File']/1000/2000*10000, width=0.2
        ,  label='Overhead',color='#9ee092')

# set log
# ax2.set_yscale('log')
# 设置横轴标签和标题
ax1.set_xlabel('Clients',fontsize=20)
ax1.set_ylabel('CPU Usage (%)',fontsize=20)
ax2.set_ylabel('Communication overhead (‱)',fontsize=20)

ax1.set_ylim(0,10)
ax2.set_ylim(0,10)
# plt.title('CPU Usage and send rate')

# 设置横轴刻度和标签
plt.xticks(rotation=45)
plt.xticks(x_ticks, df['File'])
plt.tight_layout()

# 添加图例
fig.legend(ncol=2,bbox_to_anchor=(0.5, 1.1), loc='upper center')
# 显示柱状图
plt.savefig('server-cost.pdf',bbox_inches='tight')
plt.show()
