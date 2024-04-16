from matplotlib import pyplot as plt
plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 指定使用的中文字体，如宋体、黑体等
plt.tight_layout()
plt.rcParams['font.size'] = 13


plt.figure(figsize=(6, 4))

data = [
    {'x': 0.35, 'y': 2.0228607, 'x_err': 0.50, 'y_err': 0.1, 'label': 'Bola'},
    {'x': 1.88, 'y': 2.5370267, 'x_err': 0.73, 'y_err': 0.22, 'label': 'Pensieve'},
    {'x': 17.73, 'y': 3.3761610, 'x_err': 1.48, 'y_err': 0.08, 'label': 'Comyco'},
    {'x': 0.13, 'y': 3.1220341, 'x_err': 0.88, 'y_err': 0.16, 'label': 'OMEN'}
]


for point in data:
    plt.scatter(point['x'], point['y'], label=point['label'], linewidths=4)
    plt.errorbar(point['x'], point['y'], xerr=point['x_err'], yerr=point['y_err'], capsize=4)

plt.annotate('Better', xy=(18, 2), xytext=(15,2.4),             arrowprops=dict(arrowstyle='<-',linewidth=4), fontsize=20)

plt.ylabel('Bitrate (Mbps)',fontsize=24)
plt.xlabel('Stall rate (%)',fontsize=24)
plt.gca().invert_xaxis()  # 颠倒 x 轴的数值方向
xticks = [1, 3, 5, 20]  # 非均匀刻度的位置
# plt.xticks(xticks, [''] * len(xticks))  # 将刻度标签设为空字符串
plt.xticks(fontsize=20)

plt.yticks(fontsize=20)
# upper center
plt.legend( loc='upper center')
plt.tight_layout()

plt.savefig('scatter.pdf', bbox_inches='tight')
plt.show()