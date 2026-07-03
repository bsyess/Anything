# 工作一:高低频因子融合模型 —— 答辩材料

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `工作1_高低频因子融合_答辩.pptx` | 答辩 PPT(12 页,16:9),原理推导 + 结果展示 |
| `答辩讲稿_工作1.md` | 每页讲稿 + Q&A 准备清单 |
| `model_work1.py` | 去掉 industry / pool 部分后的核心模型代码 |
| `architecture.png` | 模型架构示意图(PPT 第 5 页) |
| `lf_dynamics.png` | 低频因子动态特征示意图(PPT 第 7 页) |
| `make_ppt.py` | PPT 生成脚本,可修改后重新生成 |
| `draw_architecture.py` / `draw_lf_dynamics.py` | 两张示意图的绘制脚本 |

## 待办(答辩前请完成)

1. 封面页替换汇报人 / 日期 / 部门;
2. 第 2 页替换工作二、工作三的标题与一句话简介;
3. 第 11 页三个虚线占位框中插入自己的回测截图(累计收益 / 日收益移动平均 / 水下曲线);
4. 如有消融实验数据,建议按讲稿 Q&A 第 1 条补一页备用 slide。

## 重新生成

```bash
pip install python-pptx matplotlib
python3 draw_architecture.py
python3 draw_lf_dynamics.py
python3 make_ppt.py
```
