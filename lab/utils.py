import math
import os

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


def get_df(wave_file):
    # 读取 cwnd.csv 文件
    # 读取 dash_pro.csv 文件————手动开始和结束使用脚本抓的文件，所以时间最准确，以此为准，截取其他数据段
    wave_df = pd.read_csv(wave_file)
    # 读取 dash_pro.csv 文件
    holo_time_offset = 0 * 1000  # tp+tcp
    wave_df['time'] = wave_df['time'] + holo_time_offset  # holowan机器记录的时间有偏移

    min_time = wave_df['time'].min()
    # max_time = wave_df['time'].max()
    max_time = min_time + 650 * 1000

    wave_df = wave_df.loc[wave_df['time'] <= max_time]
    wave_df = wave_df.loc[wave_df['time'] >= min_time]
    wave_df = wave_df.loc[wave_df['time'] <= max_time]

    # 处理 wave_df 数据
    wave_df['time'] = wave_df['time'] / 1000  # 转换时间单位为秒
    wave_df['time'] = wave_df['time'] - wave_df['time'].iloc[0]  # 转换为相对时间

    return wave_df


def QoE(df, q_type="linear"):
    # 定义 q(Rn) 映射函数，暂时使用 q(Rn) = Rn
    def q(r):
        if q_type == "linear":
            return r
        if q_type == "log":
            return math.log(r)

    # 计算 q(Rn) 列
    df['q(Rn)'] = df['bitrate'].apply(q)

    diurtion = df['time'].max() - df['time'].min()

    final_Tn = get_stall_time(df)

    SQrn = df['q(Rn)'].sum()

    diff_forward = df['q(Rn)'].diff().sum()
    diff_backward = df['q(Rn)'].diff(periods=-1).sum()

    a = 0.8469
    b = 28.7959
    c = 0.2979
    d = 1.0610

    # 计算 QoE
    qoe = a * SQrn - b * final_Tn + c * diff_forward - d * diff_backward

    result = int(qoe / diurtion)
    return result if result > 0 else 0


def get_stall_time(df):
    df['Tn'] = 0.0  # 初始化 Tn 列为 0
    for i in range(1, len(df) - 1):
        if df.loc[i, 'buffer'] < 0.7:
            t = df.loc[i, 'time']
            delta_t = (df.loc[i + 1, 'time'] - df.loc[i - 1, 'time']) / 2
            df.loc[i, 'Tn'] = delta_t
    final_Tn = df['Tn'].sum() * 120
    return final_Tn


def get_one_qoe(wave_file):
    wave_df = get_df(wave_file)
    return QoE(wave_df)


def get_one_stalling_time_s(wave_file):
    df = get_df(wave_file)
    # 计算 Tn 列
    df['Tn'] = 0  # 初始化 Tn 列为 0

    for i in range(1, len(df) - 1):
        if df.loc[i, 'buffer'] < 0.7:
            t = df.loc[i, 'time']
            delta_t = (df.loc[i + 1, 'time'] - df.loc[i - 1, 'time']) / 2
            df.loc[i, 'Tn'] = delta_t

    final_Tn = df['Tn'].sum()  # *1000

    return final_Tn


def get_avg_bitrate(wave_file):
    df = get_df(wave_file)
    return df['bitrate'].mean()


def get_wave_list(dir):
    wave_list = []
    listdir = os.listdir(dir)

    for file in listdir:
        if file.endswith(".csv") and file.count("wave") > 0:
            wave_list.append(os.path.join(dir, file))  # 将文件名与路径拼接后添加到列表中

    return wave_list


def apply_function_to_files(file_list, func):
    result_list = []

    for file in file_list:
        result = func(file)  # 调用传入的函数对文件进行处理
        result_list.append(result)  # 将结果添加到结果列表中

    return result_list


# def extract_column_from_df(dfs, column_name):
#     result = []
#     for df in dfs:
#         result.append({df["time"], df[column_name]})
#     return result

def extract_column_from_df(dfs, column_name):
    res = pd.DataFrame()
    for cname in column_name:
        for i, df in enumerate(dfs):
            res[cname + str(i)] = df[cname]
    return res


def get_ndf_avg_value(dfs):
    columns = dfs[0].columns
    result_df = pd.DataFrame(columns=columns)
    for column in columns:
        time_map = {}
        if column == 'id' or column == 'time':
            continue
        for df in dfs:
            for _, row in df.iterrows():
                time = int(row['time'])
                if time not in time_map:
                    time_map[time] = [0, 0]
                time_map[time][0] += 1
                time_map[time][1] += row[column]
        for k, v in time_map.items():
            k = int(k)
            if k not in result_df['time'].values:
                result_df.loc[len(result_df)] = {'time': k, column: v[1] / v[0]}
            else:
                result_df.loc[result_df['time'] == k, column] = v[1] / v[0]
    result_df = result_df[result_df['time'].apply(lambda x: x % 1 == 0 or x.is_integer())]
    result_df = result_df.sort_values(by='time')

    result_df = result_df.reset_index(drop=True)
    result_df['id'] = result_df.index + 1

    result_df = result_df.fillna(method='ffill')
    return result_df


