import pandas as pd

import utils

based = './tcp/'
wave_list=utils.get_wave_list(based)
# dfs=utils.apply_function_to_files(wave_list, lambda file: utils.get_df(file))

# qoes=utils.apply_function_to_files(wave_list, lambda w: utils.get_one_qoe(w))

# read from qoes csv
qoes = pd.read_csv('./bola/bola_qoe.csv')
utils.plot_qoe_cdf(qoes['QoE'])
# save qoe list to csv file directly
# utils.save_qoe_list_to_csv(qoes,based+'qoe.csv')
