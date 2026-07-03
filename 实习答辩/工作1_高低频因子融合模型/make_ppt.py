# -*- coding: utf-8 -*-
"""
生成实习答辩 PPT —— 工作1:高低频因子融合模型。
重点:原理推导(少公式)+ 结果展示。
运行: python3 make_ppt.py
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---------- 主题色 ----------
INK = RGBColor(0x1F, 0x1F, 0x1F)
GREY = RGBColor(0x59, 0x59, 0x59)
BLUE = RGBColor(0x2E, 0x75, 0xB6)     # 高频
ORANGE = RGBColor(0xC5, 0x5A, 0x11)   # 低频
PURPLE = RGBColor(0x70, 0x30, 0xA0)   # 融合
GREEN = RGBColor(0x37, 0x56, 0x23)    # 输出/结论
GOLD = RGBColor(0xBF, 0x8F, 0x00)     # 门控
LIGHT = RGBColor(0xF2, 0xF4, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Microsoft YaHei"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]


def _set_font(run, size, color, bold=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    r = run._r
    rPr = r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", FONT)


def add_slide():
    return prs.slides.add_slide(BLANK)


def add_rect(slide, x, y, w, h, fill, line=None, shadow=False, round_=False):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if round_ else MSO_SHAPE.RECTANGLE,
        x, y, w, h)
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1.2)
    shp.shadow.inherit = False
    if round_:
        try:
            shp.adjustments[0] = 0.08
        except Exception:
            pass
    return shp


def add_text(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, wrap=True):
    """lines: list of (text, size, color, bold, level) 或 (text, size, color, bold)"""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    first = True
    for item in lines:
        text, size, color, bold = item[0], item[1], item[2], item[3]
        level = item[4] if len(item) > 4 else 0
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.level = level
        p.space_after = Pt(size * 0.45)
        run = p.add_run()
        run.text = text
        _set_font(run, size, color, bold)
    return tb


def slide_header(slide, title, tag=""):
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.14), BLUE)
    add_text(slide, Inches(0.55), Inches(0.32), Inches(11.0), Inches(0.8),
             [(title, 26, INK, True)])
    if tag:
        add_text(slide, Inches(10.6), Inches(0.42), Inches(2.35), Inches(0.5),
                 [(tag, 12, GREY, False)], align=PP_ALIGN.RIGHT)
    add_rect(slide, Inches(0.58), Inches(1.02), Inches(1.6), Pt(3), GOLD)


def bullet_block(slide, x, y, w, items, size=15):
    lines = []
    for it in items:
        if isinstance(it, tuple):
            lines.append(it)
        elif it.lstrip().startswith("•") or it.startswith("    "):
            lines.append((it, size, INK, False))
        else:
            lines.append(("•  " + it, size, INK, False))
    add_text(slide, x, y, w, Inches(4), lines)


def add_placeholder(slide, x, y, w, h, tip):
    shp = add_rect(slide, x, y, w, h, LIGHT, line=GREY, round_=True)
    shp.line.dash_style = 4  # dashed
    tf = shp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = tip
    _set_font(run, 13, GREY, False)


# ============================================================
# 1. 封面
# ============================================================
s = add_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, WHITE)
add_rect(s, 0, 0, SLIDE_W, Inches(0.22), BLUE)
add_rect(s, 0, Inches(7.28), SLIDE_W, Inches(0.22), BLUE)
add_text(s, Inches(1.2), Inches(2.15), Inches(11.0), Inches(1.6),
         [("高低频因子融合:高频主干 + 低频动态修正", 36, INK, True),
          ("Dynamic Low-Frequency Correction for Multi-Frequency Factor Models", 16, GREY, False)])
add_rect(s, Inches(1.25), Inches(3.62), Inches(2.2), Pt(4), GOLD)
add_text(s, Inches(1.2), Inches(3.95), Inches(11.0), Inches(1.2),
         [("实习答辩 · 工作一", 20, BLUE, True),
          ("汇报人:XXX        日期:2026-XX-XX        部门:XXX", 14, GREY, False)])

# ============================================================
# 2. 汇报结构
# ============================================================
s = add_slide()
slide_header(s, "汇报结构", "总览")
titles = [("工作一", "高低频因子融合模型", "本次汇报重点:原理 + 回测结果", BLUE),
          ("工作二", "(标题占位,请替换)", "一句话概括工作二", PURPLE),
          ("工作三", "(标题占位,请替换)", "一句话概括工作三", GREEN)]
for i, (t1, t2, t3, c) in enumerate(titles):
    x = Inches(0.7 + i * 4.15)
    card = add_rect(s, x, Inches(1.9), Inches(3.75), Inches(3.6), LIGHT, round_=True)
    add_rect(s, x, Inches(1.9), Inches(3.75), Inches(0.55), c, round_=False)
    add_text(s, x, Inches(1.95), Inches(3.75), Inches(0.5),
             [(t1, 16, WHITE, True)], align=PP_ALIGN.CENTER)
    add_text(s, x + Inches(0.3), Inches(2.75), Inches(3.15), Inches(2.4),
             [(t2, 17, INK, True), ("", 6, INK, False), (t3, 13, GREY, False)])
add_text(s, Inches(0.7), Inches(5.9), Inches(12.0), Inches(0.6),
         [("本部分聚焦工作一:先讲模型设计的原理与直觉,再展示回测结果。", 15, GREY, False)])

# ============================================================
# 3. 背景与动机
# ============================================================
s = add_slide()
slide_header(s, "背景与动机:两类因子,两种节奏", "工作一 · 问题")
# 左:两类因子对比卡片
add_rect(s, Inches(0.7), Inches(1.45), Inches(5.6), Inches(1.9), RGBColor(0xE8, 0xF0, 0xF9), round_=True)
add_text(s, Inches(0.95), Inches(1.6), Inches(5.2), Inches(1.7),
         [("高频因子(量价类,约 380 维)", 16, BLUE, True),
          ("•  每个交易日都有新值,信息新鲜、噪声大", 13.5, INK, False),
          ("•  刻画短期交易行为,是收益预测的主力", 13.5, INK, False)])
add_rect(s, Inches(0.7), Inches(3.55), Inches(5.6), Inches(1.9), RGBColor(0xFB, 0xEE, 0xE4), round_=True)
add_text(s, Inches(0.95), Inches(3.7), Inches(5.2), Inches(1.7),
         [("低频因子(基本面类,约 1300 维)", 16, ORANGE, True),
          ("•  按财报/月度节奏稀疏更新,呈阶梯状", 13.5, INK, False),
          ("•  信息含量高但\u201c陈旧\u201d,直接拼接会被噪声淹没", 13.5, INK, False)])
# 右:核心矛盾
add_rect(s, Inches(6.7), Inches(1.45), Inches(6.0), Inches(4.0), LIGHT, round_=True)
add_text(s, Inches(7.0), Inches(1.7), Inches(5.5), Inches(3.6),
         [("直接把两类因子拼在一起训练的问题", 16, INK, True),
          ("", 6, INK, False),
          ("•  更新频率错配:低频因子大部分日期取值不变,梯度信号稀疏", 14, INK, False),
          ("•  陈旧性:财报发布后信息价值随时间衰减,模型无法感知\u201c多旧\u201d", 14, INK, False),
          ("•  尺度与分布差异:两类因子统计性质差别大,共享一个主干互相干扰", 14, INK, False)])
add_rect(s, Inches(0.7), Inches(5.85), Inches(12.0), Inches(1.0), RGBColor(0xEB, 0xF2, 0xE8), round_=True)
add_text(s, Inches(1.0), Inches(5.98), Inches(11.4), Inches(0.8),
         [("设计思路:不追求\u201c一个网络吃掉所有因子\u201d,而是让高频做基线、低频做修正,并让模型自己学会\u201c什么时候该信低频\u201d。", 15, GREEN, True)])

# ============================================================
# 4. 总体思路(核心公式)
# ============================================================
s = add_slide()
slide_header(s, "总体思路:基线 + 门控残差修正", "工作一 · 原理")
add_rect(s, Inches(1.5), Inches(1.55), Inches(10.3), Inches(1.25), RGBColor(0xEE, 0xE9, 0xF5), round_=True)
add_text(s, Inches(1.5), Inches(1.72), Inches(10.3), Inches(0.95),
         [("y  =  y_HF  +  a_LF · Δ_LF  +  a_X · Δ_X", 26, PURPLE, True)],
         align=PP_ALIGN.CENTER)
cards = [
    ("y_HF:高频基线", BLUE,
     "MLP-Mixer 编码高频序列后直接出的预测,单独可用,是整个模型的\u201c保底\u201d。"),
    ("Δ_LF:低频修正", ORANGE,
     "低频信息经 FiLM 调制后给出的残差修正量,只负责\u201c纠偏\u201d而不是重新预测。"),
    ("Δ_X:交互修正", PURPLE,
     "高低频表征的乘积、差值等交互特征给出的二阶修正,捕捉两者的耦合信息。"),
    ("a_LF, a_X:门控", GOLD,
     "sigmoid 门控 ∈ (0,1),逐样本决定修正强度;初始化偏向 0,从纯高频基线温和起步。"),
]
for i, (t, c, desc) in enumerate(cards):
    x = Inches(0.7 + (i % 2) * 6.1)
    y = Inches(3.15 + (i // 2) * 1.85)
    add_rect(s, x, y, Inches(5.85), Inches(1.65), LIGHT, round_=True)
    add_rect(s, x, y, Inches(0.12), Inches(1.65), c)
    add_text(s, x + Inches(0.35), y + Inches(0.12), Inches(5.35), Inches(1.45),
             [(t, 15, c, True), (desc, 12.5, INK, False)])
add_text(s, Inches(0.7), Inches(6.85), Inches(12.0), Inches(0.5),
         [("关键性质:当门控趋于 0 时模型退化为纯高频基线 —— 低频信息\u201c只能帮忙、不能捣乱\u201d。", 14, GREEN, True)])

# ============================================================
# 5. 模型架构总览
# ============================================================
s = add_slide()
slide_header(s, "模型架构总览", "工作一 · 架构")
s.shapes.add_picture("architecture.png", Inches(0.45), Inches(1.35), width=Inches(12.45))
add_text(s, Inches(0.7), Inches(6.75), Inches(12.0), Inches(0.6),
         [("高频与低频各自独立编码到同一维度(160 维),再通过 FiLM 调制、交互头与门控路由完成融合。", 14, GREY, False)])

# ============================================================
# 6. 原理1:高频主干 MLP-Mixer
# ============================================================
s = add_slide()
slide_header(s, "原理一:高频主干 —— MLP-Mixer", "工作一 · 原理")
bullet_block(s, Inches(0.7), Inches(1.45), Inches(6.1), [
    ("为什么不用 Transformer / RNN?", 16, BLUE, True),
    "•  截面因子数据的\u201c时间模式\u201d相对固定,不需要动态注意力",
    "•  纯 MLP 结构参数少、训练稳、推理快,更适合日频调仓的生产环境",
    ("", 8, INK, False),
    ("两个方向交替混合", 16, BLUE, True),
    "•  时间混合:固定因子,沿 T 个交易日做 MLP —— 学\u201c时序形态\u201d",
    "•  因子混合:固定时间,沿 380 个因子做 MLP —— 学\u201c因子间关系\u201d",
    "•  每步都带 LayerNorm + 残差连接,堆叠 N 层后取最后时刻的表征",
], size=14)
# 右侧:mixer block 示意
x0, y0 = Inches(7.3), Inches(1.55)
add_rect(s, x0, y0, Inches(5.3), Inches(4.9), LIGHT, round_=True)
add_text(s, x0, y0 + Inches(0.15), Inches(5.3), Inches(0.5),
         [("Mixer Block(× N 层)", 15, INK, True)], align=PP_ALIGN.CENTER)
steps = [("输入  [B, T, C]", GREY),
         ("LayerNorm → 转置 [B, C, T]", BLUE),
         ("时间混合 MLP(沿 T)+ 残差", BLUE),
         ("LayerNorm", ORANGE),
         ("因子混合 MLP(沿 C)+ 残差", ORANGE),
         ("输出  [B, T, C]", GREY)]
for i, (txt, c) in enumerate(steps):
    yy = y0 + Inches(0.75 + i * 0.68)
    add_rect(s, x0 + Inches(0.7), yy, Inches(3.9), Inches(0.52), WHITE, line=c, round_=True)
    add_text(s, x0 + Inches(0.7), yy + Inches(0.04), Inches(3.9), Inches(0.45),
             [(txt, 12.5, c if c != GREY else INK, False)], align=PP_ALIGN.CENTER)
add_text(s, Inches(0.7), Inches(6.7), Inches(12.0), Inches(0.6),
         [("直觉:相当于在\u201c时间 × 因子\u201d的表格上,交替做行方向和列方向的特征提取。", 14, GREEN, True)])

# ============================================================
# 7. 原理2:低频动态编码
# ============================================================
s = add_slide()
slide_header(s, "原理二:低频因子的动态编码", "工作一 · 原理")
s.shapes.add_picture("lf_dynamics.png", Inches(0.55), Inches(1.35), width=Inches(7.5))
bullet_block(s, Inches(8.3), Inches(1.5), Inches(4.4), [
    ("不喂整段序列,只喂四个动态量:", 15, ORANGE, True),
    "•  当前值:最新一期取值",
    "•  一阶差分:这次更新改了多少",
    "•  更新掩码:今天是否刚更新",
    "•  陈旧度 age:距上次更新多久(归一化)",
    ("", 8, INK, False),
    ("为什么有效?", 15, ORANGE, True),
    "•  低频序列大部分时间是常数,整段喂入浪费容量",
    "•  四元组恰好保留了\u201c值 + 变化 + 新鲜度\u201d的全部有效信息",
    "•  模型可学到\u201c刚更新的财报权重高、陈旧的打折\u201d",
], size=13)

# ============================================================
# 8. 原理3:分组 FiLM
# ============================================================
s = add_slide()
slide_header(s, "原理三:分组 FiLM 调制 —— 让高频给低频\u201c划重点\u201d", "工作一 · 原理")
add_rect(s, Inches(0.7), Inches(1.5), Inches(6.3), Inches(1.15), RGBColor(0xEE, 0xE9, 0xF5), round_=True)
add_text(s, Inches(0.7), Inches(1.62), Inches(6.3), Inches(0.9),
         [("l̃ₖ = (1 + s·γₖ(h)) ⊙ l  +  s·βₖ(h)", 20, PURPLE, True),
          ("γ、β 由高频表征 h 生成,对低频表征 l 做逐维缩放与平移", 12, GREY, False)],
         align=PP_ALIGN.CENTER)
bullet_block(s, Inches(0.7), Inches(2.95), Inches(6.3), [
    ("FiLM 的直觉", 15, PURPLE, True),
    "•  低频信息的价值取决于当前市场状态(由高频感知)",
    "•  γ 相当于\u201c逐维音量旋钮\u201d:放大有用维度、压低无关维度",
    "•  缩放系数 s=0.3 限制调制幅度,保证训练稳定",
    ("", 6, INK, False),
    ("为什么分 K=3 组?(软 MoE)", 15, PURPLE, True),
    "•  不同市场状态下低频的\u201c用法\u201d不同,单套 γ/β 表达力不够",
    "•  3 组 FiLM + 3 个残差头,由 softmax 路由按样本加权",
    "•  监控组权重熵,确认没有塌缩到单一组",
], size=13.5)
# 右图:分组示意
x0 = Inches(7.5)
add_rect(s, x0, Inches(1.5), Inches(5.1), Inches(5.0), LIGHT, round_=True)
add_text(s, x0, Inches(1.62), Inches(5.1), Inches(0.4),
         [("分组调制 + 软路由", 14, INK, True)], align=PP_ALIGN.CENTER)
add_rect(s, x0 + Inches(0.5), Inches(2.2), Inches(1.7), Inches(0.55), BLUE, round_=True)
add_text(s, x0 + Inches(0.5), Inches(2.26), Inches(1.7), Inches(0.45),
         [("高频表征 h", 12, WHITE, True)], align=PP_ALIGN.CENTER)
add_rect(s, x0 + Inches(2.9), Inches(2.2), Inches(1.7), Inches(0.55), ORANGE, round_=True)
add_text(s, x0 + Inches(2.9), Inches(2.26), Inches(1.7), Inches(0.45),
         [("低频表征 l", 12, WHITE, True)], align=PP_ALIGN.CENTER)
for k in range(3):
    yy = Inches(3.15 + k * 0.75)
    add_rect(s, x0 + Inches(0.5), yy, Inches(2.6), Inches(0.55), PURPLE, round_=True)
    add_text(s, x0 + Inches(0.5), yy + Inches(0.05), Inches(2.6), Inches(0.45),
             [(f"FiLM 组 {k+1}:γ{k+1}, β{k+1}", 12, WHITE, False)], align=PP_ALIGN.CENTER)
    add_text(s, x0 + Inches(3.2), yy + Inches(0.05), Inches(1.4), Inches(0.45),
             [(f"权重 w{k+1}", 12, GOLD, True)], align=PP_ALIGN.CENTER)
add_rect(s, x0 + Inches(0.5), Inches(5.55), Inches(4.1), Inches(0.6), GREEN, round_=True)
add_text(s, x0 + Inches(0.5), Inches(5.62), Inches(4.1), Inches(0.5),
         [("加权求和 → 低频修正 Δ_LF", 13, WHITE, True)], align=PP_ALIGN.CENTER)

# ============================================================
# 9. 原理4:关系摘要与门控
# ============================================================
s = add_slide()
slide_header(s, "原理四:关系摘要与门控路由 —— 何时相信低频?", "工作一 · 原理")
bullet_block(s, Inches(0.7), Inches(1.45), Inches(6.2), [
    ("关系摘要:用 4 个标量刻画高低频\u201c一致性\u201d", 15, GREEN, True),
    "•  余弦相似度、表征距离、缩放内积、平均绝对差",
    "•  直觉:高低频\u201c说法一致\u201d时修正可以更大胆;分歧大时应谨慎",
    "•  4 个标量经小型 MLP 升维后,同时喂给交互头和门控",
    ("", 8, INK, False),
    ("门控路由的两个设计细节", 15, GOLD, True),
    "•  输出 sigmoid 门控 a_LF、a_X,逐样本连续取值,而非硬开关",
    "•  末层偏置初始化为 −1.5:训练初期门控 ≈ 0.18,",
    ("    模型先学好高频基线,再逐步\u201c打开\u201d低频修正,避免早期噪声污染", 13.5, INK, False),
], size=13.5)
# 右侧:门控行为示意卡
x0 = Inches(7.4)
add_rect(s, x0, Inches(1.5), Inches(5.2), Inches(4.6), LIGHT, round_=True)
add_text(s, x0 + Inches(0.3), Inches(1.7), Inches(4.6), Inches(0.5),
         [("训练动态(监控指标)", 15, INK, True)])
rows = [("训练初期", "a_LF ≈ 0.2,几乎纯高频基线", BLUE),
        ("训练中期", "门控逐步打开,低频修正介入", PURPLE),
        ("收敛后", "a_LF 随样本分化:财报期高、平时低", GREEN),
        ("防退化监控", "组权重熵、γ/β 幅值、门控均值/方差", GOLD)]
for i, (t, d, c) in enumerate(rows):
    yy = Inches(2.35 + i * 0.92)
    add_rect(s, x0 + Inches(0.3), yy, Inches(1.55), Inches(0.7), c, round_=True)
    add_text(s, x0 + Inches(0.3), yy + Inches(0.12), Inches(1.55), Inches(0.5),
             [(t, 12, WHITE, True)], align=PP_ALIGN.CENTER)
    add_text(s, x0 + Inches(2.0), yy + Inches(0.08), Inches(3.0), Inches(0.65),
             [(d, 12, INK, False)])
add_text(s, Inches(0.7), Inches(6.6), Inches(12.0), Inches(0.6),
         [("一句话:模型不仅学\u201c低频怎么用\u201d,还学\u201c低频什么时候值得用\u201d。", 15, GREEN, True)])

# ============================================================
# 10. 回测结果:指标表
# ============================================================
s = add_slide()
slide_header(s, "回测结果:分年度绩效指标", "工作一 · 结果")
headers = ["区间", "起止", "%ret", "%ret\n(费后)", "%tvr", "Sharpe", "Sharpe\n(费后)", "IR", "IR\n(费后)", "%maxDD", "%win", "持仓数"]
data = [
    ["Total", "22/01–24/06", "50.51", "32.92", "85.68", "7.62", "4.96", "0.49", "0.32", "-2.33", "0.72", "734"],
    ["2022", "全年", "59.08", "41.27", "86.94", "9.60", "6.68", "0.62", "0.43", "-1.32", "0.71", "696"],
    ["2023", "全年", "31.01", "13.60", "84.63", "6.16", "2.71", "0.40", "0.17", "-1.37", "0.70", "767"],
    ["2024", "上半年", "73.14", "55.61", "85.24", "7.72", "5.86", "0.50", "0.38", "-2.33", "0.77", "746"],
]
n_rows, n_cols = len(data) + 1, len(headers)
tbl_shape = s.shapes.add_table(n_rows, n_cols, Inches(0.55), Inches(1.5),
                               Inches(12.25), Inches(2.6))
tbl = tbl_shape.table
tbl.columns[0].width = Inches(0.95)
tbl.columns[1].width = Inches(1.5)
for j in range(2, n_cols):
    tbl.columns[j].width = Inches(0.98)
for j, htxt in enumerate(headers):
    cell = tbl.cell(0, j)
    cell.fill.solid()
    cell.fill.fore_color.rgb = BLUE
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    tfc = cell.text_frame
    tfc.word_wrap = True
    for li, part in enumerate(htxt.split("\n")):
        p = tfc.paragraphs[0] if li == 0 else tfc.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = part
        _set_font(run, 12, WHITE, True)
for i, row in enumerate(data):
    for j, val in enumerate(row):
        cell = tbl.cell(i + 1, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = LIGHT if (i % 2 == 0) else WHITE
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = val
        _set_font(run, 12.5, INK, i == 0)
notes = [
    ("样本外回测区间 2022-01 至 2024-06,约 2.5 年,组合日均持仓约 730 只。", 14, INK, False),
    ("•  费前年化收益 50.5%,费后 32.9%;日均超额约 20.9 bps,IR 0.49", 14, INK, False),
    ("•  全区间最大回撤仅 -2.33%,日度胜率 72% —— 收益曲线平稳、回撤可控", 14, INK, False),
    ("•  三个年度费后均为正收益,2023 年市场风格切换期依然保住正收益(费后 13.6%)", 14, INK, False),
]
add_text(s, Inches(0.7), Inches(4.5), Inches(12.0), Inches(2.2), notes)

# ============================================================
# 11. 回测结果:曲线图
# ============================================================
s = add_slide()
slide_header(s, "回测结果:收益曲线与回撤", "工作一 · 结果")
tips = [
    ("累计收益曲线", "此处插入截图:\nPortfolio Cumulative Return\n(20.9 bps, IR 0.49)"),
    ("日收益 20 日移动平均", "此处插入截图:\nMoving Average of Daily Rtn"),
    ("水下曲线(回撤)", "此处插入截图:\nUnderwater Plot\n(maxDD -2.33%)"),
]
for i, (t, tip) in enumerate(tips):
    x = Inches(0.55 + i * 4.18)
    add_text(s, x, Inches(1.35), Inches(3.95), Inches(0.45),
             [(t, 15, BLUE, True)], align=PP_ALIGN.CENTER)
    add_placeholder(s, x, Inches(1.85), Inches(3.95), Inches(3.3), tip)
bullet_block(s, Inches(0.7), Inches(5.5), Inches(12.0), [
    "•  累计收益曲线斜率稳定,2024 年斜率进一步抬升 —— 低频修正在风格切换后仍然有效",
    "•  水下曲线显示回撤浅且恢复快,单次回撤基本控制在 1% 以内,最深 -2.33%",
    "•  日收益移动平均始终位于零轴上方为主,策略收益并非由个别极端交易日贡献",
], size=14)

# ============================================================
# 12. 总结与展望
# ============================================================
s = add_slide()
slide_header(s, "工作一小结", "工作一 · 总结")
add_rect(s, Inches(0.7), Inches(1.5), Inches(5.9), Inches(4.4), RGBColor(0xE8, 0xF0, 0xF9), round_=True)
add_text(s, Inches(1.0), Inches(1.7), Inches(5.3), Inches(4.0),
         [("方法贡献", 17, BLUE, True),
          ("", 6, INK, False),
          ("•  提出\u201c高频基线 + 门控残差修正\u201d的融合框架,低频信息只增益不添乱", 13.5, INK, False),
          ("•  用\u201c当前值/差分/掩码/陈旧度\u201d四元组显式建模低频因子的稀疏更新特性", 13.5, INK, False),
          ("•  分组 FiLM + 软路由,让低频的\u201c用法\u201d随市场状态自适应切换", 13.5, INK, False),
          ("•  关系摘要 + 保守初始化门控,训练稳定且行为可解释、可监控", 13.5, INK, False)])
add_rect(s, Inches(6.9), Inches(1.5), Inches(5.9), Inches(4.4), RGBColor(0xEB, 0xF2, 0xE8), round_=True)
add_text(s, Inches(7.2), Inches(1.7), Inches(5.3), Inches(4.0),
         [("结果与展望", 17, GREEN, True),
          ("", 6, INK, False),
          ("•  样本外 2.5 年:费后年化 32.9%,IR 0.49,最大回撤 -2.33%", 13.5, INK, False),
          ("•  分年度均为正收益,风格切换年份(2023)依然稳健", 13.5, INK, False),
          ("•  展望:门控行为归因分析(财报期 vs 平时)、组路由的可解释聚类、", 13.5, INK, False),
          ("    以及与更多低频数据源(分析师预期等)的接入", 13.5, INK, False)])
add_text(s, Inches(0.7), Inches(6.2), Inches(12.0), Inches(0.6),
         [("接下来汇报工作二。", 15, GREY, False)])

prs.save("工作1_高低频因子融合_答辩.pptx")
print("saved 工作1_高低频因子融合_答辩.pptx")
