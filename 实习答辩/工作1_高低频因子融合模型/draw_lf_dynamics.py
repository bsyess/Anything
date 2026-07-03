# -*- coding: utf-8 -*-
"""低频因子陈旧性与动态特征四元组示意图。"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ZH = FontProperties(fname="/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")

T = 40
t = np.arange(T)
lf = np.zeros(T)
# 阶梯状:低频因子只在少数交易日更新
lf[:8] = 0.6
lf[8:21] = 1.1
lf[21:33] = 0.75
lf[33:] = 1.35
updates = [8, 21, 33]

fig, axes = plt.subplots(2, 1, figsize=(10.5, 5.2), dpi=200,
                         gridspec_kw={"height_ratios": [2.2, 1.0]}, sharex=True)

ax = axes[0]
ax.step(t, lf, where="post", color="#C55A11", lw=2.4, label="低频因子取值(阶梯状)")
hf = 1.0 + 0.25 * np.sin(t / 2.2) + 0.08 * np.random.RandomState(7).randn(T)
ax.plot(t, hf, color="#2E75B6", lw=1.4, alpha=0.85, label="高频因子(每日更新)")
for u in updates:
    ax.axvline(u, color="#C55A11", ls="--", lw=1.0, alpha=0.5)
    ax.annotate("更新", (u, lf[u] + 0.07), fontsize=10, color="#C55A11",
                fontproperties=ZH, ha="center")
ax.annotate("", xy=(32.6, 0.62), xytext=(21.4, 0.62),
            arrowprops=dict(arrowstyle="<->", color="#404040", lw=1.4))
ax.text(27, 0.50, "陈旧期:取值不变,信息逐渐过时", fontsize=10.5,
        fontproperties=ZH, ha="center", color="#404040")
ax.set_ylabel("因子取值", fontproperties=ZH, fontsize=11)
ax.legend(prop=ZH, fontsize=10, loc="upper left", framealpha=0.9)
ax.set_title("低频因子的稀疏更新问题 → 用四个动态特征刻画", fontproperties=ZH,
             fontsize=13, weight="bold")
ax.grid(alpha=0.25)

ax2 = axes[1]
age = np.zeros(T)
c = 0
for i in range(1, T):
    c = 0 if i in updates else c + 1
    age[i] = c
ax2.plot(t, age / (T - 1), color="#7030A0", lw=2.0, label="age(距上次更新的归一化时长)")
mask = np.zeros(T)
mask[updates] = 1
ax2.stem(t, mask * 0.9, linefmt="#548235", markerfmt=" ", basefmt=" ",
         label="更新掩码 mask(当日是否更新)")
ax2.set_xlabel("交易日", fontproperties=ZH, fontsize=11)
ax2.set_ylabel("动态特征", fontproperties=ZH, fontsize=11)
ax2.legend(prop=ZH, fontsize=10, loc="upper left", ncol=2, framealpha=0.9)
ax2.grid(alpha=0.25)

plt.tight_layout()
plt.savefig("lf_dynamics.png", bbox_inches="tight")
print("saved lf_dynamics.png")
