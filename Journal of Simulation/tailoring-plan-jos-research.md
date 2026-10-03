# Tailoring Plan — Journal of Simulation (Research Article)

日期：2026-10-03 ｜ 源稿：`docs/paper_main.md` v2.1（中文）｜ 目标：JOS Research Article（英文，Interact 模板，Style P）

## 1. 核验记录

- 事实来源：用户提供的离线 Instructions for Authors（`Journal of Simulation/Submit your article to Journal of Simulation.md`，官方页面存档，更新于 2026-09-14）。此前（2026-10-03）已对期刊范围做过在线核验（与离线版一致：仿真方法学社区）。
- **关键要求**：仅英文；**双匿名评审**；正文 ≤10,000 词（含图表位，不含参考文献/附录），需附词数；摘要非结构化 ≤200 词；关键词 3–6；结构 = 标题页/摘要/关键词/正文（Intro–Methods–Results–Discussion）/致谢/利益声明/**生成式 AI 使用声明**/数据可用性/参考文献/附录；LaTeX 提交必须附 `.bib`；图线上版 1200 dpi、彩图 300 dpi（评审阶段"足够分辨率"即可，录用后生产阶段需重出高分辨率）；无投稿费/版面费。
- 模板：`interact.cls` v1.01 + `tfp.bst`（数字括号引用，natbib numbers 模式）——以模板样例前言为准。
- 矛盾：无。离线说明与既有核验一致。

## 2. 去实验报告化（重构方案）

源稿病灶（用户指出 + 复核确认）：
1. Introduction 是"研究背景/关键挑战/核心洞察/空白/目标/贡献"的实验报告脚手架；
2. 正文按"实验 1–8"顺序罗列，标题即 `实验N：XXX`，穿插 `results/expXX.csv` 文件路径、`RUN_MANIFEST`、`✅/⚠️/❌` 表格语言、"✅ GO"等内部管理语言；
3. 中文稿。

重构决策：
- **按研究问题组织结果**，不按实验编号：RQ1 行为反馈开关效应 → RQ2 水平 vs 动态分解（含规模复核）→ RQ3 机制对照 → RQ4 媒体放大阈值 → RQ5 真实数据校准与跨季外推 → RQ6 组件消融。
- 实验编号只保留在内部（`exp01–exp08`），正文称 "the switch comparison / decomposition experiment / mechanism control / ..."。
- 所有结果文件路径移出正文（进数据可用性声明与附录 A：再生协议）。
- Introduction 重写为叙事式：负担 → 行为的重要性与 awareness 文献 → 混合仿真缺口 → "评估缺口"（效应混淆）→ 本文问题与贡献。
- 统计口径、种子协议、消融符号约定压缩进 Methods 一节与附录。
- 所有数字与 `results/*.csv` 一致（由 `scripts/verify_consistency.py` 机械核对，本次将 .tex 纳入核对范围）。

## 3. 标题与摘要（提案）

- **Title**: Protection level or behavioural dynamics? An effect-decomposition study of an information-saliency-driven hybrid simulation framework for dengue
- **Abstract**: ≤200 词，非结构化（见 manuscript.tex；数字与 CSV 一致）
- **Keywords**: hybrid simulation; agent-based modelling; dengue; behavioural epidemiology; model validation; effect decomposition

## 4. 双匿名与声明

- 作者块匿名化（双匿名）；真实作者块以注释保存在 tex 中待录用还原。
- 自我指涉清零：代码"available from the corresponding author"；数据 = OpenDengue 公共数据（引用 OpenDengue 2024）。
- 四项声明：Funding（无——**需作者确认**）、Declaration of interest（无——需确认）、**Generative AI declaration**（按实际情况起草：AI 用于代码开发、实验执行与稿件起草——**需作者按 T&F 政策确认措辞与范围**）、Data availability（OpenDengue 公共 + 代码按上）。
- Acknowledgements：留空占位（匿名版省略）。

## 5. 图表与词数预算

- 图 4 幅：F1 框架图（新生成）、F2 开关对比轨迹（300 dpi 重生成）、F3 分解对比（N=1000 vs N=10⁴ 双面板）、F4 校准拟合。均由 CSV 重生成，生产阶段再按 T&F 分辨率要求重出。
- 表 6 张：主结果、分解（两规模）、机制对照、α 敏感性、校准与外推、消融。
- 词数目标：正文 ≈ 7,800 词 + 图表 ≈ 1,500 词当量 < 10,000。

## 6. 执行清单

1. `scripts/make_submission_figures.py` 生成 4 图（300 dpi 英文标签）
2. `submission/refs.bib`（25 条，全部经前期核验）
3. `submission/manuscript.tex`（Interact + tfp，双匿名）
4. 编译验证 + 词数统计 + verify_consistency.py 扩展纳入 .tex
