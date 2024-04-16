import math

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import new_preprocess
import utils
from rl_preprocess import do_preprocess
from tools import *
import dash_process
from utils import *

plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 指定使用的中文字体，如宋体、黑体等
plt.tight_layout()
plt.rcParams['font.size'] = 13


# tcpStatus = read_tcp_status("tcpStatus.txt")

base_dir = './comyco/'

# wave_file = base_name + '_wave.csv'
# status_file = base_name + '_status.csv'
cwnd_states1 = ['tcp_fastretrans_alert', 'cubictcp_cong_avoid', 'tcp_cwnd_reduction']
cwnd_states2 = ['tcp_try_keep_open', '//tcp_xmit_recovery', 'tcp_sndbuf_expand', 'tcp_try_undo_recovery',
                'tcp_undo_cwnd_reduction']


def get_df(wave_file):
    # 读取 cwnd.csv 文件
    # 读取 dash_pro.csv 文件————手动开始和结束使用脚本抓的文件，所以时间最准确，以此为准，截取其他数据段
    wave_df = pd.read_csv(wave_file)
    # 读取 dash_pro.csv 文件
    holo_time_offset = 0 * 1000  # tp+tcp
    wave_df['time'] = wave_df['time'] + holo_time_offset  # holowan机器记录的时间有偏移

    min_time = wave_df['time'].min()
    # max_time = wave_df['time'].max()
    max_time = min_time + 600*1000

    wave_df = wave_df.loc[wave_df['time'] <= max_time]
    wave_df = wave_df.loc[wave_df['time'] >= min_time]
    wave_df = wave_df.loc[wave_df['time'] <= max_time]

    # 处理 wave_df 数据
    wave_df['time'] = wave_df['time'] / 1000  # 转换时间单位为秒
    wave_df['time'] = wave_df['time'] - wave_df['time'].iloc[0]  # 转换为相对时间

    return wave_df

def plot_graphs(wave_file,base_name="default"):
    wave_df=get_df(wave_file)
    fig,ax1=plt.subplots(figsize=(15, 6))

    sine_wave, time = get_sin_wave()
    # 绘制曲线1：带宽 数据
    # plt.plot(time, sine_wave, label='Bandwidth', color='blue')

    # 绘制曲线2：比特率 数据
    wave_df['bitrate']=wave_df['bitrate'].rolling(window=2, min_periods=1).max()  # 使用窗口大小为3的滑动平均
    wave_df['bitrate']=wave_df['bitrate'].rolling(window=3, min_periods=1).min()  # 使用窗口大小为3的滑动平均
    ax1.plot(wave_df['time'], wave_df['bitrate'], label='Bitrate', color='red')

    # first_occurrence_index = wave_df['bitrate'].eq(3886).idxmax()

    # 在图中添加竖线
    # plt.axvline(x=first_occurrence_index, color='r', linestyle='--')

    # create a y axis with diff scale
    ax2 = ax1.twinx()
    #
    wave_df['buffer'] = wave_df['buffer'].rolling(window=3, min_periods=1).mean()  # 使用窗口大小为3的滑动平均
    # wave_df['buffer'] = wave_df['buffer'].rolling(window=3, min_periods=1).min()
    ax2.plot(wave_df['time'], wave_df['buffer'], label='buffer')

    # 绘制曲线3：实际吞吐量 数据
    wave_df['throughput'] = wave_df['throughput'].rolling(window=5, min_periods=1).mean()
    wave_df['throughput'] = wave_df['throughput'].rolling(window=3, min_periods=1).mean()
    # wave_df['bitrate'] = wave_df['bitrate'].rolling(window=15, min_periods=1).mean()

    ax1.plot(wave_df['time'], wave_df['throughput'], label='throughput (kbps)',color='green')

    qoe = QoE(wave_df)
    print(f'QoE:{qoe}')

    plt.xlabel('Time (s)')
    ax1.set_ylabel('Bitrate (kbps)')
    ax2.set_ylabel('buffer (s)')
    plt.title(f'{base_dir}{base_name}')
    plt.legend()
    plt.grid(True)
    plt.savefig(base_dir + f"{base_name}.svg")
    plt.show()



def get_sin_wave():
    # 绘制曲线1：正弦函数曲线
    time = np.linspace(0, 600, 1000)  # 时间范围为 0 到 600 秒
    amplitude = (5000 - 400) / 2  # 振幅为最高值和最低值的一半
    phase = 120 * 0.75  # 初始相位为 200
    sine_wave = amplitude * np.sin(2 * np.pi * (time + phase) / 120) + (5000 + 400) / 2
    return sine_wave, time


# 调用函数并传入文件路径

# dash_process.do_preprocess(base_name, base_dir, holo_file)
#

# new_preprocess.do_preprocess(base_dir,"case1.csv")
do_preprocess(base_dir,"case3.csv")

wave_list=utils.get_wave_list(base_dir)
# lambda: call plot_graphs(base_dir + wave_file, cwnd_states1 + cwnd_states2)
# dfs=utils.apply_function_to_files(wave_list,lambda file:get_df(file))
utils.apply_function_to_files(wave_list,lambda file:plot_graphs(file,file.split('/')[-1].split('.')[0]))

# plot_graphs(dfs,'buffer','bitrate_fig')

dfs=utils.apply_function_to_files(wave_list,lambda file:get_df(file))
# dfs=utils.apply_function_to_files(dfs,lambda df:utils.convert_records_to_secondly(df))
# dfs=utils.apply_function_to_files(dfs,utils.interpolate_data)
result_df=utils.get_ndf_avg_value(dfs)
result_df.to_csv(base_dir+'avg.csv',index=False)


# plot_graphs(base_dir + "avg.csv", cwnd_states1 + cwnd_states2)
# plot_graphs(base_dir + status_file, base_dir + bitrate_file, base_dir + holo_file,cwnd_states2)


# draw_each_status_fig(base_dir + status_file, base_dir + bitrate_file, base_dir + holo_file)
