import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 指定使用的中文字体，如宋体、黑体等
plt.tight_layout()
plt.rcParams['font.size'] = 16


plt.figure(figsize=(6,4))

# 生成均匀分布的 x 坐标
x_ticks = np.arange(2)

plt.bar(x_ticks - 0.1, [1657,1657], width=0.2, alpha=0.8, color='#d2d2d2')
plt.bar(x_ticks + 0.1, [1737.4,0], width=0.2, alpha=0.8, color='#f8d793')
plt.bar(x_ticks + 0.1, [0,1876.33], width=0.2, alpha=0.8, color='#9ee092')


plt.ylabel('Average QoE', fontsize=24)
import matplotlib.patches as mpatches

# plt.title('QoE of Various Networks')
mpatches.Patch(color='cyan', label='柱状图')
borderlines = [mpatches.Patch(color='#d2d2d2'),
               mpatches.Patch(color='#f8d793'),
               mpatches.Patch(color='#9ee092'), ]
plt.legend(handles=borderlines,
           labels=['BOLA', 'CARA w/o OMEN', 'CARA w OMEN'],loc='lower center')

# 设置横轴刻度和标签
# plt.xticks(rotation=45)
plt.xticks(x_ticks, [], fontsize=24)
plt.yticks(fontsize=24)
plt.ylim(1000,2000)
plt.tight_layout()

# 添加图例
# plt.legend()
# 显示柱状图
plt.savefig('sub.pdf',bbox_inches='tight')
plt.show()
