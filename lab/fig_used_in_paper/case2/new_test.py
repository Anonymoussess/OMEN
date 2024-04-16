import numpy as np
import matplotlib.pyplot as plt
import sys
import pandas as pd
import os
import matplotlib

sys.path.append('..')
import utils

# 设置随机种子以便结果可复现
np.random.seed(0)

# 生成基础数据点


# 假设的 utils.get_wave_list 函数和 get_data 函数
# 如果您没有这些函数，请替换为您实际的函数实现
def get_wave_list(directory):
    """List CSV files in the given directory"""
    return [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.csv')]


# 提供的 get_df 函数，读取和处理 csv 文件
def get_data(wave_file, column_name):
    wave_df = pd.read_csv(wave_file)
    holo_time_offset = 0 * 1000
    wave_df['time'] = wave_df['time'] + holo_time_offset

    min_time = wave_df['time'].min() + 240
    max_time = min_time + 480

    wave_df = wave_df.loc[wave_df['time'] <= max_time]
    wave_df = wave_df.loc[wave_df['time'] >= min_time]

    wave_df['time'] = wave_df['time'] - wave_df['time'].iloc[0]

    return wave_df[column_name]

def get_sin_wave_spe(length):
    """Generate a sin wave specified for the given length"""
    time = np.linspace(0, 360, length)  # 时间范围为 0 到 120 秒
    amplitude = (5000 - 400) / 2  # 振幅为最高值和最低值的一半
    phase = 120 * 0.75  # 初始相位为 200
    sine_wave = amplitude * np.sin(2 * np.pi * (time + phase) / 120) + (5000 + 400) / 2
    sine_wave[sine_wave > 4000] = 4000
    return time, sine_wave

# 指定的文件夹和列名
base_dir = './avg_res/'
column_name = 'bitrate'

# 获取所有波形文件列表
wave_list = get_wave_list(base_dir)

# 读取数据并生成拟合数据
fit_data_1 = get_data(wave_list[0], column_name)
fit_data_2 = get_data(wave_list[1], column_name)
fit_data_3 = get_data(wave_list[2], column_name)
fit_data_4 = get_data(wave_list[3], column_name)

# 根据读取的数据长度生成准确数据
length = len(fit_data_1)  # 假设所有数据长度一致
x, accurate_data = get_sin_wave_spe(length)

# 计算方差的累积均值
def cumulative_mean_variance(fit_data):
    diff_squared = (fit_data - accurate_data) ** 2
    cum_variance = np.cumsum(diff_squared)
    return cum_variance

cum_var_1 = cumulative_mean_variance(fit_data_1)
cum_var_2 = cumulative_mean_variance(fit_data_2)
cum_var_3 = cumulative_mean_variance(fit_data_3)
cum_var_4 = cumulative_mean_variance(fit_data_4)

# 配置 matplotlib 使用 Times New Roman 字体
matplotlib.rcParams['font.family'] = 'Times New Roman'

# 创建3D图形
fig = plt.figure(figsize=(20, 20))
ax = fig.add_subplot(111, projection='3d')
# 设置坐标轴范围
ax.set_xlim([0, 350])
# ax.set_ylim([-1, 1])
ax.set_zlim([0, 4000])

ax.set_box_aspect([6, 1, 1])  # 比例因子

# 设置三维图形的视角
ax.view_init(elev=40, azim=-90)

# 提供的颜色HEX值
color_hex = ['#7B1FA2', '#1976D2', '#00a087', '#ff7f0e', '#D32F2F']
# 将准确数据的颜色设置为给定的第一个颜色
accurate_data_color = color_hex[0]
# 将拟合数据的颜色设置为接下来的四个颜色
color_hex = color_hex[1:]

# 绘制准确数据线，z为纵坐标，y=0
ax.plot(x, np.zeros_like(x), accurate_data, color=accurate_data_color, label='Optimal', linewidth=2)

data_sets = [fit_data_1, fit_data_2, fit_data_3, fit_data_4]

line_styles = ['-.', ':', '--', '-', '-']  # 不同的线条样式

label_line = ['Bola', 'Comyco', 'Pensieve', 'OMEN']

# 绘制准确数据和拟合数据线，z为纵坐标，y=0
for i, (data, color, line_style) in enumerate(zip(data_sets, color_hex, line_styles), start=0):
    y = np.zeros_like(x)  # y 值固定为0
    ax.plot(x, y, data, color=color, linestyle=line_style, label=label_line[i], linewidth=2)

for cum_var, color, line_style in zip([cum_var_1, cum_var_2, cum_var_3, cum_var_4], color_hex, line_styles):
    cum_var_values = cum_var.values
    Z_1 = np.zeros_like(x)  # Z坐标初始化为0，因为我们要在z=0平面绘制曲线

    # 绘制方差表面的顶部和底部边界曲线
    ax.plot(x, Z_1, cum_var_values, zdir='y', linestyle=line_style, color=color, linewidth=2)  # 顶部边界曲线
    ax.plot(x, Z_1, -cum_var_values, zdir='y', linestyle=line_style, color=color, linewidth=2)  # 底部边界曲线

# 绘制方差区域，y为纵坐标，z=0
for cum_var, color in zip([cum_var_1, cum_var_2, cum_var_3, cum_var_4], color_hex):
    # 创建网格数据
    X, Y = np.meshgrid(x, [-1, 1])
    cum_var_values = cum_var.values
    Z = cum_var_values.reshape(1, -1) * Y  # Y方向上的扩展是方差数据的对称展示

    # 绘制方差表面
    ax.plot_surface(X, Z, Y * 0, color=color, alpha=0.2, rstride=10, cstride=1)



# 设置轴标签
ax.set_xlabel('Time (s)')
ax.set_ylabel('Cumulative Deviation (Kbps)')
ax.set_zlabel('Bitrate (Kbps)')

# 设置图例，并调整字体大小
ax.legend(loc=(0.05, 0.60), fontsize=12, frameon=True, facecolor='white', edgecolor='black', ncol=5)
plt.show()
