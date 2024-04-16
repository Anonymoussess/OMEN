import pandas as pd #注意时间偏移，因为有的文件我手动在CSV文件里已经加了偏置，所以代码里没有加time_flit 
import matplotlib.pyplot as plt
import numpy as np

def plot_throughput_and_bitrate(throughput_csv_path1, throughput_csv_path2,bitrate_csv_path1,bitrate_csv_path2,output_image_path):
    # 读取并转换吞吐量数据的时间列为数值类型
    df_throughput1 = pd.read_csv(throughput_csv_path1)
    # 读取并转换比特率数据的时间列为数值类型
    df_throughput2 = pd.read_csv(throughput_csv_path2)

    window_size = 20  # 窗口大小，根据你的数据调整
    df_throughput1['Smoothed'] = df_throughput1['Throughput_kbps'].rolling(window=window_size).mean()
    df_throughput2['Smoothed'] = df_throughput2['Throughput_kbps'].rolling(window=window_size).mean()
    df_bitrate1 = pd.read_csv(bitrate_csv_path1)
    df_bitrate1['Time'] = pd.to_datetime(df_bitrate1['Time'], format='%Y-%m-%d %H:%M:%S',errors='coerce')
    start_time1 = df_bitrate1['Time'].min()
    df_bitrate1['Time'] = (df_bitrate1['Time'] - start_time1).dt.total_seconds()
    # 读取并转换比特率数据的时间列为数值类型
    # 读取比特率数据并转换时间列 时间列类型转化 注意格式，尤其是连接的时候是-还是/
    df_bitrate2 = pd.read_csv(bitrate_csv_path2)
    # 转换时间列为datetime类型
    df_bitrate2['Time'] = pd.to_datetime(df_bitrate2['Time'], format='%Y-%m-%d %H:%M:%S',errors='coerce')
    # 转换时间为相对于第一个时间点的秒数
    start_time2 = df_bitrate2['Time'].min()
    time_flit = 24
    df_bitrate2['Time'] = (df_bitrate2['Time'] - start_time2).dt.total_seconds()+time_flit
    fig, ax1 = plt.subplots(figsize=(12, 3))
    # 采样数据点
    sample_ratio = 20  # 采样比例，可以根据需要调整
    throughput_sample_indices = np.linspace(0, len(df_throughput1) - 1, len(df_throughput1) // sample_ratio, dtype=int)
    bitrate_sample_indices = np.linspace(0, len(df_throughput2) - 1, len(df_throughput2) // sample_ratio, dtype=int)

    # 绘图
    plt.figure(figsize=(12, 5))
    plt.plot(
        df_throughput1.iloc[throughput_sample_indices]['Time'],
        df_throughput1.iloc[throughput_sample_indices]['Smoothed'],
        label='Client1 Throughput',
        color='blue',  # 蓝色
        linestyle='solid',  # 实线
        marker='',  # 不显示标记
        linewidth=1  # 线条较细
    )
    plt.plot(
        df_throughput2.iloc[bitrate_sample_indices]['Time'] + time_flit ,
        df_throughput2.iloc[bitrate_sample_indices]['Smoothed'],
        label='Client2 Throughput',
        color='orange',  # 橙色
        linestyle='solid',  # 实线
        marker='',  # 不显示标记
        linewidth=1  # 线条较细
    )
    plt.plot(
        df_bitrate1['Time'],
        df_bitrate1['Bitrate_Downloading'],
        label='Client1 Bitrate',
        color='blue',  # 蓝色
        linestyle='dashed',  # 虚线
        linewidth=1  # 线条较细
    )
    plt.plot(
        df_bitrate2['Time'],
        df_bitrate2['Bitrate_Downloading'],
        label='Client2 Bitrate',
        color='orange',  # 橙色
        linestyle='dashed',  # 虚线
        linewidth=1  # 线条较细
    )
    # 设置图表标题和坐标轴标签
    plt.title(' Throughput and Bitrate Over Time')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Throughput/Bitrate (kbps)', fontsize=20)
    plt.xticks(fontsize=18)  # 设置 x 轴刻度的字体大小
    plt.yticks(fontsize=18)  # 设置 y 轴刻度的字体大小
    # 显示图例
    plt.legend()

    # 调整布局
    plt.tight_layout()

    # 保存图表
    plt.savefig(output_image_path)

    # 显示图表
    plt.show()

# 调用函数进行绘图
throughput_csv_path1 = r'.\rl\client1_0-pcap.csv'
throughput_csv_path2 = r'.\rl\client2_0-pcap.csv'
bitrate_csv_path1 = r'.\rl\client1_0.xlsx'
bitrate_csv_path2 = r'.\rl\client2_0.xlsx'
output_image_path = r'.\rl\rl.svg'
plot_throughput_and_bitrate(throughput_csv_path1, throughput_csv_path2,bitrate_csv_path1,bitrate_csv_path2,output_image_path)
plt.clf()
plt.close()