# 一秒多个
def convert_records_to_secondly(df):
    df = df.rename(columns={'time': 'Time'})
    columns = df.columns
    result_df = pd.DataFrame(columns=columns)

    for column in columns:
        time_map = {}
        if column == 'id' or column == 'Time':
            result_df[column] = df[column]
            continue
        for _, row in df.iterrows():
            time = int(row['Time'])
            if time not in time_map:
                time_map[time] = [0, 0]
            time_map[time][0] += 1
            time_map[time][1] += row[column]
        for k, v in time_map.items():
            k = int(k)
            if k not in result_df['Time'].values:
                result_df.loc[len(result_df)] = {'Time': k, column: v[1] / v[0]}
                # result_df = result_df._append({'time': k, column: v[1] / v[0]}, ignore_index=True)
            else:
                result_df.loc[result_df['Time'] == k, column] = v[1] / v[0]
    result_df = result_df[result_df['Time'].apply(lambda x: x.is_integer())]
    result_df = result_df.sort_values(by='Time')

    result_df = result_df.reset_index(drop=True)
    result_df['id'] = result_df.index + 1

    result_df = result_df.fillna(method='ffill')

    return result_df


# 多秒一个
def interpolate_data(df):
    # 将时间列设置为索引
    df = df.set_index('time')

    # 计算时间间隔
    time_diff = df.index.to_series().diff().fillna(0)

    # 找到时间间隔大于一秒的索引
    mask = time_diff > 1
    indexes = df[mask].index

    bitrate_list = [141, 647, 1093, 1904, 3886]

    # 遍历需要插值的索引
    for i, index in enumerate(indexes):
        # 获取前后两条记录
        if i < 1 or i >= len(indexes) - 1:
            continue
        prev_row = df.loc[indexes[i - 1]]
        next_row = df.loc[indexes[i + 1]]

        # 计算前后两秒之间的线性变化
        num_rows = int(time_diff[index])
        diff_bitrate = (next_row['Bitrate_Downloading'] - prev_row['Bitrate_Downloading']) / num_rows
        diff_buffer = (next_row['Buffer_Length'] - prev_row['Buffer_Length']) / num_rows
        diff_bandwidth = (next_row['BandWidth'] - prev_row['BandWidth']) / num_rows

        # 插入缺失的行
        for i in range(1, num_rows):
            new_time = index - num_rows - i
            new_bitrate = prev_row['Bitrate_Downloading'] + i * diff_bitrate
            new_bitrate = find_closest_value(bitrate_list, new_bitrate)
            new_buffer = prev_row['Buffer_Length'] + i * diff_buffer
            new_bandwidth = prev_row['BandWidth'] + i * diff_bandwidth

            new_row = pd.DataFrame({'Bitrate_Downloading': new_bitrate,
                                    'Buffer_Length': new_buffer,
                                    'BandWidth': new_bandwidth}, index=[new_time])

            df = pd.concat([df.loc[:new_time], new_row, df.loc[new_time:]])

    # 重新设置索引
    df = df.reset_index()

    df = df.rename(columns={'index': 'time'})

    df = df.sort_values(by='time')

    df = df.reset_index(drop=True)
    df['id'] = df.index + 1

    df = df.fillna(method='ffill')
    return df


def find_closest_value(lst, target):
    closest_value = None
    min_difference = float('inf')

    for value in lst:
        difference = abs(value - target)
        if difference < min_difference:
            min_difference = difference
            closest_value = value

    return closest_value


def plot_qoe_cdf(qoe_values):
    sorted_qoe = np.sort(qoe_values)
    cdf = np.arange(len(sorted_qoe)) / float(len(sorted_qoe))

    plt.plot(sorted_qoe, cdf, marker='.', markersize=2)

    plt.xlabel('QoE')
    plt.ylabel('CDF')
    plt.title('QoE CDF Distribution')

    plt.show()

# generate a len=100 random value list in [0,100]
# plot_qoe_cdf(np.random.randint(0, 100, 1000))
# plot_qoe_cdf([3, 4, 4, 5, 5, 5, 6, 7, 7, 7, 8, 8, 9])


# a=extract_column_from_df(apply_function_to_files(get_wave_list('fin2case/5000kbps/'), get_df),['id'])
def save_qoe_list_to_csv(qoes, path):
    df = pd.DataFrame(qoes, columns=['QoE'])
    df.to_csv(path, index=False)
    return None