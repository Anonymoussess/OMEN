import pandas as pd #注意时间偏移，因为有的文件我手动在CSV文件里已经加了偏置，所以代码里没有加time_flit 
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

def read_data(file_path):
    # 根据文件扩展名选择合适的Pandas读取函数
    _, file_extension = os.path.splitext(file_path)
    if file_extension == '.csv':
        return pd.read_csv(file_path)
    elif file_extension in ['.xls', '.xlsx']:
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format: {}".format(file_extension))

def plot_throughput_and_bitrate(throughput_csv_path1, throughput_csv_path2,bitrate_csv_path1,bitrate_csv_path2,output_image_path):
    # 读取并转换吞吐量数据的时间列为数值类型
    df_throughput1 = pd.read_csv(throughput_csv_path1)
    # 读取并转换比特率数据的时间列为数值类型
    df_throughput2 = pd.read_csv(throughput_csv_path2)

    window_size = 20  # 窗口大小，根据你的数据调整
    df_throughput1['Smoothed'] = df_throughput1['Throughput_kbps'].rolling(window=window_size).mean()
    df_throughput2['Smoothed'] = df_throughput2['Throughput_kbps'].rolling(window=window_size).mean()
    print(bitrate_csv_path1)
    df_bitrate1 = read_data(bitrate_csv_path1)
    df_bitrate1['Time'] = pd.to_datetime(df_bitrate1['Time'], format='%Y-%m-%d %H:%M:%S',errors='coerce')
    start_time1 = df_bitrate1['Time'].min()
    # end_limit1 = start_time1 + pd.Timedelta(seconds=70)
    # df_bitrate1=df_bitrate1.loc[df_bitrate1['Time']<=end_limit1]
    df_bitrate1['Time'] = (df_bitrate1['Time'] - start_time1).dt.total_seconds()
    # 读取并转换比特率数据的时间列为数值类型
    # 读取比特率数据并转换时间列 时间列类型转化 注意格式，尤其是连接的时候是-还是/
    df_bitrate2 = read_data(bitrate_csv_path2)
    # 转换时间列为datetime类型
    df_bitrate2['Time'] = pd.to_datetime(df_bitrate2['Time'], format='%Y-%m-%d %H:%M:%S',errors='coerce')
    # 转换时间为相对于第一个时间点的秒数
    start_time2 = df_bitrate2['Time'].min()
    # end_limit2=start_time2+ pd.Timedelta(seconds=70)
    # df_bitrate2=df_bitrate2.loc[df_bitrate2['Time']<=end_limit2]
    time_flit = 24
    df_bitrate2['Time'] = (df_bitrate2['Time'] - start_time2).dt.total_seconds()+time_flit

    # fig, ax1 = plt.subplots(figsize=(12, 3))
    # plt.xticks()
    #
    # # 采样数据点
    # sample_ratio = 20  # 采样比例，可以根据需要调整
    # throughput_sample_indices = np.linspace(0, len(df_throughput1) - 1, len(df_throughput1) // sample_ratio, dtype=int)
    # bitrate_sample_indices = np.linspace(0, len(df_throughput2) - 1, len(df_throughput2) // sample_ratio, dtype=int)
    #
    # 使用滑动窗口计算平均值
    window_size = 1  # 滑动窗口的大小，根据您的数据调整
    df_throughput1_smoothed = df_throughput1['Smoothed'].rolling(window=window_size).mean()
    df_throughput2_smoothed = df_throughput2['Smoothed'].rolling(window=window_size).mean()
    df_bitrate1_smoothed = df_bitrate1['Bitrate_Downloading'].rolling(window=window_size).mean()
    df_bitrate2_smoothed = df_bitrate2['Bitrate_Downloading'].rolling(window=window_size).mean()
    #
    # # 计算波动范围（标准差）
    # std_throughput1 = df_throughput1['Smoothed'].rolling(window=window_size).std()
    # std_throughput2 = df_throughput2['Smoothed'].rolling(window=window_size).std()
    # std_bitrate1 = df_bitrate1['Bitrate_Downloading'].rolling(window=window_size).std()
    # std_bitrate2 = df_bitrate2['Bitrate_Downloading'].rolling(window=window_size).std()
    #
    # # 开始绘图
    # plt.figure(figsize=(12, 6))
    #
    # # 绘制Throughput平均曲线和波动范围
    # plt.plot(df_throughput1['Time'], df_throughput1_smoothed, label='Client1 Throughput', color='blue', linestyle='-',
    #          linewidth=2)
    # plt.fill_between(df_throughput1['Time'], df_throughput1_smoothed - std_throughput1,
    #                  df_throughput1_smoothed + std_throughput1, color='blue', alpha=0.3)
    #
    # plt.plot(df_throughput2['Time'] + time_flit, df_throughput2_smoothed, label='Client2 Throughput', color='red',
    #          linestyle='-', linewidth=2)
    # plt.fill_between(df_throughput2['Time'] + time_flit, df_throughput2_smoothed - std_throughput2,
    #                  df_throughput2_smoothed + std_throughput2, color='red', alpha=0.3)
    #
    # # 绘制Bitrate平均曲线和波动范围
    # plt.plot(df_bitrate1['Time'], df_bitrate1_smoothed, label='Client1 Bitrate', color='blue', linestyle='--',
    #          linewidth=2)
    # plt.fill_between(df_bitrate1['Time'], df_bitrate1_smoothed - std_bitrate1, df_bitrate1_smoothed + std_bitrate1,
    #                  color='blue', alpha=0.3)
    #
    # plt.plot(df_bitrate2['Time'], df_bitrate2_smoothed, label='Client2 Bitrate', color='red', linestyle='--',
    #          linewidth=2)
    # plt.fill_between(df_bitrate2['Time'], df_bitrate2_smoothed - std_bitrate2, df_bitrate2_smoothed + std_bitrate2,
    #                  color='red', alpha=0.3)
    #
    # # 设置图表标题和坐标轴标签
    # plt.title('Throughput and Bitrate Over Time')
    # plt.xlabel('Time (seconds)')
    # plt.ylabel('Throughput/Bitrate (kbps)')
    # plt.xticks(fontsize=14)  # 设置 x 轴刻度的字体大小
    # plt.yticks(fontsize=14)  # 设置 y 轴刻度的字体大小
    # # 显示图例
    # plt.legend(fontsize=14)
    #
    # # 显示网格
    # plt.grid(True)
    #
    # # 调整布局
    # plt.tight_layout()
    #
    # # 保存图表
    # plt.savefig(output_image_path)
    #
    # # 显示图表
    # plt.show()
    #
    # # 计算累积均值和累积标准差
    # df_throughput1_cum_mean = df_throughput1['Smoothed'].expanding().mean()
    # df_throughput2_cum_mean = df_throughput2['Smoothed'].expanding().mean()
    # df_bitrate1_cum_mean = df_bitrate1['Bitrate_Downloading'].expanding().mean()
    # df_bitrate2_cum_mean = df_bitrate2['Bitrate_Downloading'].expanding().mean()
    #
    # # 计算波动范围（累积标准差）
    # std_throughput1_cum = df_throughput1['Smoothed'].expanding().std()
    # std_throughput2_cum = df_throughput2['Smoothed'].expanding().std()
    # std_bitrate1_cum = df_bitrate1['Bitrate_Downloading'].expanding().std()
    # std_bitrate2_cum = df_bitrate2['Bitrate_Downloading'].expanding().std()
    #
    # # 开始绘图
    # plt.figure(figsize=(12, 6))
    #
    # # 绘制 Throughput 累积平均曲线和波动范围
    # plt.plot(df_throughput1['Time'], df_throughput1_cum_mean, label='Client1 Throughput', color='blue', linestyle='-',
    #          linewidth=2)
    # plt.fill_between(df_throughput1['Time'], df_throughput1_cum_mean - std_throughput1_cum,
    #                  df_throughput1_cum_mean + std_throughput1_cum, color='blue', alpha=0.3)
    #
    # plt.plot(df_throughput2['Time'] + time_flit, df_throughput2_cum_mean, label='Client2 Throughput', color='red',
    #          linestyle='-', linewidth=2)
    # plt.fill_between(df_throughput2['Time'] + time_flit, df_throughput2_cum_mean - std_throughput2_cum,
    #                  df_throughput2_cum_mean + std_throughput2_cum, color='red', alpha=0.3)
    #
    # # 绘制 Bitrate 累积平均曲线和波动范围
    # plt.plot(df_bitrate1['Time'], df_bitrate1_cum_mean, label='Client1 Bitrate', color='blue', linestyle='--',
    #          linewidth=2)
    # plt.fill_between(df_bitrate1['Time'], df_bitrate1_cum_mean - std_bitrate1_cum,
    #                  df_bitrate1_cum_mean + std_bitrate1_cum, color='blue', alpha=0.3)
    #
    # plt.plot(df_bitrate2['Time'], df_bitrate2_cum_mean, label='Client2 Bitrate', color='red', linestyle='--',
    #          linewidth=2)
    # plt.fill_between(df_bitrate2['Time'], df_bitrate2_cum_mean - std_bitrate2_cum,
    #                  df_bitrate2_cum_mean + std_bitrate2_cum, color='red', alpha=0.3)
    #
    # # 设置图表标题和坐标轴标签
    # plt.title('Throughput and Bitrate Over Time')
    # plt.xlabel('Time (seconds)')
    # plt.ylabel('Throughput/Bitrate (kbps)')
    # plt.xticks(fontsize=14)  # 设置 x 轴刻度的字体大小
    # plt.yticks(fontsize=14)  # 设置 y 轴刻度的字体大小
    # # 显示图例
    # plt.legend(fontsize=14)
    #
    # # 显示网格
    # plt.grid(True)
    #
    # # 调整布局
    # plt.tight_layout()
    #
    # # 保存图表
    # plt.savefig(output_image_path)
    #
    # # 显示图表
    # plt.show()

    ############### 第三种绘图方式 ##########################
    # 开始绘图，创建两个子图

    # 配置 matplotlib 使用 Times New Roman 字体
    matplotlib.rcParams['font.family'] = 'Times New Roman'
    matplotlib.rcParams['font.size'] = 36  # 默认字体大小
    matplotlib.rcParams['axes.labelsize'] = 34  # 坐标轴标签的字体大小

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(24, 9))
    bitrate1_time_1 = df_bitrate1['Time'].values
    bitrate1_time_2 = df_bitrate2['Time'].values
    df_bitrate1_smoothed_1 = df_bitrate1_smoothed.values
    df_bitrate1_smoothed_2 = df_bitrate2_smoothed.values

    # 创建包含时间和相应比特率的DataFrame
    df1 = pd.DataFrame({'Time': bitrate1_time_1, 'Bitrate': df_bitrate1_smoothed_1})
    df2 = pd.DataFrame({'Time': bitrate1_time_2, 'Bitrate': df_bitrate1_smoothed_2})

    # 合并两个DataFrame
    df_combined_1 = pd.concat([df1]).drop_duplicates(subset='Time')

    # 对重复的时间戳取平均值
    df_average = df_combined_1.groupby('Time', as_index=False).mean()

    # 如果有需要，排序数据
    df_average.sort_values('Time', inplace=True)

    # 从这个平均值DataFrame中提取时间和比特率
    bitrate1_time_1 = df_average['Time'].values
    df_bitrate1_smoothed_1 = df_average['Bitrate'].values

    # 合并两个DataFrame
    df_combined_2 = pd.concat([df2]).drop_duplicates(subset='Time')

    # 对重复的时间戳取平均值
    df_average = df_combined_2.groupby('Time', as_index=False).mean()

    # 如果有需要，排序数据
    df_average.sort_values('Time', inplace=True)

    # 从这个平均值DataFrame中提取时间和比特率
    bitrate1_time_2 = df_average['Time'].values
    df_bitrate1_smoothed_2 = df_average['Bitrate'].values

    # 假设 df_bitrate1_smoothed_1 和 df_bitrate1_smoothed_2 是对应的数据值
    # 创建包含时间和相应比特率的DataFrame
    df1 = pd.DataFrame({'Time': bitrate1_time_1, 'Bitrate': df_bitrate1_smoothed_1})
    df2 = pd.DataFrame({'Time': bitrate1_time_2, 'Bitrate': df_bitrate1_smoothed_2})

    # 获取两个时间序列的并集，并创建一个新的时间序列DataFrame
    all_times = np.union1d(df1['Time'], df2['Time'])
    df_all_times = pd.DataFrame({'Time': all_times})

    # 对两个数据集执行线性插值
    df1_interpolated = df1.set_index('Time').reindex(all_times).interpolate(method='linear').fillna(0)
    df2_interpolated = df2.set_index('Time').reindex(all_times).interpolate(method='linear').fillna(0)

    # 现在可以绘制插值后的数据了
    ax1.plot(bitrate1_time_1, df_bitrate1_smoothed_1, label='Client1 Bitrate', color='blue', linestyle='--',
             linewidth=4)
    ax1.plot(bitrate1_time_2, df_bitrate1_smoothed_2, label='Client2 Bitrate', color='red', linestyle='--',
             linewidth=4)

    # ax1.set_title('Bitrate Over Time')
    # ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Bitrate (kbps)')
    # ax1.legend(loc='upper left')
    ax1.grid(True)
    ax1.set_xlim(0, 125)

    # 调整子图间的垂直间距
    # plt.subplots_adjust(hspace=0.3)  # hspace 控制垂直间的间隔，值越大间隔越宽

    # 假设df_throughput1_smoothed和df_throughput2_smoothed是对应的数据值
    # 创建包含时间和相应吞吐量的DataFrame
    df1 = pd.DataFrame({'Time': df_throughput1['Time'], 'Throughput': df_throughput1_smoothed})
    df2 = pd.DataFrame({'Time': df_throughput2['Time'] + time_flit, 'Throughput': df_throughput2_smoothed})

    # 获取两个时间序列的并集，并创建一个新的时间序列DataFrame
    all_times = np.union1d(df1['Time'], df2['Time'])
    df_all_times = pd.DataFrame({'Time': all_times})

    # 对两个数据集执行线性插值
    df1_interpolated = df1.set_index('Time').reindex(all_times).interpolate(method='linear').fillna(0)
    df2_interpolated = df2.set_index('Time').reindex(all_times).interpolate(method='linear').fillna(0)

    # 准备堆叠图数据
    throughput_stack = np.vstack((df1_interpolated['Throughput'], df2_interpolated['Throughput']))

    # 使用堆叠图展示数据
    ax2.stackplot(df_all_times['Time'], throughput_stack,
                  labels=['Client1 Throughput', 'Client2 Throughput'], colors=['blue', 'red'], alpha=0.5)

    # 添加标题和图例等
    # ax2.set_title('Stacked Throughput Over Time')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Throughput (kbps)')
    fig.legend(loc='upper center', ncol=4,bbox_to_anchor=(0.5, 1.025))
    ax2.grid(True)
    ax2.set_xlim(0,125)
    plt.savefig(output_image_path, bbox_inches='tight')
    plt.show()


