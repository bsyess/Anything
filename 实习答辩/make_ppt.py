# -*- coding: utf-8 -*-
"""
生成实习答辩 PPT(三部分工作,高换手/低换手因子)。
运行: python3 make_ppt.py
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

INK = RGBColor(0x1F, 0x1F, 0x1F)
GREY = RGBColor(0x59, 0x59, 0x59)
BLUE = RGBColor(0x2E, 0x75, 0xB6)     # 高换手
DBLUE = RGBColor(0x1F, 0x4E, 0x79)    # 数据处理
ORANGE = RGBColor(0xC5, 0x5A, 0x11)   # 低换手
PURPLE = RGBColor(0x70, 0x30, 0xA0)   # 融合/修正
GREEN = RGBColor(0x37, 0x56, 0x23)    # 输出/结论
REL = RGBColor(0x54, 0x82, 0x35)      # 关系摘要/统计量
GOLD = RGBColor(0xBF, 0x8F, 0x00)     # 门控
LIGHT = RGBColor(0xF2, 0xF4, 0xF8)
LBLUE = RGBColor(0xE8, 0xF0, 0xF9)
LORANGE = RGBColor(0xFB, 0xEE, 0xE4)
LGREEN = RGBColor(0xEB, 0xF2, 0xE8)
LPURPLE = RGBColor(0xEE, 0xE9, 0xF5)
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
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", FONT)


def add_slide():
    return prs.slides.add_slide(BLANK)


def add_rect(slide, x, y, w, h, fill, line=None, round_=False, dash=False):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if round_ else MSO_SHAPE.RECTANGLE, x, y, w, h)
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
        if dash:
            shp.line.dash_style = 4
    shp.shadow.inherit = False
    if round_:
        try:
            shp.adjustments[0] = 0.08
        except Exception:
            pass
    return shp


def add_text(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    first = True
    for item in lines:
        text, size, color, bold = item[0], item[1], item[2], item[3]
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(size * 0.45)
        run = p.add_run()
        run.text = text
        _set_font(run, size, color, bold)
    return tb


def slide_header(slide, title, tag=""):
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.14), BLUE)
    add_text(slide, Inches(0.55), Inches(0.32), Inches(10.6), Inches(0.8),
             [(title, 25, INK, True)])
    if tag:
        add_text(slide, Inches(10.4), Inches(0.42), Inches(2.55), Inches(0.5),
                 [(tag, 12, GREY, False)], align=PP_ALIGN.RIGHT)
    add_rect(slide, Inches(0.58), Inches(1.0), Inches(1.6), Pt(3), GOLD)


def bullet_block(slide, x, y, w, items, size=15):
    lines = []
    for it in items:
        if isinstance(it, tuple):
            lines.append(it)
        elif it.lstrip().startswith("•") or it.startswith("    "):
            lines.append((it, size, INK, False))
        else:
            lines.append(("•  " + it, size, INK, False))
    add_text(slide, x, y, w, Inches(4.5), lines)


def add_placeholder(slide, x, y, w, h, tip):
    shp = add_rect(slide, x, y, w, h, LIGHT, line=GREY, round_=True, dash=True)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = tip
    _set_font(run, 13, GREY, False)


RESULT_HEADERS = ["区间", "起止", "%ret", "%ret\n(费后)", "%tvr", "Sharpe",
                  "Sharpe\n(费后)", "IR", "IR\n(费后)", "%maxDD", "%win", "持仓数"]


def result_table(slide, data, x=Inches(0.55), y=Inches(1.45), w=Inches(12.25), h=Inches(2.5)):
    n_rows, n_cols = len(data) + 1, len(RESULT_HEADERS)
    tbl = slide.shapes.add_table(n_rows, n_cols, x, y, w, h).table
    tbl.columns[0].width = Inches(0.95)
    tbl.columns[1].width = Inches(1.5)
    for j in range(2, n_cols):
        tbl.columns[j].width = Inches(0.98)
    for j, htxt in enumerate(RESULT_HEADERS):
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
    return tbl


def chart_placeholder_row(slide, y_title=Inches(1.35), y_box=Inches(1.85), h_box=Inches(3.3),
                          bps="", ir="", dd=""):
    tips = [
        ("累计收益曲线", f"此处插入截图:\nPortfolio Cumulative Return\n({bps}, IR {ir})"),
        ("日收益 20 日移动平均", "此处插入截图:\nMoving Average of Daily Rtn"),
        ("水下曲线(回撤)", f"此处插入截图:\nUnderwater Plot\n(maxDD {dd})"),
    ]
    for i, (t, tip) in enumerate(tips):
        x = Inches(0.55 + i * 4.18)
        add_text(slide, x, y_title, Inches(3.95), Inches(0.45),
                 [(t, 15, BLUE, True)], align=PP_ALIGN.CENTER)
        add_placeholder(slide, x, y_box, Inches(3.95), h_box, tip)


# ======================= 数据 =======================
DATA_BASE = [
    ["Total", "22/01–24/06", "47.08", "27.16", "97.00", "6.16", "3.55", "0.40", "0.23", "-3.30", "0.67", "745"],
    ["2022", "全年", "48.16", "28.13", "97.79", "7.85", "4.56", "0.50", "0.29", "-0.92", "0.67", "725"],
    ["2023", "全年", "27.51", "7.62", "96.70", "4.19", "1.16", "0.27", "0.07", "-2.71", "0.65", "755"],
    ["2024", "上半年", "85.31", "65.56", "96.01", "7.62", "5.85", "0.49", "0.38", "-3.30", "0.69", "767"],
]
DATA_W1 = [
    ["Total", "22/01–24/06", "50.51", "32.92", "85.68", "7.62", "4.96", "0.49", "0.32", "-2.33", "0.72", "734"],
    ["2022", "全年", "59.08", "41.27", "86.94", "9.60", "6.68", "0.62", "0.43", "-1.32", "0.71", "696"],
    ["2023", "全年", "31.01", "13.60", "84.63", "6.16", "2.71", "0.40", "0.17", "-1.37", "0.70", "767"],
    ["2024", "上半年", "73.14", "55.61", "85.24", "7.72", "5.86", "0.50", "0.38", "-2.33", "0.77", "746"],
]
DATA_W2 = [
    ["Total", "22/01–24/06", "47.40", "27.67", "96.12", "7.20", "4.20", "0.46", "0.27", "-2.12", "0.70", "762"],
    ["2022", "全年", "47.96", "27.98", "97.54", "8.67", "5.05", "0.56", "0.32", "-0.94", "0.70", "736"],
    ["2023", "全年", "34.11", "15.03", "92.74", "5.97", "2.64", "0.38", "0.17", "-1.73", "0.68", "772"],
    ["2024", "上半年", "73.76", "53.16", "100.17", "7.85", "5.65", "0.50", "0.36", "-2.12", "0.73", "796"],
]
DATA_W3 = [
    ["Total", "22/01–24/06", "50.09", "32.44", "85.92", "9.06", "5.88", "0.58", "0.38", "-1.76", "0.78", "758"],
    ["2022", "全年", "53.81", "35.97", "87.06", "10.74", "7.17", "0.69", "0.46", "-1.00", "0.78", "719"],
    ["2023", "全年", "33.15", "16.28", "81.98", "9.35", "4.60", "0.60", "0.30", "-0.65", "0.77", "778"],
    ["2024", "上半年", "67.44", "58.57", "91.72", "9.00", "6.81", "0.58", "0.44", "-1.76", "0.78", "795"],
]

FIG = "figures/"

# ============================================================
# 1 封面
# ============================================================
s = add_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, WHITE)
add_rect(s, 0, 0, SLIDE_W, Inches(0.22), BLUE)
add_rect(s, 0, Inches(7.28), SLIDE_W, Inches(0.22), BLUE)
add_text(s, Inches(1.2), Inches(2.05), Inches(11.0), Inches(1.7),
         [("高换手量价模型的三步演进:", 34, INK, True),
          ("低换手因子融合 · 主干结构升级 · 行业软中性化", 30, INK, True),
          ("", 8, GREY, False)])
add_rect(s, Inches(1.25), Inches(3.85), Inches(2.2), Pt(4), GOLD)
add_text(s, Inches(1.2), Inches(4.15), Inches(11.0), Inches(1.2),
         [("实习答辩 · 三部分工作", 20, BLUE, True),
          ("汇报人:XXX        日期:2026-XX-XX        部门:XXX", 14, GREY, False)])

# ============================================================
# 2 三部分工作总览
# ============================================================
s = add_slide()
slide_header(s, "三部分工作总览:一条演进主线", "总览")
cards = [
    ("起点(上次答辩)", "MLP-Mixer + 高换手 HF380", "Sharpe 6.16 · IR 0.40\nmaxDD -3.30%", GREY),
    ("工作一", "融入低换手 alpha1298\n门控残差修正框架", "Sharpe 7.62 · IR 0.49\nmaxDD -2.33%", BLUE),
    ("工作二", "纯高换手主干升级\n因子图注意力+决策感知", "Sharpe 7.20 · IR 0.46\nmaxDD -2.12%", PURPLE),
    ("工作三", "工作2主干 × 工作1框架\n+ 行业软中性化数据", "Sharpe 9.06 · IR 0.58\nmaxDD -1.76%(初步)", GREEN),
]
for i, (t1, t2, t3, c) in enumerate(cards):
    x = Inches(0.55 + i * 3.13)
    add_rect(s, x, Inches(1.65), Inches(2.85), Inches(3.5), LIGHT, round_=True)
    add_rect(s, x, Inches(1.65), Inches(2.85), Inches(0.55), c)
    add_text(s, x, Inches(1.70), Inches(2.85), Inches(0.5),
             [(t1, 15, WHITE, True)], align=PP_ALIGN.CENTER)
    add_text(s, x + Inches(0.2), Inches(2.45), Inches(2.45), Inches(1.5),
             [(t2, 14, INK, True)])
    add_text(s, x + Inches(0.2), Inches(4.0), Inches(2.45), Inches(1.1),
             [(t3, 13, c if c != GREY else INK, True)])
    if i < 3:
        add_text(s, x + Inches(2.82), Inches(3.1), Inches(0.4), Inches(0.6),
                 [("→", 22, GREY, True)], align=PP_ALIGN.CENTER)
add_rect(s, Inches(0.55), Inches(5.55), Inches(12.25), Inches(1.45), LGREEN, round_=True)
add_text(s, Inches(0.85), Inches(5.7), Inches(11.7), Inches(1.25),
         [("统一实验设置", 15, GREEN, True),
          ("•  样本外回测 2022-01 至 2024-06;所有结果为 4 个随机种子平均(工作三当前为 2 个种子,最终版将补齐 4 个)", 13, INK, False),
          ("•  每部分的核心部件均做过消融实验逐项验证有效性后才保留", 13, INK, False)])

# ============================================================
# 3 数据背景
# ============================================================
s = add_slide()
slide_header(s, "数据背景:两类日频因子,换手节奏不同", "数据")
add_rect(s, Inches(0.7), Inches(1.4), Inches(5.9), Inches(1.95), LBLUE, round_=True)
add_text(s, Inches(0.95), Inches(1.55), Inches(5.5), Inches(1.75),
         [("高换手因子 HF380", 16, BLUE, True),
          ("•  从 994 维量价因子中筛选出 380 维(筛选方法详见上次答辩)", 13, INK, False),
          ("•  日频、逐日变化,信号强但换手高(组合换手约 97%),费损大", 13, INK, False)])
add_rect(s, Inches(0.7), Inches(3.55), Inches(5.9), Inches(1.95), LORANGE, round_=True)
add_text(s, Inches(0.95), Inches(3.7), Inches(5.5), Inches(1.75),
         [("低换手因子 alpha1298", 16, ORANGE, True),
          ("•  同为日频数据,但取值变化缓慢、大部分交易日与前一日相同", 13, INK, False),
          ("•  信号更稳、换手低,与高换手因子信息互补", 13, INK, False)])
add_rect(s, Inches(7.0), Inches(1.4), Inches(5.7), Inches(4.1), LIGHT, round_=True)
add_text(s, Inches(7.3), Inches(1.55), Inches(5.1), Inches(1.0),
         [("演进起点:上次答辩的基线", 16, INK, True),
          ("MLP-Mixer + HF380(4 seed 平均)", 13, GREY, False)])
base_rows = [("%ret / 费后", "47.08  /  27.16"),
             ("Sharpe / 费后", "6.16  /  3.55"),
             ("IR / 费后", "0.40  /  0.23"),
             ("%tvr / %maxDD", "97.00  /  -3.30"),
             ("日均超额", "19.5 bps")]
for i, (k, v) in enumerate(base_rows):
    yy = Inches(2.55 + i * 0.57)
    add_text(s, Inches(7.3), yy, Inches(2.4), Inches(0.5), [(k, 13, GREY, False)])
    add_text(s, Inches(9.8), yy, Inches(2.7), Inches(0.5), [(v, 13.5, INK, True)])
add_rect(s, Inches(0.7), Inches(5.85), Inches(12.0), Inches(1.05), LGREEN, round_=True)
add_text(s, Inches(1.0), Inches(5.98), Inches(11.4), Inches(0.85),
         [("三部分工作回答三个问题:低换手信息怎么融进来(工作一)?高换手主干还能怎么改(工作二)?两者合体 + 数据端还能做什么(工作三)?", 14.5, GREEN, True)])

# ============================================================
# 4 工作1 定位 + 核心公式
# ============================================================
s = add_slide()
slide_header(s, "工作一:融入低换手因子 —— 基线 + 门控残差修正", "工作一 · 原理")
add_text(s, Inches(0.7), Inches(1.25), Inches(12.0), Inches(0.55),
         [("动机:高换手信号强但换手 97%、费损大;低换手 alpha1298 信号稳、换手低。目标是两者互补:保住高换手信号,同时压低换手、改善费后。", 14, GREY, False)])
add_rect(s, Inches(1.5), Inches(2.0), Inches(10.3), Inches(1.15), LPURPLE, round_=True)
add_text(s, Inches(1.5), Inches(2.15), Inches(10.3), Inches(0.9),
         [("y  =  y_HF  +  a_LF · Δ_LF  +  a_X · Δ_X", 26, PURPLE, True)],
         align=PP_ALIGN.CENTER)
cards = [
    ("y_HF:高换手基线", BLUE,
     "MLP-Mixer 编码高换手序列直接出的预测,单独可用,是整个模型的\u201c保底\u201d。"),
    ("Δ_LF:低换手修正", ORANGE,
     "低换手信息经 FiLM 调制后给出的残差修正量,只负责\u201c纠偏\u201d,不重新预测。"),
    ("Δ_X:交互修正", PURPLE,
     "两路表征的乘积、差值等交互特征给出的二阶修正,捕捉两者的耦合信息。"),
    ("a_LF, a_X:门控", GOLD,
     "sigmoid 门控 ∈ (0,1),逐样本决定修正强度;初始偏向 0,从纯高换手基线温和起步。"),
]
for i, (t, c, desc) in enumerate(cards):
    x = Inches(0.7 + (i % 2) * 6.1)
    y = Inches(3.45 + (i // 2) * 1.75)
    add_rect(s, x, y, Inches(5.85), Inches(1.55), LIGHT, round_=True)
    add_rect(s, x, y, Inches(0.12), Inches(1.55), c)
    add_text(s, x + Inches(0.35), y + Inches(0.1), Inches(5.35), Inches(1.4),
             [(t, 15, c, True), (desc, 12.5, INK, False)])
add_text(s, Inches(0.7), Inches(6.95), Inches(12.0), Inches(0.45),
         [("关键性质:门控趋于 0 时退化为纯高换手基线 —— 低换手信息\u201c只能帮忙、不能捣乱\u201d。", 14, GREEN, True)])

# ============================================================
# 5 工作1 架构图
# ============================================================
s = add_slide()
slide_header(s, "工作一:模型架构总览", "工作一 · 原理")
s.shapes.add_picture(FIG + "w1_architecture.png", Inches(0.45), Inches(1.3), width=Inches(12.45))
add_text(s, Inches(0.7), Inches(6.85), Inches(12.0), Inches(0.5),
         [("两路各自编码到同一维度(160 维),再经 FiLM 调制、交互头与门控路由合成输出。", 14, GREY, False)])

# ============================================================
# 6 工作1 低换手动态编码
# ============================================================
s = add_slide()
slide_header(s, "工作一原理:低换手因子的动态编码", "工作一 · 原理")
s.shapes.add_picture(FIG + "lowturnover_dynamics.png", Inches(0.55), Inches(1.35), width=Inches(7.5))
bullet_block(s, Inches(8.3), Inches(1.5), Inches(4.4), [
    ("不喂整段序列,只喂四个动态量:", 15, ORANGE, True),
    "当前值:最新取值",
    "一阶差分:这次变化改了多少",
    "更新掩码:今天是否刚变化",
    "陈旧度 age:距上次变化多久(归一化)",
    ("", 8, INK, False),
    ("为什么有效?", 15, ORANGE, True),
    "低换手序列大部分日期取值不变,整段喂入全是冗余",
    "四元组保留了\u201c值 + 变化 + 新鲜度\u201d的全部有效信息",
    "模型可学到\u201c刚变化的信息权重高、陈旧的打折\u201d",
], size=13)

# ============================================================
# 7 工作1 分组FiLM + 门控
# ============================================================
s = add_slide()
slide_header(s, "工作一原理:分组 FiLM 调制 与 门控路由", "工作一 · 原理")
add_rect(s, Inches(0.7), Inches(1.45), Inches(6.0), Inches(1.1), LPURPLE, round_=True)
add_text(s, Inches(0.7), Inches(1.55), Inches(6.0), Inches(0.9),
         [("l̃ₖ = (1 + s·γₖ(h)) ⊙ l  +  s·βₖ(h)", 19, PURPLE, True),
          ("γ、β 由高换手表征 h 生成,对低换手表征 l 逐维缩放平移", 11.5, GREY, False)],
         align=PP_ALIGN.CENTER)
bullet_block(s, Inches(0.7), Inches(2.8), Inches(6.0), [
    ("FiLM:让高换手给低换手\u201c划重点\u201d", 15, PURPLE, True),
    "低换手信息的价值取决于当前市场状态(由高换手感知)",
    "γ 是\u201c逐维音量旋钮\u201d:放大有用维度、压低无关维度",
    "缩放系数 s=0.3 限制调制幅度,训练稳定",
    ("", 6, INK, False),
    ("分 K=3 组(软 MoE)", 15, PURPLE, True),
    "不同市场状态下低换手的\u201c用法\u201d不同,单套 γ/β 不够",
    "3 组 FiLM + 3 个残差头,softmax 路由按样本加权",
    "监控组权重熵,确认未塌缩到单一组(消融验证过分组数)",
], size=13)
bullet_block(s, Inches(7.2), Inches(1.5), Inches(5.5), [
    ("关系摘要:何时该相信低换手?", 15, REL, True),
    "余弦相似度、表征距离、缩放内积、平均绝对差,4 个标量刻画两路表征\u201c说法是否一致\u201d",
    "一致 → 修正可更大胆;分歧大 → 应谨慎",
    ("", 6, INK, False),
    ("门控的两个设计细节", 15, GOLD, True),
    "sigmoid 连续门控,逐样本取值,而非硬开关",
    "末层偏置初始化 −1.5:初始门控 ≈ 0.18,模型先学好高换手基线,再逐步\u201c打开\u201d低换手修正,避免早期噪声污染",
    ("", 6, INK, False),
    ("一句话:模型不仅学\u201c低换手怎么用\u201d,还学\u201c什么时候值得用\u201d。", 13.5, GREEN, True),
], size=13)

# ============================================================
# 8 工作1 结果表
# ============================================================
s = add_slide()
slide_header(s, "工作一结果:分年度绩效(4 seed 平均)", "工作一 · 结果")
result_table(s, DATA_W1)
add_text(s, Inches(0.7), Inches(4.35), Inches(12.0), Inches(2.4), [
    ("与基线直接对比(Total,基线数值在括号内):", 14.5, INK, True),
    ("•  换手率 85.68(基线 97.00);费后收益 32.92(基线 27.16);费后 Sharpe 4.96(基线 3.55)", 14, INK, False),
    ("•  Sharpe 7.62(基线 6.16);IR 0.49(基线 0.40);maxDD -2.33%(基线 -3.30%);日均超额 20.9 bps(基线 19.5)", 14, INK, False),
    ("•  低换手因子融入后换手下降、费后指标全面改善,且三个年度费后均为正收益", 14, INK, False),
    ("•  消融:分组数 K、关系摘要、门控初始化、动态四元组均逐项消融验证过作用", 13.5, GREEN, True),
])

# ============================================================
# 9 工作1 三图占位
# ============================================================
s = add_slide()
slide_header(s, "工作一结果:收益曲线与回撤", "工作一 · 结果")
chart_placeholder_row(s, bps="20.9 bps", ir="0.49", dd="-2.33%")
bullet_block(s, Inches(0.7), Inches(5.5), Inches(12.0), [
    "累计收益曲线斜率稳定,2024 年斜率进一步抬升",
    "水下曲线回撤浅且恢复快,最深 -2.33%",
    "日收益移动平均大部分时间位于零轴上方,收益并非由个别极端交易日贡献",
], size=14)

# ============================================================
# 10 工作2 动机定位
# ============================================================
s = add_slide()
slide_header(s, "工作二:纯高换手主干升级(不加入低换手因子)", "工作二 · 原理")
bullet_block(s, Inches(0.7), Inches(1.5), Inches(6.0), [
    ("为什么要动主干?", 16, BLUE, True),
    "基线 Mixer 的因子混合是一个固定权重 MLP:对所有样本、所有市场状态一视同仁",
    "但因子之间的关系是随市场变化的 —— 动量与流动性因子的联动在不同阶段完全不同",
    "固定混合权重表达不了\u201c因子关系本身在变\u201d这件事",
    ("", 8, INK, False),
    ("升级思路", 16, BLUE, True),
    "把每个因子看作图上的一个节点,用注意力逐样本动态计算因子间的交互 —— 相当于每天为每只票现算一张\u201c因子关系图\u201d",
    "同时在输出端加\u201c决策感知\u201d控制,让网络监控自己的内部行为",
], size=13.5)
add_rect(s, Inches(7.2), Inches(1.5), Inches(5.5), Inches(4.6), LIGHT, round_=True)
add_text(s, Inches(7.5), Inches(1.7), Inches(4.9), Inches(0.5),
         [("工作二的三个改动", 16, INK, True)])
rows = [("因子图注意力", "因子→token,线性注意力建模因子间动态关系", PURPLE),
        ("图门控", "因子末态(值/变化)调制各节点话语权", GOLD),
        ("决策感知输出端", "更新统计量驱动 Δ头 / 辅助头α门 / 幅值门", REL)]
for i, (t, d, c) in enumerate(rows):
    yy = Inches(2.45 + i * 1.15)
    add_rect(s, Inches(7.5), yy, Inches(1.85), Inches(0.9), c, round_=True)
    add_text(s, Inches(7.5), yy + Inches(0.16), Inches(1.85), Inches(0.6),
             [(t, 12.5, WHITE, True)], align=PP_ALIGN.CENTER)
    add_text(s, Inches(9.55), yy + Inches(0.05), Inches(3.0), Inches(0.85),
             [(d, 12, INK, False)])
add_text(s, Inches(0.7), Inches(6.55), Inches(12.0), Inches(0.5),
         [("统一哲学与工作一相同:所有新分支都是\u201c小初始 scale + 残差 + 保守门控\u201d,基线预测永远兜底。", 14, GREEN, True)])

# ============================================================
# 11 工作2 架构图
# ============================================================
s = add_slide()
slide_header(s, "工作二:主干架构", "工作二 · 原理")
s.shapes.add_picture(FIG + "w2_architecture.png", Inches(0.55), Inches(1.3), width=Inches(12.25))
add_text(s, Inches(0.7), Inches(6.9), Inches(12.0), Inches(0.45),
         [("时间混合沿用 MLP;因子混合升级为\u201c因子 token + 图门控 + 线性注意力\u201d;输出端由更新统计量驱动三个小修正部件。", 13.5, GREY, False)])

# ============================================================
# 12 工作2 原理细节
# ============================================================
s = add_slide()
slide_header(s, "工作二原理:因子图注意力 与 决策感知输出端", "工作二 · 原理")
bullet_block(s, Inches(0.7), Inches(1.45), Inches(6.0), [
    ("因子 token + 线性注意力", 15, PURPLE, True),
    "每个因子的窗口时序压成 16 维 token,加可学习因子 ID 嵌入 —— \u201c因子\u201d成为图上的节点",
    "注意力在 380 个节点间交互:因子关系逐样本动态生成,不再是固定权重",
    "线性注意力(ELU+1 特征映射)把复杂度从 O(C²) 降到 O(C),380 个因子才跑得动",
    ("", 6, INK, False),
    ("图门控", 15, GOLD, True),
    "用因子末态(最新值、变化量及绝对值)生成节点级缩放和偏置,tanh 限幅",
    "直觉:近期行为活跃的因子在图上话语权更高",
    "正则:整因子随机丢弃(factor dropout)+ 输出门 + 小初始 scale", 
], size=13)
bullet_block(s, Inches(7.2), Inches(1.45), Inches(5.5), [
    ("决策感知:网络监控自己的\u201c施工量\u201d", 15, REL, True),
    "每层顺便产出 6 维更新统计量:时间混合、因子混合各改动了多少(相对输入的 RMS 比值等)",
    "直觉:内部改动剧烈 ↔ 市场状态特殊,输出端应据此调整行为",
    ("", 6, INK, False),
    ("统计量驱动三个小部件", 15, GOLD, True),
    "Δ头:表征末两步差分 → 小残差修正(scale 初始 0.01)",
    "辅助头:α 门控(sigmoid,偏置 −1.5)决定是否采纳辅助预测",
    "幅值门:tanh 微调最终预测的幅度,方向不变 —— 只调\u201c下注大小\u201d",
    ("", 6, INK, False),
    ("三个部件与注意力、图门控均单独做过消融验证。", 13.5, GREEN, True),
], size=13)

# ============================================================
# 13 工作2 结果表
# ============================================================
s = add_slide()
slide_header(s, "工作二结果:分年度绩效(4 seed 平均)", "工作二 · 结果")
result_table(s, DATA_W2)
add_text(s, Inches(0.7), Inches(4.35), Inches(12.0), Inches(2.4), [
    ("与基线直接对比(Total,基线数值在括号内;两者都是纯高换手 380,输入完全相同):", 14.5, INK, True),
    ("•  Sharpe 7.20(基线 6.16);IR 0.46(基线 0.40);maxDD -2.12%(基线 -3.30%)", 14, INK, False),
    ("•  %ret 47.40(基线 47.08);费后 27.67(基线 27.16);换手 96.12(基线 97.00)", 14, INK, False),
    ("•  收益量级相当的情况下,曲线更稳:回撤更浅、Sharpe 更高 —— 主干升级主要改善的是稳定性", 14, INK, False),
    ("•  消融:线性注意力、图门控、Δ头 / 辅助头 / 幅值门均逐项消融验证过作用", 13.5, GREEN, True),
])

# ============================================================
# 14 工作2 三图占位
# ============================================================
s = add_slide()
slide_header(s, "工作二结果:收益曲线与回撤", "工作二 · 结果")
chart_placeholder_row(s, bps="19.6 bps", ir="0.46", dd="-2.12%")
bullet_block(s, Inches(0.7), Inches(5.5), Inches(12.0), [
    "与基线相比累计收益曲线形态相近,但回撤明显更浅(maxDD -2.12% vs 基线 -3.30%)",
    "2023 年(基线最难的年份)Sharpe 5.97、费后收益 15.03,较基线的 4.19、7.62 更稳",
], size=14)

# ============================================================
# 15 工作3 设计
# ============================================================
s = add_slide()
slide_header(s, "工作三:工作2 主干 × 工作1 融合框架", "工作三 · 原理")
s.shapes.add_picture(FIG + "w3_overview.png", Inches(0.55), Inches(1.35), width=Inches(12.25))
bullet_block(s, Inches(0.7), Inches(5.85), Inches(12.0), [
    "把工作1 的高换手主干整体替换为工作2 的图感知主干,低换手修正框架沿用工作1 思想",
    "两处小改进:低换手动态特征扩为五元组(增加窗口均值);修正分支对主干侧输入 detach —— 修正学习完全不干扰主干训练",
], size=13.5)

# ============================================================
# 16 工作3 行业软中性化
# ============================================================
s = add_slide()
slide_header(s, "工作三原理:数据端的行业软中性化", "工作三 · 原理")
add_rect(s, Inches(1.5), Inches(1.5), Inches(10.3), Inches(1.1), RGBColor(0xE3, 0xEA, 0xF3), round_=True)
add_text(s, Inches(1.5), Inches(1.66), Inches(10.3), Inches(0.85),
         [("soft_HF  =  raw_HF  −  λ · 行业均值", 26, DBLUE, True)],
         align=PP_ALIGN.CENTER)
bullet_block(s, Inches(0.7), Inches(2.95), Inches(6.0), [
    ("为什么要做?", 15, DBLUE, True),
    "个股因子值 = 行业共同成分 + 个股特质成分",
    "行业共同波动往往主导原始因子,个股 alpha 被行业噪声掩盖",
    "模型容易学成\u201c变相的行业轮动\u201d,回撤也集中在行业切换期",
    ("", 6, INK, False),
    ("为什么是\u201c软\u201d(λ<1)而不是完全中性化?", 15, DBLUE, True),
    "λ=1 完全减掉行业均值:行业维度的 alpha 也被一并抹掉",
    "λ=0 不处理:行业噪声主导",
    "软中性化保留少量行业暴露,在\u201c个股选择\u201d与\u201c行业信息\u201d之间取平衡",
], size=13)
add_rect(s, Inches(7.2), Inches(2.95), Inches(5.5), Inches(3.3), LIGHT, round_=True)
add_text(s, Inches(7.5), Inches(3.15), Inches(4.9), Inches(3.0),
         [("λ 的选择:实测扫描,不拍脑袋", 15, INK, True),
          ("", 6, INK, False),
          ("•  对 λ 实际测试了多组取值(0 到 1 之间)", 13.5, INK, False),
          ("•  综合收益、Sharpe、回撤等指标,实测 λ = 0.8 平衡最好", 13.5, INK, False),
          ("•  处理后得到 raw / soft 两组数据,工作三使用 soft_HF 作为主干输入", 13.5, INK, False),
          ("", 6, INK, False),
          ("(此处可补一页备用 slide:不同 λ 的指标对比表)", 12.5, GREY, False)])
add_text(s, Inches(0.7), Inches(6.6), Inches(12.0), Inches(0.5),
         [("一句话:先在数据端把\u201c行业共同噪声\u201d压下去,再让模型专注学个股层面的结构。", 14, GREEN, True)])

# ============================================================
# 17 工作3 结果表
# ============================================================
s = add_slide()
slide_header(s, "工作三结果:分年度绩效(初步,2 seed)", "工作三 · 结果")
result_table(s, DATA_W3)
add_text(s, Inches(0.7), Inches(4.35), Inches(12.0), Inches(2.4), [
    ("注:以下为 2 个种子的初步结果,其余工作均为 4 seed 平均,最终版将补齐后更新。", 13.5, ORANGE, True),
    ("•  Sharpe 9.06 · 费后 Sharpe 5.88 · IR 0.58 · 胜率 0.78,均为三部分工作中最高", 14, INK, False),
    ("•  maxDD -1.76%,为三部分工作中最浅;2023 年(最难年份)Sharpe 9.35、maxDD -0.65%", 14, INK, False),
    ("•  换手 85.92、费后收益 32.44,保持了工作一融入低换手后的换手与费后水平", 14, INK, False),
    ("•  消融:主干替换、低换手修正分支、软中性化(λ 扫描)分别验证过各自贡献", 13.5, GREEN, True),
])

# ============================================================
# 18 工作3 三图占位
# ============================================================
s = add_slide()
slide_header(s, "工作三结果:收益曲线与回撤", "工作三 · 结果")
chart_placeholder_row(s, bps="20.7 bps", ir="0.58", dd="-1.76%")
bullet_block(s, Inches(0.7), Inches(5.5), Inches(12.0), [
    "水下曲线整体明显变浅,多数回撤在 1% 以内",
    "2023 年风格切换期的深回撤在工作三中基本消失(maxDD -0.65%),软中性化 + 稳定主干共同作用",
], size=14)

# ============================================================
# 19 汇总对比
# ============================================================
s = add_slide()
slide_header(s, "三部分工作汇总(Total 区间,数值直接对比)", "总结")
sum_headers = ["模型", "%ret", "%ret\n(费后)", "%tvr", "Sharpe", "Sharpe\n(费后)", "IR", "IR\n(费后)", "%maxDD", "%win", "日均超额\n(bps)"]
sum_data = [
    ["基线(上次答辩)", "47.08", "27.16", "97.00", "6.16", "3.55", "0.40", "0.23", "-3.30", "0.67", "19.5"],
    ["工作一", "50.51", "32.92", "85.68", "7.62", "4.96", "0.49", "0.32", "-2.33", "0.72", "20.9"],
    ["工作二", "47.40", "27.67", "96.12", "7.20", "4.20", "0.46", "0.27", "-2.12", "0.70", "19.6"],
    ["工作三(初步)", "50.09", "32.44", "85.92", "9.06", "5.88", "0.58", "0.38", "-1.76", "0.78", "20.7"],
]
n_rows, n_cols = len(sum_data) + 1, len(sum_headers)
tbl = s.shapes.add_table(n_rows, n_cols, Inches(0.55), Inches(1.5), Inches(12.25), Inches(2.9)).table
tbl.columns[0].width = Inches(2.35)
for j in range(1, n_cols):
    tbl.columns[j].width = Inches(0.99)
for j, htxt in enumerate(sum_headers):
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
row_colors = [GREY, BLUE, PURPLE, GREEN]
for i, row in enumerate(sum_data):
    for j, val in enumerate(row):
        cell = tbl.cell(i + 1, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = LIGHT if (i % 2 == 0) else WHITE
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
        run = p.add_run()
        run.text = val
        _set_font(run, 12.5, row_colors[i] if j == 0 else INK, j == 0 or i == 3)
add_text(s, Inches(0.7), Inches(4.75), Inches(12.0), Inches(2.0), [
    ("•  工作一:低换手因子融入 → 换手下降、费后改善", 14.5, BLUE, False),
    ("•  工作二:主干升级 → 同等输入下曲线更稳、回撤更浅", 14.5, PURPLE, False),
    ("•  工作三:两者合体 + 行业软中性化 → Sharpe、IR、回撤、胜率全面为三者最优(2 seed 初步,待补齐)", 14.5, GREEN, False),
    ("•  所有部件均经消融实验逐项验证;基线与工作一、二为 4 seed 平均", 13.5, GREY, False),
])

# ============================================================
# 20 总结与展望
# ============================================================
s = add_slide()
slide_header(s, "总结与展望", "总结")
add_rect(s, Inches(0.7), Inches(1.5), Inches(5.9), Inches(4.5), LBLUE, round_=True)
add_text(s, Inches(1.0), Inches(1.7), Inches(5.3), Inches(4.1),
         [("方法层面的三点沉淀", 17, BLUE, True),
          ("", 6, INK, False),
          ("•  \u201c基线 + 小尺度门控残差\u201d是贯穿三部分的统一设计哲学:任何新信息、新部件都只能温和地修正基线,不能反客为主", 13.5, INK, False),
          ("•  针对数据特性做显式建模:低换手因子的\u201c值/变化/新鲜度\u201d动态编码、因子关系的逐样本注意力", 13.5, INK, False),
          ("•  数据端与模型端联动:行业软中性化(λ=0.8 实测选定)让模型专注个股 alpha", 13.5, INK, False)])
add_rect(s, Inches(6.9), Inches(1.5), Inches(5.9), Inches(4.5), LGREEN, round_=True)
add_text(s, Inches(7.2), Inches(1.7), Inches(5.3), Inches(4.1),
         [("结果与后续", 17, GREEN, True),
          ("", 6, INK, False),
          ("•  基线 → 工作三:Sharpe 6.16 → 9.06,IR 0.40 → 0.58,maxDD -3.30% → -1.76%(工作三为 2 seed 初步)", 13.5, INK, False),
          ("•  后续:补齐工作三 4 seed;λ 与其他数据处理的进一步扫描;门控与注意力行为的归因分析", 13.5, INK, False)])
add_text(s, Inches(0.7), Inches(6.3), Inches(12.0), Inches(0.6),
         [("感谢聆听,请各位老师指正。", 16, INK, True)], align=PP_ALIGN.CENTER)

prs.save("实习答辩_三部分工作.pptx")
print("saved 实习答辩_三部分工作.pptx, slides:", len(prs.slides._sldIdLst))
