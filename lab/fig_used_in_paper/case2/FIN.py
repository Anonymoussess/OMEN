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
plt.rcParams['font.size'] = 16



# tcpStatus = read_tcp_status("tcpStatus.txt")

base_dir = './avg_res/'



def get_df(wave_file):
    # 读取 cwnd.csv 文件
    # 读取 dash_pro.csv 文件————手动开始和结束使用脚本抓的文件，所以时间最准确，以此为准，截取其他数据段
    wave_df = pd.read_csv(wave_file)
    # 读取 dash_pro.csv 文件
    holo_time_offset = 0 * 1000  # tp+tcp
    wave_df['time'] = wave_df['time'] + holo_time_offset  # holowan机器记录的时间有偏移

    min_time = wave_df['time'].min()+120
    # max_time = wave_df['time'].max()
    max_time = min_time + 240

    wave_df = wave_df.loc[wave_df['time'] <= max_time]
    wave_df = wave_df.loc[wave_df['time'] >= min_time]
    wave_df = wave_df.loc[wave_df['time'] <= max_time]

    # 处理 wave_df 数据
    # wave_df['time'] = wave_df['time'] / 1000  # 转换时间单位为秒
    wave_df['time'] = wave_df['time'] - wave_df['time'].iloc[0]  # 转换为相对时间

    return wave_df

def plot_graphs(wave_file,base_name="default"):
    if wave_file.count('ensieve')==0:
        return
    fig,ax1=plt.subplots(figsize=(12,3.5))
    ax2 = ax1.twinx()
    wave_df=get_df(wave_file)

    wave_df = wave_df.reset_index(drop=True)
    wave_df['id'] = wave_df.index + 1
    sine_wave, time = get_sin_wave()
    sine_wave[sine_wave>4000]=4000

    # 绘制曲线1：带宽 数据
    ax1.plot(time, sine_wave, label='Available bandwidth', color='blue',alpha=0.3,linewidth=2.5)

    wave_df = wave_df.fillna(method='ffill')
    x=wave_df['id']
    wave_df['bitrate'] = wave_df['bitrate'].rolling(window=2, min_periods=1).max()
    wave_df['bitrate'] = wave_df['bitrate'].rolling(window=2, min_periods=1).max()
    wave_df['bitrate'] = wave_df['bitrate'].rolling(window=3, min_periods=1).mean()
    # wave_df['bitrate'] = wave_df['bitrate'].rolling(window=8, min_periods=1).mean() if wave_file.count('comyco')>0 and column=='buffer' else wave_df['bitrate']
    # wave_df['bitrate'] = wave_df['bitrate'].rolling(window=15, min_periods=1).mean()
    alp=1 if wave_file.count('tcp')>0 else 0.7
    ax1.plot(wave_df['id'], wave_df['bitrate'], label='Bitrate',alpha=alp,linewidth=2.5)

    ax2.plot(wave_df['id'], wave_df['buffer'], label='Buffer level',alpha=alp,color='orange',linewidth=2.5)


    sin_y = get_sin_wave_new(len(wave_df))
    sin_y[sin_y>4000]=4000

    ax1.fill_between(x,  wave_df['bitrate'], sin_y, where=(wave_df['bitrate'].values >= sin_y), facecolor='gray', alpha=0.3)
    ax1.fill_between(x,  sin_y,wave_df['bitrate'], where=(wave_df['bitrate'].values < sin_y), facecolor='gray', alpha=0.3)


    # qoe = QoE(wave_df)
    # print(f'QoE:{qoe}')

    ax1.set_xlabel('Time (s)', fontsize=20)
    ax1.set_ylabel('Bitrate (kbps)', fontsize=20)
    ax2.set_ylabel('Buffer (s)', fontsize=20)
    ax2.set_ylim(0,70)
    ax1.set_xlim(0,250)
    # plt.title(f'{base_dir}{base_name}')
    # fig.legend(fontsize='x-large',loc='upper center')
    plt.grid(False)

    # plt.title(f'{base_dir}/{base_name}', fontsize=25)
    fig.legend(fontsize='x-large',ncol=3,loc='upper right')
    plt.xticks(fontsize=18)  # 设置 x 轴刻度的字体大小
    plt.yticks(fontsize=18)  # 设置 y 轴刻度的字体大小


    plt.savefig(base_dir + f"{base_name}.svg", bbox_inches='tight')
    plt.tight_layout()
    plt.show()


def get_sin_wave():
    # 绘制曲线1：正弦函数曲线
    time = np.linspace(0, 240, 10000)  # 时间范围为 0 到 120 秒
    amplitude = (5000 - 400) / 2  # 振幅为最高值和最低值的一半
    phase = 120 * 0.75  # 初始相位为 200
    sine_wave = amplitude * np.sin(2 * np.pi *
                                   (time + phase) / 120) + (5000 + 400) / 2
    return sine_wave, time

def get_sin_wave_new(points):
    # 绘制曲线1：正弦函数曲线
    time = np.linspace(0.3, 238, points)  # 时间范围为 0 到 120 秒
    amplitude = (5000 - 400) / 2  # 振幅为最高值和最低值的一半
    phase = 120 * 0.75  # 初始相位为 200
    sine_wave = amplitude * np.sin(2 * np.pi *
                                   (time + phase) / 120) + (5000 + 400) / 2
    return sine_wave
# 调用函数并传入文件路径

# dash_process.do_preprocess(base_name, base_dir, holo_file)
#

# new_preprocess.do_preprocess(base_dir,"case2.csv")

wave_list=utils.get_wave_list(base_dir)
# lambda: call plot_graphs(base_dir + wave_file, cwnd_states1 + cwnd_states2)
# dfs=utils.apply_function_to_files(wave_list,lambda file:get_df(file))
# dfs=utils.apply_function_to_files(dfs,lambda df:utils.convert_records_to_secondly())

column='bitrate'
utils.apply_function_to_files(wave_list,lambda file:plot_graphs(file,file.split('/')[-1].split('_')[0]))
# plot_graphs(wave_list,f'case2-fig_fig')

# dfs=utils.apply_function_to_files(wave_list,lambda file:get_df(file))

# result_df=utils.get_ndf_avg_value(dfs)
# result_df.to_csv(base_dir+'avg.csv',index=False)


# plot_graphs(base_dir + "avg.csv", cwnd_states1 + cwnd_states2)
# plot_graphs(base_dir + status_file, base_dir + bitrate_file, base_dir + holo_file,cwnd_states2)


# draw_each_status_fig(base_dir + status_file, base_dir + bitrate_file, base_dir + holo_file)
