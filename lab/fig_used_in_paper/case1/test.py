import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

import utils

base_dir = 'withtcp/tp/'


def plot_lines(x, df):
    # select first 60 rows
    x = [a for a in x if a<60]
    df = df.iloc[:len(x)]

    for column in df.columns:
       df[column]=df[column].rolling(window=5, min_periods=1).mean()  # 使用窗口大小为3的滑动平均
       df[column]=df[column].rolling(window=3, min_periods=1).mean()
       # df[column]=df[column].rolling(window=10, min_periods=1).mean()


    # convert columns in df to list[]

    # 计算上下界及平均值
    result=pd.DataFrame()
    result["ub"]=df.max(axis=1)
    result["lb"]=df.min(axis=1)
    result["avg"]=df.mean(axis=1)
    # df["lb"]=df["lb"].rolling(window=5, min_periods=1).max()
    # result["ub"]=result["ub"].rolling(window=5, min_periods=1).mean()
    # df["lb"]=df["lb"].rolling(window=5, min_periods=1).mean()
    # df["ub"]=df["ub"].rolling(window=5, min_periods=1).mean()
    # df["avg"]=df["avg"].rolling(window=5, min_periods=1).mean()

    # lines_data = np.array(df)

    upper_bound = np.array(result['ub'])
    lower_bound = np.array(result['lb'])
    average = np.array(result['avg'])

    # 计算上下界及平均值
    # upper_bound = np.max(lines, axis=-1)
    # lower_bound = np.min(lines, axis=-1)
    # average = np.mean(lines, axis=-1)

    # 绘制曲线
    for column in df.columns:
        plt.plot(x, df[column], alpha=0.1)

    # 绘制上下界
    plt.fill_between(x, lower_bound, upper_bound, color='red', alpha=0.3)
    plt.plot(x, upper_bound, color='orange', alpha=0.6),
    plt.plot(x, lower_bound, color='cyan', alpha=0.6),
    # 绘制平均值曲线
    plt.plot(x, average, linewidth=2, color='red')

    # 创建图例并指定要显示的曲线
    borderlines = [plt.Line2D(x, upper_bound, color='orange'),
                   plt.Line2D(x, lower_bound, color='cyan'),
                   plt.Line2D(x, average, color='red')]
    plt.legend(handles=borderlines,
               labels=['Upper Bound', 'Lower Bound', 'Average'])
    plt.title(base_dir)
    plt.ylabel('bitrate(kbps)')
    plt.xlabel('Time(s)')
    plt.xlim(0,60)
    plt.ylim(0,4000)
    plt.savefig(base_dir + f".svg")
    plt.show()

# 示例数据
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = 2 * np.sin(x)
y3 = 4 * np.sin(x)
y4 = np.cos(x)

# 调用函数绘制图形
# plot_lines(x, y1, y2, y3, y4)

dfs=utils.apply_function_to_files(utils.get_wave_list(base_dir), utils.get_df)
dfs=utils.apply_function_to_files(dfs,utils.convert_records_to_secondly)

thputs= utils.extract_column_from_df(dfs, ['bitrate'])
plot_lines(dfs[0]['time'],thputs)