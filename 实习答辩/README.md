# 实习答辩材料(三部分工作)

主线:高换手量价模型的三步演进 —— 低换手因子融合(工作一)、主干结构升级(工作二)、合体 + 行业软中性化(工作三)。
注意术语:高换手 / 低换手因子,均为日频数据。

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `实习答辩_三部分工作.pptx` | 答辩 PPT(20 页,16:9),原理讲解 + 结果展示 |
| `答辩讲稿.md` | 逐页讲稿 + Q&A 准备清单 |
| `make_ppt.py` | PPT 生成脚本(含全部表格数值,可改后重新生成) |
| `figures/draw_figures.py` | 四张示意图绘制脚本 |
| `figures/w1_architecture.png` | 工作一架构图(PPT 第 5 页) |
| `figures/lowturnover_dynamics.png` | 低换手因子动态特征示意(第 6 页) |
| `figures/w2_architecture.png` | 工作二主干架构图(第 11 页) |
| `figures/w3_overview.png` | 工作三组合示意图(第 15 页) |
| `code/model_work1.py` | 工作一模型(已去 industry / pool) |
| `code/model_work2_backbone.py` | 工作二主干(已去 industry / pool) |
| `code/model_work3_fusion.py` | 工作三融合模型(已去 industry / pool) |

## 答辩前待办

1. 封面替换汇报人 / 日期 / 部门;
2. 第 9、14、18 页的虚线占位框中插入三组回测截图(累计收益 / 日收益移动平均 / 水下曲线);
3. 工作三补齐 4 seed 后,更新第 17、19 页表格数值(在 `make_ppt.py` 的 `DATA_W3` 与 `sum_data` 中修改后重跑);
4. 建议准备附录备用 slide:各部分关键消融数值表、不同 λ 的指标对比表;
5. 核对第 17 页工作三表格数值(截图分辨率有限,个别数字请对照原始结果确认)。

## 重新生成

```bash
pip install python-pptx matplotlib
cd figures && python3 draw_figures.py && cd ..
python3 make_ppt.py
```
