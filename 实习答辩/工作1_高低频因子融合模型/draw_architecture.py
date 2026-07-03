# -*- coding: utf-8 -*-
"""绘制工作1模型架构示意图(去掉 industry / pool 后的核心模型)。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontProperties

ZH = FontProperties(fname="/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")

C_HF = "#2E75B6"      # 高频通路
C_LF = "#C55A11"      # 低频通路
C_FUSE = "#7030A0"    # 融合/修正
C_OUT = "#375623"     # 输出
C_BG = "#FFFFFF"


def box(ax, xy, w, h, text, fc, fs=11, tc="white", lw=0):
    x, y = xy
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
        fc=fc, ec="none" if lw == 0 else "#404040", lw=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, fontproperties=ZH, zorder=4, linespacing=1.5)


def arrow(ax, p0, p1, color="#595959", lw=1.8, style="-|>"):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                shrinkA=2, shrinkB=2), zorder=2)


fig, ax = plt.subplots(figsize=(13.2, 6.4), dpi=200)
ax.set_xlim(0, 13.2)
ax.set_ylim(0, 6.4)
ax.axis("off")
fig.patch.set_facecolor(C_BG)

# ---------------- 输入 ----------------
box(ax, (0.25, 4.35), 1.9, 1.25, "高频因子序列\nHF  [B, T, 380]", C_HF, fs=11)
box(ax, (0.25, 0.85), 1.9, 1.25, "低频因子序列\nLF  [B, T, 1289]", C_LF, fs=11)

# ---------------- HF 通路 ----------------
box(ax, (2.75, 4.35), 2.35, 1.25,
    "MLP-Mixer × N 层\n时间混合 + 因子混合\n(残差连接)", C_HF, fs=10)
box(ax, (5.65, 4.35), 1.75, 1.25, "HF 表征\n$h$  [B, 160]", C_HF, fs=11)
arrow(ax, (2.15, 4.98), (2.75, 4.98))
arrow(ax, (5.10, 4.98), (5.65, 4.98))

# ---------------- LF 通路 ----------------
box(ax, (2.75, 0.85), 2.35, 1.25,
    "低频动态特征\n[当前值, 一阶差分,\n更新掩码, 陈旧度age]", C_LF, fs=10)
box(ax, (5.65, 0.85), 1.75, 1.25, "LF 表征\n$l$  [B, 160]", C_LF, fs=11)
arrow(ax, (2.15, 1.48), (2.75, 1.48))
arrow(ax, (5.10, 1.48), (5.65, 1.48))

# ---------------- 关系摘要 ----------------
box(ax, (5.65, 2.65), 1.75, 1.1, "关系摘要\ncos / 距离 / 内积", "#548235", fs=10)
arrow(ax, (6.5, 4.35), (6.5, 3.75), color=C_HF)
arrow(ax, (6.5, 2.10), (6.5, 2.65), color=C_LF)

# ---------------- 三个头 ----------------
box(ax, (8.15, 4.55), 2.3, 1.05, "基线预测头\n$y_{HF}$", C_HF, fs=11)
box(ax, (8.15, 2.95), 2.3, 1.25, "分组 FiLM 调制\n+ K 组残差头  $\\Delta_{LF}$", C_FUSE, fs=10)
box(ax, (8.15, 1.45), 2.3, 1.05, "交互修正头\n$\\Delta_{X}$", C_FUSE, fs=11)
box(ax, (8.15, 0.15), 2.3, 0.95, "门控路由 Router\n$a_{LF},\\ a_{X}\\in(0,1)$", "#BF8F00", fs=10)

# HF repr 到三个头
arrow(ax, (7.40, 5.15), (8.15, 5.08), color=C_HF)
arrow(ax, (7.40, 4.80), (8.15, 3.80), color=C_HF)
arrow(ax, (7.40, 4.55), (8.15, 2.15), color=C_HF)
arrow(ax, (7.40, 4.45), (8.15, 0.80), color=C_HF)
# LF repr 到 FiLM / 交互
arrow(ax, (7.40, 1.60), (8.15, 3.30), color=C_LF)
arrow(ax, (7.40, 1.48), (8.15, 1.80), color=C_LF)
# 关系摘要到交互/路由
arrow(ax, (7.40, 3.10), (8.15, 2.00), color="#548235")
arrow(ax, (7.40, 2.90), (8.15, 0.62), color="#548235")

# ---------------- 输出合成 ----------------
box(ax, (11.05, 2.75), 1.9, 1.5,
    "$y = y_{HF}$\n$+\\ a_{LF}\\cdot\\Delta_{LF}$\n$+\\ a_{X}\\cdot\\Delta_{X}$",
    C_OUT, fs=12)
arrow(ax, (10.45, 5.08), (11.05, 3.95), color=C_HF)
arrow(ax, (10.45, 3.58), (11.05, 3.50), color=C_FUSE)
arrow(ax, (10.45, 1.98), (11.05, 3.05), color=C_FUSE)
arrow(ax, (10.45, 0.62), (11.05, 2.85), color="#BF8F00")

ax.text(6.6, 6.15, "工作1:高频主干 + 低频动态修正的因子融合模型",
        ha="center", fontsize=15, fontproperties=ZH, weight="bold", color="#1F1F1F")

plt.tight_layout()
plt.savefig("architecture.png", bbox_inches="tight", facecolor=C_BG)
print("saved architecture.png")
