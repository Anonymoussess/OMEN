import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

import utils

plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 指定使用的中文字体，如宋体、黑体等
plt.tight_layout()
plt.rcParams['font.size'] = 16


fig, ax1 = plt.subplots(figsize=(6,5))
ax2 = ax1.twinx()

dfs = utils.apply_function_to_files(utils.get_wave_list('.'), utils.get_df)
# dfs = utils.apply_function_to_files(dfs, utils.convert_records_to_secondly)
# ==============================================================================

x = dfs[0]['time']
df = utils.extract_column_from_df(dfs, ['bitrate'])

# select first 60 rows
x = [a for a in x if a < 60]
df = df.iloc[:len(x)]

for column in df.columns:
    df[column] = df[column].rolling(window=5, min_periods=1).mean()  # 使用窗口大小为3的滑动平均
    df[column] = df[column].rolling(window=3, min_periods=1).mean()

# 计算上下界及平均值
result = pd.DataFrame()
result["ub"] = df.max(axis=1)
result["lb"] = df.min(axis=1)
result["avg"] = df.mean(axis=1)
upper_bound = np.array(result['ub'])
lower_bound = np.array(result['lb'])
average = np.array(result['avg'])
bitFlag = np.where(average >= 3886)[0][0]

# 绘制曲线
for column in df.columns:
    ax1.plot(x, df[column], alpha=0.1)

ax1.fill_between(x, lower_bound, upper_bound, color='red', alpha=0.3)
ax1.plot(x, upper_bound, color='orange', alpha=0.6),
ax1.plot(x, lower_bound, color='cyan', alpha=0.6),
ax1.plot(x, average, linewidth=2, color='red')
# ax1.set_ylabel(f'bitrate(kbps)', fontsize=20)
ax1.set_ylim(0, 4000)

# ==============================================================================

# ==============================================================================
dfs = utils.apply_function_to_files(dfs, utils.convert_records_to_secondly)
x = dfs[0]['Time']
df= utils.extract_column_from_df(dfs, ['buffer'])
# bufferFlag = index = df.index[df['buffer'] > 29][0]

x = [a for a in x if a < 60]
df = df.iloc[:len(x)]

for column in df.columns:
    df[column] = df[column].rolling(window=5, min_periods=1).mean()  # 使用窗口大小为3的滑动平均
    df[column] = df[column].rolling(window=3, min_periods=1).mean()

# 计算上下界及平均值
result = pd.DataFrame()
result["ub"] = df.max(axis=1)
result["lb"] = df.min(axis=1)
result["avg"] = df.mean(axis=1)
upper_bound = np.array(result['ub'])
lower_bound = np.array(result['lb'])
average = np.array(result['avg'])
bufferFlag = np.where(average > 29)[0][0]

# 绘制曲线
for column in df.columns:
    ax2.plot(x, df[column], alpha=0.1)

ax2.fill_between(x, lower_bound, upper_bound, color='red', alpha=0.3)
ax2.plot(x, upper_bound, color='orange', alpha=0.6),
ax2.plot(x, lower_bound, color='cyan', alpha=0.6),
ax2.plot(x, average, linewidth=2, color='blue')
# ax2.set_ylabel(f'buffer(s)', fontsize=20)
ax2.set_ylim(0, 60)
# ==============================================================================


plt.axvline(x=bitFlag, color='r', linestyle='--')
plt.axvline(x=bufferFlag, color='b', linestyle='--')

plt.xlabel('Time(s)')
borderlines = [plt.Line2D([], [], color='orange'),
               plt.Line2D([], [], color='cyan'),
               plt.Line2D([], [], color='red'),
               plt.Line2D([], [], color='blue')]
# plt.legend(handles=borderlines,labels=['Upper Bound', 'Lower Bound', 'Bitrate Average','Buffer Average'])
# plt.title('')
plt.xlim(0, 60)
ax1.set_xlabel('Time (s)', fontsize=20)

plt.savefig(f"bola.pdf",bbox_inches='tight')
plt.show()
