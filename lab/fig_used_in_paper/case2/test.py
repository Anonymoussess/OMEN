import math

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import new_preprocess
import utils
from tools import *
import dash_process
from utils import *

plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 指定使用的中文字体，如宋体、黑体等
plt.tight_layout()
plt.rcParams['font.size'] = 13



# tcpStatus = read_tcp_status("tcpStatus.txt")

base_dir = './avg_res/'

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

    min_time = wave_df['time'].min()#+120
    # max_time = wave_df['time'].max()
    max_time = min_time + 600

    wave_df = wave_df.loc[wave_df['time'] <= max_time]
    wave_df = wave_df.loc[wave_df['time'] >= min_time]
    wave_df = wave_df.loc[wave_df['time'] <= max_time]

    # 处理 wave_df 数据
    # wave_df['time'] = wave_df['time'] / 1000  # 转换时间单位为秒
    wave_df['time'] = wave_df['time'] - wave_df['time'].iloc[0]  # 转换为相对时间

    return wave_df

def plot_graphs(wave_files,cloumn,base_name="default"):
    plt.figure(figsize=(14,3))
    sine_wave, time = get_sin_wave()
    # 绘制曲线1：带宽 数据
    if column=='bitrate':
        plt.plot(time, sine_wave, label='Bandwidth', color='blue',alpha=0.3)
        pass
    for wave_file in wave_files:
        if wave_file.count('tcp')>0:
            continue
        wave_df=get_df(wave_file)

        wave_df = wave_df.reset_index(drop=True)
        wave_df['id'] = wave_df.index + 1

        wave_df = wave_df.fillna(method='ffill')
    # 绘制曲线2：比特率 数据
    # wave_df['bitrate']=wave_df['bitrate'].rolling(window=3, min_periods=1).max()  # 使用窗口大小为3的滑动平均
    # wave_df['bitrate']=wave_df['bitrate'].rolling(window=2, min_periods=1).max()  # 使用窗口大小为3的滑动平均
    # plt.plot(wave_df['time'], wave_df['bitrate'], label='Bitrate', color='red')

    # first_occurrence_index = wave_df['bitrate'].eq(3886).idxmax()

    # 在图中添加竖线
    # plt.axvline(x=first_occurrence_index, color='r', linestyle='--')

    # create a y axis with diff scale
    # ax2 = ax1.twinx()
    #
    # wave_df['buffer'] = wave_df['buffer'].rolling(window=3, min_periods=1).mean()  # 使用窗口大小为3的滑动平均
    # wave_df['buffer'] = wave_df['buffer'].rolling(window=3, min_periods=1).min()
    # ax2.plot(wave_df['time'], wave_df['buffer'], label='buffer')

    # 绘制曲线3：实际吞吐量 数据
    #     wave_df[cloumn] = wave_df[cloumn].rolling(window=5, min_periods=1).min() if wave_file.count('tcp')==0 else wave_df[cloumn]
    #     wave_df[cloumn] = wave_df[cloumn].rolling(window=3, min_periods=1).max()
    #     wave_df[cloumn] = wave_df[cloumn].rolling(window=5, min_periods=1).max()
        wave_df[cloumn] = wave_df[cloumn].rolling(window=2, min_periods=1).max()
        wave_df[cloumn] = wave_df[cloumn].rolling(window=2, min_periods=1).max()
        wave_df[cloumn] = wave_df[cloumn].rolling(window=3, min_periods=1).mean()
        wave_df[cloumn] = wave_df[cloumn].rolling(window=8, min_periods=1).mean() if wave_file.count('comyco')>0 and column=='buffer' else wave_df[cloumn]
        # wave_df[cloumn] = wave_df[cloumn].rolling(window=15, min_periods=1).mean()
        alp=1 if wave_file.count('tcp')>0 else 0.7
        plt.plot(wave_df['id'], wave_df[cloumn], label=wave_file.split('/')[-1].split('_')[0],alpha=alp)

    # qoe = QoE(wave_df)
    # print(f'QoE:{qoe}')

    plt.xlabel('Time (s)', fontsize=20)
    if column.count('bitrate')>0:
        plt.ylabel('Bitrate (kbps)', fontsize=20)
    else:
        plt.ylabel('Buffer (s)', fontsize=20)
    # plt.title(f'{base_dir}{base_name}')
    if column.count('buffer')>0:
        plt.legend()
    plt.grid(True)

    # plt.title(f'{base_dir}/{base_name}', fontsize=25)
    plt.legend(fontsize='x-large',loc='lower right')
    plt.xticks(fontsize=18)  # 设置 x 轴刻度的字体大小
    plt.yticks(fontsize=18)  # 设置 y 轴刻度的字体大小


    plt.savefig(base_dir + f"{base_name}.svg")
    plt.tight_layout()
    plt.show()


def get_sin_wave():
    # 绘制曲线1：正弦函数曲线
    time = np.linspace(0, 600, 10000)  # 时间范围为 0 到 120 秒
    amplitude = (5000 - 400) / 2  # 振幅为最高值和最低值的一半
    phase = 120 * 0.75  # 初始相位为 200
    sine_wave = amplitude * np.sin(2 * np.pi *
                                   (time + phase) / 120) + (5000 + 400) / 2
    return sine_wave, time


# 调用函数并传入文件路径

# dash_process.do_preprocess(base_name, base_dir, holo_file)
#

# new_preprocess.do_preprocess(base_dir,"case2.csv")

wave_list=utils.get_wave_list(base_dir)
# lambda: call plot_graphs(base_dir + wave_file, cwnd_states1 + cwnd_states2)
# dfs=utils.apply_function_to_files(wave_list,lambda file:get_df(file))
# dfs=utils.apply_function_to_files(dfs,lambda df:utils.convert_records_to_secondly())

column='bitrate'
plot_graphs(wave_list,column,f'{column}_fig')

# dfs=utils.apply_function_to_files(wave_list,lambda file:get_df(file))

# result_df=utils.get_ndf_avg_value(dfs)
# result_df.to_csv(base_dir+'avg.csv',index=False)


# plot_graphs(base_dir + "avg.csv", cwnd_states1 + cwnd_states2)
# plot_graphs(base_dir + status_file, base_dir + bitrate_file, base_dir + holo_file,cwnd_states2)


# draw_each_status_fig(base_dir + status_file, base_dir + bitrate_file, base_dir + holo_file)