# 调用函数进行绘图
solution_names = ['rl data', 'bola', 'CARA']

# solution_names = ['bola']

for solution_name in solution_names:
    if solution_name == 'rl data':
        throughput_csv_path1 = './rl data/client1_0-pcap.csv'
        throughput_csv_path2 = './rl data/client2_0-pcap.csv'
        bitrate_csv_path1 = './rl data/client1_0.xlsx'
        bitrate_csv_path2 = './rl data/client2_0.xlsx'
        output_image_path = './rl data/rl.pdf'
    elif solution_name == 'bola':
        throughput_csv_path1 = './bola/client1_1-pcap.csv'
        throughput_csv_path2 = './bola/client2_1-pcap.csv'
        bitrate_csv_path1 = './bola/client1_1.csv'
        bitrate_csv_path2 = './bola/client2_1.csv'
        output_image_path = './bola/bola.pdf'
    elif solution_name == 'CARA':
        throughput_csv_path1 = './CARA/client1-pcap.csv'
        throughput_csv_path2 = './CARA/client2-pcap.csv'
        bitrate_csv_path1 = './CARA/client1.csv'
        bitrate_csv_path2 = './CARA/client2.csv'
        output_image_path = './CARA/CARA.pdf'

    plot_throughput_and_bitrate(throughput_csv_path1, throughput_csv_path2,bitrate_csv_path1,bitrate_csv_path2,output_image_path)
    plt.clf()
    plt.close()