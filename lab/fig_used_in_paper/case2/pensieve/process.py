import os

import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

import re
import csv


# dir = '1st comp/'
# base_name = 'tp'

# ^(?!Received message).*$



def preprocess_new_data(input_file):
    # 读取CSV文件
    df = pd.read_csv(input_file)

    # 将秒级时间戳转换为毫秒级时间戳
    df['Time'] = df['Time'] * 1000

    # 将BitrateLevel转换为Bitrate_Downloading
    bitrate_mapping = {
        0: 141569,
        1: 647117,
        2: 1093080,
        3: 1904424,
        4: 3886193,
        5: 3886193
    }
    df['Bitrate_Downloading'] = df['BitrateLevel'].map(bitrate_mapping)/1000

    # 删除不需要的列
    df = df.drop(['BitrateLevel', 'Clientnum'], axis=1)

    # 对于时间戳相同的数据，进行插值处理
    time_counts = defaultdict(int)
    for index, row in df.iterrows():
        time_counts[row['Time']] += 1

    for index, row in df.iterrows():
        if time_counts[row['Time']] > 1:
            milliseconds = 0
            for i in range(time_counts[row['Time']]):
                df.at[index, 'Time'] -= milliseconds
                milliseconds += 1000 // time_counts[row['Time']]  # 平均插值
            time_counts[row['Time']] -= 1

    return df

def holo_csv(input_file):
    # 读取CSV文件
    df = pd.read_csv(input_file)
    holo_offset = 8 * 3600 * 1000 + 0 * 1000
    # holo_offset=0
    # 将Time列转换为时间戳
    df['time'] = pd.to_datetime(df['time']).apply(
        lambda x: int(x.timestamp() * 1000) - holo_offset)  # 转换为毫秒级时间戳

    # 对于时间戳相同的数据，进行插值处理
    time_counts = defaultdict(int)
    for index, row in df.iterrows():
        time_counts[row['time']] += 1

    for index, row in df.iterrows():
        if time_counts[row['time']] > 1:
            milliseconds = 0
            for i in range(time_counts[row['time']]):
                df.at[index, 'time'] -= milliseconds
                milliseconds += 1000 // time_counts[row['time']]  # 平均插值
            time_counts[row['time']] -= 1
    df = df[df['direction'] == 'right']

    # 保存处理后的数据
    # df.to_csv(output_file, index=False)
    return df

def merge_wave_df(dash_df, holo_df, output_filename):
    # 筛选时间范围
    start_time = dash_df['Time'].min()
    end_time = dash_df['Time'].max()
    holo_df = holo_df[holo_df['time'].between(start_time, end_time)]

    # 按照 Time 排序
    dash_df = dash_df.sort_values('Time')

    # 删除相邻重复行
    dash_df = dash_df.drop_duplicates(subset=dash_df.columns.difference(['Time']), keep='first')
    dash_df = dash_df.reset_index(drop=True)

    # 将毫秒级时间置为空
    temp_dash_df = dash_df.copy()
    temp_dash_df['Time'] = temp_dash_df['Time'] // 1000 * 1000

    # 合并数据框
    merged_df = pd.merge_asof(temp_dash_df, holo_df, left_on='Time', right_on='time', direction='nearest')

    # 还原 dash_df 数据的毫秒级时间
    merged_df['Time'] = dash_df['Time']

    # 删除多余的时间列
    merged_df = merged_df.drop(columns=['time'])
    # 重命名列
    merged_df = merged_df.rename(
        columns={'Bitrate_Downloading': 'bitrate', 'Buffer_Length': 'buffer', 'Time': 'time', 'tx_rate': 'throughput'})

    # 调整列顺序
    merged_df = merged_df[['id', 'time', 'buffer', 'bitrate', 'throughput']]

    # 删除除指定列之外的所有列
    merged_df = merged_df[['id', 'time', 'buffer', 'bitrate', 'throughput']]

    merged_df['throughput'] = merged_df['throughput'] / 1000
    # 写出到文件
    merged_df.to_csv(output_filename, index=False)


# 测试函数
def do_preprocess(dir, holo_csv_file="holo.csv"):
    # holowan导出的，吞吐量的文件
    listdir = os.listdir(dir)
    if "holo.csv" not in listdir:
        input_file = holo_csv_file
        holo_df = holo_csv(dir + input_file)
        holo_df.to_csv(dir + 'holo.csv', index=False)
    else:
        holo_df = pd.read_csv(dir + 'holo.csv')

    # dash的比特率记录文件，插件抓的
    for file in listdir:
        if file.endswith(".csv"):
            if file.startswith("holo") or file.count("wave") > 0 or file == holo_csv_file or file=='avg.csv':
                continue
            input_file = file
            # output_file = file[:-4] + '.csv'
            dash_df = preprocess_new_data(dir + input_file)
            merge_wave_df(dash_df, holo_df, dir + os.path.basename(file)[:-4] + '_wave.csv')
    # input_file = base_name + '.csv'
    # output_file = base_name + '_dash.csv'
    # dash_df=preprocess_csv(dir + input_file, dir + output_file)
    # merge_wave_df(dash_df, holo_df, dir + base_name + '_wave.csv')

# preprocess_new_data('./log_RL_0.csv')
# do_preprocess('case1/case1/', 'holowan.csv')
# do_preprocess()
