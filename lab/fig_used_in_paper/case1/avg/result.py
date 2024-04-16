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

# tcpStatus = read_tcp_status("tcpStatus.txt")

base_dir = './'

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
    max_time = min_time + 24

    wave_df = wave_df.loc[wave_df['time'] <= max_time]
    wave_df = wave_df.loc[wave_df['time'] >= min_time]
    wave_df = wave_df.loc[wave_df['time'] <= max_time]

    # 处理 wave_df 数据
    # wave_df['time'] = wave_df['time'] / 1000  # 转换时间单位为秒
    wave_df['time'] = wave_df['time'] - wave_df['time'].iloc[0]  # 转换为相对时间

    return wave_df


def plot_graphs(wave_files, base_name="default"):
    plt.figure(figsize=(15, 5))
    dfs = []
    max_throughput_time = float(-1)
    max_buffer_time = float(-1)
    min_throughput_time = float('inf')
    min_buffer_time = float('inf')
    marker=['p','o','s','*']
    marker_size=[15,12,12,16]

    i=0
    for wave_file in wave_files:
        if wave_file.count('tcp') > 0:
            continue
        wave_df = get_df(wave_file)
        dfs.append(wave_df)
        wave_df['bitrate'] = wave_df['bitrate'].rolling(window=2, min_periods=1).max()
        wave_df['bitrate'] = wave_df['bitrate'].rolling(window=2, min_periods=1).max()
        wave_df['bitrate'] = wave_df['bitrate'].rolling(window=3, min_periods=1).mean()

        # 找到最早达到最大值的吞吐量时间点
        max_throughput_idx = wave_df['throughput'][:10].idxmax()
        # min_throughput_time = min(max_throughput_idx, min_throughput_time)
        # max_throughput_time = max(max_throughput_idx, max_throughput_time)

        plt.scatter(max_throughput_idx, wave_df.loc[max_throughput_idx]['bitrate'],
                    color='blue', marker='o',linewidths=10, zorder=10)
        plt.errorbar(max_throughput_idx, wave_df.loc[max_throughput_idx]['bitrate'],
                     color='blue',xerr=0, yerr=500)

        # 找到最晚达到最大值的缓冲区时间点
        max_buffer_idx = wave_df['buffer'][:20].idxmax()

        # find the first idx that  buffer > 29
        limit_buffer_idx=wave_df[wave_df['buffer']>23].index[0]
        max_buffer_idx = min(limit_buffer_idx, max_buffer_idx)

        # min_buffer_time = min(max_buffer_idx, min_buffer_time)
        # max_buffer_time = max(max_buffer_idx, max_buffer_time)
        plt.scatter(max_buffer_idx, wave_df.loc[max_buffer_idx]['bitrate'],
                    color='red', marker='^', linewidths=10, zorder=11)
        plt.errorbar(max_buffer_idx, wave_df.loc[max_buffer_idx]['bitrate'],
                     color='red',xerr=0, yerr=500)

        alp = 1 if wave_file.count('tcp') > 0 else 0.9
        plt.plot(wave_df['time'], wave_df['bitrate'], linewidth=5,marker=marker[i],markersize=marker_size[i]
                 , label=wave_file.split('/')[-1].split('_')[0], alpha=alp)
        i+=1

    # 创建吞吐量阴影区域
    # plt.fill_between([min_throughput_time, max_throughput_time], 0, np.max(dfs[0]['bitrate']), color='gray', alpha=0.3)
    # plt.text(min_throughput_time+3, 2000, 'Thpt', ha='center', va='bottom',fontsize=20)

    # 创建缓冲区阴影区域
    # plt.fill_between([min_buffer_time, max_buffer_time], 0, np.max(dfs[0]['bitrate']), color='cyan', alpha=0.3)
    # plt.text(max_buffer_time-2, 2000, 'Buffer', ha='center', va='bottom',fontsize=20)

    plt.xlabel('Time (s)', fontsize=20)
    plt.ylabel('Bitrate (kbps)', fontsize=20)
    plt.grid(False)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)

    plt.xlim(0,25)
    plt.ylim(0, 4000)
    original_legend = plt.legend()
    # 自定义的图例记录
    custom_labels = ['BOLA','Comyco','Pensieve','Reach Max Thpt', 'Reach Max Buffer']
    custom_handles = [plt.Line2D([], [], color='blue', marker='h',linewidth=12, linestyle='None'),
                      plt.Line2D([], [], color='red', marker='^',linewidth=12, linestyle='None')]

    # 添加自定义的图例记录到图例框中
    plt.legend(handles=original_legend.legendHandles + custom_handles,
               labels=custom_labels,fontsize='xx-large')

    plt.savefig(base_dir + f"{base_name}.pdf",bbox_inches='tight')
    plt.tight_layout()
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
# do_preprocess(base_dir,"case3.csv")

wave_list = utils.get_wave_list(base_dir)
# lambda: call plot_graphs(base_dir + wave_file, cwnd_states1 + cwnd_states2)
# dfs=utils.apply_function_to_files(wave_list,lambda file:get_df(file))
# utils.apply_function_to_files(wave_list,lambda file:plot_graphs(file,file.split('/')[-1].split('.')[0]))

plot_graphs(wave_list, 'motivation_fig')

# dfs=utils.apply_function_to_files(wave_list,lambda file:get_df(file))
# dfs=utils.apply_function_to_files(dfs,lambda df:utils.convert_records_to_secondly(df))
# dfs=utils.apply_function_to_files(dfs,utils.interpolate_data)
# result_df=utils.get_ndf_avg_value(dfs)
# result_df.to_csv(base_dir+'avg.csv',index=False)


# plot_graphs(base_dir + "avg.csv", cwnd_states1 + cwnd_states2)
# plot_graphs(base_dir + status_file, base_dir + bitrate_file, base_dir + holo_file,cwnd_states2)


# draw_each_status_fig(base_dir + status_file, base_dir + bitrate_file, base_dir + holo_file)
