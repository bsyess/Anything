# -*- coding: utf-8 -*-
"""绘制答辩 PPT 所需的四张示意图(高换手/低换手术语)。运行: python3 draw_figures.py"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontProperties

ZH = FontProperties(fname="/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")

C_HF = "#2E75B6"      # 高换手通路
C_LF = "#C55A11"      # 低换手通路
C_FUSE = "#7030A0"    # 融合/修正
C_OUT = "#375623"     # 输出
C_GATE = "#BF8F00"    # 门控
C_REL = "#548235"     # 关系摘要
C_BG = "#FFFFFF"


def box(ax, xy, w, h, text, fc, fs=11, tc="white", ec=None, ls="-"):
    x, y = xy
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
        fc=fc, ec=ec if ec else "none", lw=1.4 if ec else 0, linestyle=ls, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, fontproperties=ZH, zorder=4, linespacing=1.5)


def arrow(ax, p0, p1, color="#595959", lw=1.8):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                shrinkA=2, shrinkB=2), zorder=2)


# ============================================================
# 图1:工作1 架构总览
# ============================================================
def fig_w1_architecture():
    fig, ax = plt.subplots(figsize=(13.2, 6.4), dpi=200)
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 6.4)
    ax.axis("off")
    fig.patch.set_facecolor(C_BG)

    box(ax, (0.25, 4.35), 1.9, 1.25, "高换手因子\nHF380  [B, T, 380]", C_HF, fs=11)
    box(ax, (0.25, 0.85), 1.9, 1.25, "低换手因子\nalpha1298", C_LF, fs=11)

    box(ax, (2.75, 4.35), 2.35, 1.25, "MLP-Mixer × N 层\n时间混合 + 因子混合\n(残差连接)", C_HF, fs=10)
    box(ax, (5.65, 4.35), 1.75, 1.25, "高换手表征\n$h$  [B, 160]", C_HF, fs=11)
    arrow(ax, (2.15, 4.98), (2.75, 4.98))
    arrow(ax, (5.10, 4.98), (5.65, 4.98))

    box(ax, (2.75, 0.85), 2.35, 1.25, "低换手动态特征\n[当前值, 一阶差分,\n更新掩码, 陈旧度age]", C_LF, fs=10)
    box(ax, (5.65, 0.85), 1.75, 1.25, "低换手表征\n$l$  [B, 160]", C_LF, fs=11)
    arrow(ax, (2.15, 1.48), (2.75, 1.48))
    arrow(ax, (5.10, 1.48), (5.65, 1.48))

    box(ax, (5.65, 2.65), 1.75, 1.1, "关系摘要\ncos / 距离 / 内积", C_REL, fs=10)
    arrow(ax, (6.5, 4.35), (6.5, 3.75), color=C_HF)
    arrow(ax, (6.5, 2.10), (6.5, 2.65), color=C_LF)

    box(ax, (8.15, 4.55), 2.3, 1.05, "基线预测头\n$y_{HF}$", C_HF, fs=11)
    box(ax, (8.15, 2.95), 2.3, 1.25, "分组 FiLM 调制\n+ K 组残差头  $\\Delta_{LF}$", C_FUSE, fs=10)
    box(ax, (8.15, 1.45), 2.3, 1.05, "交互修正头\n$\\Delta_{X}$", C_FUSE, fs=11)
    box(ax, (8.15, 0.15), 2.3, 0.95, "门控路由 Router\n$a_{LF},\\ a_{X}\\in(0,1)$", C_GATE, fs=10)

    arrow(ax, (7.40, 5.15), (8.15, 5.08), color=C_HF)
    arrow(ax, (7.40, 4.80), (8.15, 3.80), color=C_HF)
    arrow(ax, (7.40, 4.55), (8.15, 2.15), color=C_HF)
    arrow(ax, (7.40, 4.45), (8.15, 0.80), color=C_HF)
    arrow(ax, (7.40, 1.60), (8.15, 3.30), color=C_LF)
    arrow(ax, (7.40, 1.48), (8.15, 1.80), color=C_LF)
    arrow(ax, (7.40, 3.10), (8.15, 2.00), color=C_REL)
    arrow(ax, (7.40, 2.90), (8.15, 0.62), color=C_REL)

    box(ax, (11.05, 2.75), 1.9, 1.5,
        "$y = y_{HF}$\n$+\\ a_{LF}\\cdot\\Delta_{LF}$\n$+\\ a_{X}\\cdot\\Delta_{X}$", C_OUT, fs=12)
    arrow(ax, (10.45, 5.08), (11.05, 3.95), color=C_HF)
    arrow(ax, (10.45, 3.58), (11.05, 3.50), color=C_FUSE)
    arrow(ax, (10.45, 1.98), (11.05, 3.05), color=C_FUSE)
    arrow(ax, (10.45, 0.62), (11.05, 2.85), color=C_GATE)

    ax.text(6.6, 6.15, "工作1:高换手主干 + 低换手动态修正", ha="center",
            fontsize=15, fontproperties=ZH, weight="bold", color="#1F1F1F")
    plt.tight_layout()
    plt.savefig("w1_architecture.png", bbox_inches="tight", facecolor=C_BG)
    plt.close(fig)
    print("saved w1_architecture.png")


# ============================================================
# 图2:低换手因子取值变化稀疏示意
# ============================================================
def fig_lowturnover_dynamics():
    T = 40
    t = np.arange(T)
    lf = np.zeros(T)
    lf[:8] = 0.6
    lf[8:21] = 1.1
    lf[21:33] = 0.75
    lf[33:] = 1.35
    updates = [8, 21, 33]

    fig, axes = plt.subplots(2, 1, figsize=(10.5, 5.2), dpi=200,
                             gridspec_kw={"height_ratios": [2.2, 1.0]}, sharex=True)
    ax = axes[0]
    ax.step(t, lf, where="post", color=C_LF, lw=2.4, label="低换手因子(取值长期不变,阶梯状)")
    hf = 1.0 + 0.25 * np.sin(t / 2.2) + 0.08 * np.random.RandomState(7).randn(T)
    ax.plot(t, hf, color=C_HF, lw=1.4, alpha=0.85, label="高换手因子(逐日变化)")
    for u in updates:
        ax.axvline(u, color=C_LF, ls="--", lw=1.0, alpha=0.5)
        ax.annotate("变化", (u, lf[u] + 0.07), fontsize=10, color=C_LF,
                    fontproperties=ZH, ha="center")
    ax.annotate("", xy=(32.6, 0.62), xytext=(21.4, 0.62),
                arrowprops=dict(arrowstyle="<->", color="#404040", lw=1.4))
    ax.text(27, 0.50, "取值不变期:直接喂序列 → 大量冗余", fontsize=10.5,
            fontproperties=ZH, ha="center", color="#404040")
    ax.set_ylabel("因子取值", fontproperties=ZH, fontsize=11)
    ax.legend(prop=ZH, fontsize=10, loc="upper left", framealpha=0.9)
    ax.set_title("低换手因子取值变化稀疏(均为日频数据)→ 用四个动态特征刻画",
                 fontproperties=ZH, fontsize=13, weight="bold")
    ax.grid(alpha=0.25)

    ax2 = axes[1]
    age = np.zeros(T)
    c = 0
    for i in range(1, T):
        c = 0 if i in updates else c + 1
        age[i] = c
    ax2.plot(t, age / (T - 1), color=C_FUSE, lw=2.0, label="age(距上次变化的归一化时长)")
    mask = np.zeros(T)
    mask[updates] = 1
    ax2.stem(t, mask * 0.9, linefmt=C_REL, markerfmt=" ", basefmt=" ",
             label="更新掩码 mask(当日是否变化)")
    ax2.set_xlabel("交易日", fontproperties=ZH, fontsize=11)
    ax2.set_ylabel("动态特征", fontproperties=ZH, fontsize=11)
    ax2.legend(prop=ZH, fontsize=10, loc="upper left", ncol=2, framealpha=0.9)
    ax2.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig("lowturnover_dynamics.png", bbox_inches="tight")
    plt.close(fig)
    print("saved lowturnover_dynamics.png")


# ============================================================
# 图3:工作2 主干架构
# ============================================================
def fig_w2_architecture():
    fig, ax = plt.subplots(figsize=(13.2, 6.6), dpi=200)
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 6.6)
    ax.axis("off")
    fig.patch.set_facecolor(C_BG)

    box(ax, (0.2, 4.0), 1.7, 1.2, "高换手因子\nHF380\n[B, T, 380]", C_HF, fs=10.5)

    # Block × N 虚线大框
    ax.add_patch(mpatches.FancyBboxPatch(
        (2.25, 2.2), 7.3, 3.9, boxstyle="round,pad=0.03,rounding_size=0.1",
        fc="#F2F4F8", ec="#8496B0", lw=1.6, linestyle="--", zorder=1))
    ax.text(5.9, 5.82, "Graph-aware Block × N 层", ha="center", fontsize=12.5,
            fontproperties=ZH, weight="bold", color="#333F50")

    box(ax, (2.5, 4.35), 2.1, 1.1, "时间混合 MLP\n(+ 残差)", C_HF, fs=10.5)
    box(ax, (5.0, 4.35), 2.1, 1.1, "因子 → token\n每因子时序→16维\n+ 因子 ID 嵌入", C_FUSE, fs=9.5)
    box(ax, (7.4, 4.35), 1.95, 1.1, "图门控\n因子末态→\n缩放+偏置", C_GATE, fs=9.5)
    box(ax, (2.5, 2.5), 3.1, 1.1, "线性注意力 × L\n因子间动态交互\n复杂度 O(C)", C_FUSE, fs=10)
    box(ax, (6.1, 2.5), 3.25, 1.1, "还原回时序 × 输出门\n(+ 残差, 小初始 scale)", C_FUSE, fs=10)

    arrow(ax, (1.9, 4.9), (2.5, 4.9))
    arrow(ax, (4.6, 4.9), (5.0, 4.9))
    arrow(ax, (7.1, 4.9), (7.4, 4.9))
    arrow(ax, (8.35, 4.35), (4.05, 3.6), color="#595959")
    arrow(ax, (5.6, 3.05), (6.1, 3.05))

    # 主干输出
    box(ax, (10.1, 4.35), 2.85, 1.1, "LayerNorm + 池化\n→ 表征 h", C_HF, fs=10.5)
    arrow(ax, (9.55, 4.9), (10.1, 4.9))
    box(ax, (10.1, 2.95), 2.85, 0.95, "主预测头  $y_{main}$", C_HF, fs=11)
    arrow(ax, (11.5, 4.35), (11.5, 3.9), color=C_HF)

    # 决策感知输出端
    box(ax, (0.2, 0.35), 2.5, 1.15, "更新统计量(6维)\n各层修正幅度\nRMS 比值等", C_REL, fs=9.5)
    arrow(ax, (5.9, 2.2), (2.7, 1.3), color=C_REL)
    box(ax, (3.3, 0.35), 2.15, 1.15, "Δ头\n表征末两步差分\n小残差修正", C_FUSE, fs=9.5)
    box(ax, (5.85, 0.35), 2.3, 1.15, "决策感知辅助头\nα 门控(σ, 偏置−1.5)\n× 辅助预测", C_GATE, fs=9.5)
    box(ax, (8.55, 0.35), 2.3, 1.15, "幅值门\ntanh 微调预测幅度\n方向不变", C_GATE, fs=9.5)
    arrow(ax, (2.7, 0.92), (3.3, 0.92), color=C_REL)
    arrow(ax, (5.45, 0.92), (5.85, 0.92), color=C_REL)
    arrow(ax, (8.15, 0.92), (8.55, 0.92), color=C_REL)

    box(ax, (11.25, 0.3), 1.7, 1.25, "最终预测\n$y$", C_OUT, fs=12)
    arrow(ax, (11.5, 2.95), (11.85, 1.55), color=C_HF)
    arrow(ax, (10.85, 0.92), (11.25, 0.92), color=C_GATE)

    ax.text(6.6, 6.35, "工作2:纯高换手主干升级(不加入低换手因子)", ha="center",
            fontsize=15, fontproperties=ZH, weight="bold", color="#1F1F1F")
    plt.tight_layout()
    plt.savefig("w2_architecture.png", bbox_inches="tight", facecolor=C_BG)
    plt.close(fig)
    print("saved w2_architecture.png")


# ============================================================
# 图4:工作3 组合示意
# ============================================================
def fig_w3_overview():
    fig, ax = plt.subplots(figsize=(13.2, 5.6), dpi=200)
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    fig.patch.set_facecolor(C_BG)

    # 数据端
    box(ax, (0.25, 3.6), 2.0, 1.2, "原始高换手\nraw_HF380", C_HF, fs=10.5)
    box(ax, (2.85, 3.6), 3.3, 1.2,
        "行业软中性化(数据端,新)\nsoft_HF = raw_HF − λ·行业均值\nλ 多组实测,取 0.8", "#1F4E79", fs=10)
    arrow(ax, (2.25, 4.2), (2.85, 4.2))

    box(ax, (6.85, 3.6), 3.1, 1.2, "工作2 主干\n图感知因子混合\n+ 决策感知输出端", C_HF, fs=10)
    arrow(ax, (6.15, 4.2), (6.85, 4.2))
    ax.text(8.4, 5.0, "来自工作2", ha="center", fontsize=10.5, color=C_HF,
            fontproperties=ZH, weight="bold")

    box(ax, (10.55, 3.6), 1.7, 1.2, "$y_{HF}$ + 表征 $h$", C_HF, fs=11)
    arrow(ax, (9.95, 4.2), (10.55, 4.2))

    # 低换手通路
    box(ax, (0.25, 1.1), 2.0, 1.2, "低换手因子\nalpha1298", C_LF, fs=10.5)
    box(ax, (2.85, 1.1), 3.3, 1.2, "动态编码(五元组)\n当前值/差分/掩码/age\n+ 窗口均值", C_LF, fs=10)
    arrow(ax, (2.25, 1.7), (2.85, 1.7))
    box(ax, (6.85, 1.1), 3.1, 1.2,
        "双专家修正 + 门控\nLF专家 / 交互专家\n(主干侧输入 detach)", C_FUSE, fs=10)
    arrow(ax, (6.15, 1.7), (6.85, 1.7))
    ax.text(8.4, 0.7, "来自工作1(框架思想)", ha="center", fontsize=10.5, color=C_FUSE,
            fontproperties=ZH, weight="bold")
    arrow(ax, (11.4, 3.6), (9.6, 2.3), color=C_HF)

    box(ax, (10.55, 1.1), 2.4, 1.2,
        "$y = y_{HF} + s\\cdot(a_{LF}\\Delta_{LF}$\n$+\\ a_{X}\\Delta_{X})$", C_OUT, fs=10.5)
    arrow(ax, (9.95, 1.7), (10.55, 1.7), color=C_FUSE)

    ax.text(6.6, 5.35, "工作3:工作2 主干 × 工作1 融合框架 + 行业软中性化数据", ha="center",
            fontsize=15, fontproperties=ZH, weight="bold", color="#1F1F1F")
    plt.tight_layout()
    plt.savefig("w3_overview.png", bbox_inches="tight", facecolor=C_BG)
    plt.close(fig)
    print("saved w3_overview.png")


if __name__ == "__main__":
    fig_w1_architecture()
    fig_lowturnover_dynamics()
    fig_w2_architecture()
    fig_w3_overview()
