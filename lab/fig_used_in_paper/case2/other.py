import utils

wave_files =utils.get_wave_list('./source')
avg_bitrate_list = utils.apply_function_to_files(wave_files, utils.get_avg_bitrate)
# print mean
print(sum(avg_bitrate_list)/len(avg_bitrate_list))