import numpy as np

import utils


wave_list=utils.get_wave_list('.')

for wave in wave_list:
    df=utils.get_df(wave)
    avg_bitrate = df['bitrate'].mean()
    df.loc[df['buffer'] < 4, 'buffer'] = 0
    stall_time = utils.get_stall_time(df)
    print(f'{wave}: (avg_bitrate,stall_time) = ({avg_bitrate},{stall_time})')

wave_list = utils.get_wave_list('.')

bitrate_values = []
stall_time_values = []

for wave in wave_list:
    df = utils.get_df(wave)
    avg_bitrate = df['bitrate'].mean()
    df.loc[df['buffer'] < 4, 'buffer'] = 0
    stall_time = utils.get_stall_time(df)

    bitrate_values.append(avg_bitrate)
    stall_time_values.append(stall_time)

# 正则化
normalized_bitrate_values = (bitrate_values - np.mean(bitrate_values)) / np.std(bitrate_values)
normalized_stall_time_values = (stall_time_values - np.mean(stall_time_values)) / np.std(stall_time_values)

for i, wave in enumerate(wave_list):
    print(
        f'{wave}: (normalized_avg_bitrate, normalized_stall_time) = ({normalized_bitrate_values[i]}, {normalized_stall_time_values[i]+1})')