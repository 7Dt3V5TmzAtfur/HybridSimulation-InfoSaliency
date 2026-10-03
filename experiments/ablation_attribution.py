# -*- coding: utf-8 -*-
"""
归因审计（Ablation-Attribution Analysis）—— 单一运行集、配对种子、n≥10

设计（见 results/RUN_MANIFEST.yml）：
- 条件：baseline / no_info_saliency / no_behavior_feedback /
        no_hospital_constraint / no_mosquito（5 条件 × 10 次配对重复）
- 配对种子：所有条件使用相同种子集（seed = 707*1000 + i），差异 partly 来自
  组件移除、partly 来自随机流分叉——故报告均值±标准差，不做单次运行归因。
- 床位 50 / ICU 10（使资源约束实际生效；默认 200 床下约束几乎不触发）
- 归因约定（全文唯一口径）：变化% = (消融均值 − 基线均值) / 基线均值 × 100，
  **正值 = 移除该组件后指标上升**（该组件在完整模型中起抑制作用）。
- 已知局限：住院资源在当前模型中不反馈传播动力学（入院不隔离），故
  no_hospital_constraint 对峰值感染的影响应接近随机噪声——本实验将显式检验这一点。

输出：
- results/ablation_per_run.csv        每次运行原始指标
- results/ablation_summary.csv        各条件均值±标准差
- results/ablation_attribution.csv    归因（变化%，含上述口径）
- results/ablation_attribution_report.md
- results/ablation_attribution.png
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.hybrid_model import DESParams, HybridEpidemicModel
from experiments.protocol import (NUM_DAYS, NUM_INITIAL, POPULATION_SIZE,
                                  record_manifest, set_seed)

N_RUNS = 10
MEDIA_AMPLIFICATION = 1.0  # 与主实验统一（α=1.0；α 维度由实验3覆盖）

CONDITIONS = {
    'baseline': {},
    'no_info_saliency': {'disable_info_saliency': True},
    'no_behavior_feedback': {'disable_behavior_feedback': True},
    'no_hospital_constraint': {'disable_hospital_constraint': True},
    'no_mosquito': {'disable_mosquito': True},
    'no_human_transmission': {'disable_human_transmission': True},
}

METRICS = ['peak_infected', 'peak_day', 'total_infected', 'peak_protection', 'deferred_admissions']


def run_condition(config: dict, run_index: int) -> dict:
    set_seed('ablation', run_index)
    model = HybridEpidemicModel(
        population_size=POPULATION_SIZE,
        des_params=DESParams(hospital_beds=50, icu_beds=10, testing_capacity=100,
                             avg_hospital_stay=7, avg_icu_stay=14, test_result_time=1),
        media_amplification=MEDIA_AMPLIFICATION,
        enable_info_behavior_feedback=True,
        enable_mosquito_transmission=True,
    )

    if config.get('disable_info_saliency'):
        model.info_model.media_amplification = 0.0
    if config.get('disable_behavior_feedback'):
        model.enable_info_behavior_feedback = False
    if config.get('disable_hospital_constraint'):
        model.hospital.params.hospital_beds = 1_000_000
        model.hospital.params.icu_beds = 1_000_000
    if config.get('disable_mosquito'):
        model.enable_mosquito_transmission = False
    if config.get('disable_human_transmission'):
        model.enable_human_transmission = False

    model.seed_infection(num_initial=NUM_INITIAL)
    model.run(num_days=NUM_DAYS)
    df = model.get_results()
    peak = int(df['I'].max())
    return {
        'peak_infected': peak,
        'peak_day': int(df['I'].idxmax()),
        'total_infected': int(df['R'].iloc[-1]),
        'peak_protection': float(df['avg_protection'].max()),
        'deferred_admissions': int(df['deferred_admissions'].iloc[-1]),
    }


def main():
    print('=' * 70)
    print(f'归因审计（{len(CONDITIONS)}条件 × {N_RUNS}次配对重复，床位50/ICU10）')
    print('=' * 70)

    rows = []
    for cond, config in CONDITIONS.items():
        print(f'[{cond}] 运行 {N_RUNS} 次...')
        for i in range(N_RUNS):
            r = run_condition(config, i)
            r['condition'] = cond
            r['run'] = i
            rows.append(r)
    per_run = pd.DataFrame(rows)

    summary = per_run.groupby('condition')[METRICS].agg(['mean', 'std'])
    summary.columns = ['_'.join(c) for c in summary.columns]

    base = summary.loc['baseline']
    attrib = pd.DataFrame(index=list(CONDITIONS.keys()),
                          columns=[m + '_change_pct' for m in METRICS], dtype=float)
    for cond in CONDITIONS:
        for m in METRICS:
            if cond == 'baseline':
                attrib.loc[cond, m + '_change_pct'] = 0.0
            else:
                b = base[m + '_mean']
                v = summary.loc[cond, m + '_mean']
                attrib.loc[cond, m + '_change_pct'] = (v - b) / b * 100 if b != 0 else np.nan

    print('\n=== 各条件均值±标准差 ===')
    for cond in CONDITIONS:
        r = summary.loc[cond]
        print(f"{cond}: 峰值 {r['peak_infected_mean']:.1f}±{r['peak_infected_std']:.1f}，"
              f"总感染 {r['total_infected_mean']:.1f}±{r['total_infected_std']:.1f}，"
              f"峰值防护 {r['peak_protection_mean']:.3f}，延后入院 {r['deferred_admissions_mean']:.0f}")

    print('\n=== 归因（变化% = (消融均值−基线均值)/基线均值×100；正值=移除后指标上升） ===')
    print(attrib.round(1).to_string())

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    per_run.to_csv(os.path.join(out_dir, 'ablation_per_run.csv'), index=False)
    summary.to_csv(os.path.join(out_dir, 'ablation_summary.csv'))
    attrib.to_csv(os.path.join(out_dir, 'ablation_attribution.csv'))

    # 报告
    cond_desc = {'baseline': '完整模型',
                 'no_info_saliency': '禁用信息显著性（media_amplification=0）',
                 'no_behavior_feedback': '禁用信息-行为反馈（防护=0）',
                 'no_hospital_constraint': '移除医疗资源约束（床位/ICU≈无限）',
                 'no_mosquito': '禁用蚊媒传播通道',
                 'no_human_transmission': '禁用人-人传播通道（仅蚊媒）'}
    lines = []
    lines.append('# 归因审计报告（Ablation-Attribution Report）')
    lines.append('')
    lines.append('## 实验配置')
    lines.append('')
    lines.append(f'- 人口数量: {POPULATION_SIZE}，仿真天数: {NUM_DAYS}，初始感染: {NUM_INITIAL}')
    lines.append(f'- 重复次数: 每条件 {N_RUNS} 次（配对种子，seed = 707*1000 + i）')
    lines.append('- 床位 50 / ICU 10（收紧以使资源约束生效；默认 200 床下约束几乎不触发）')
    lines.append(f'- media_amplification = {MEDIA_AMPLIFICATION}')
    lines.append('')
    lines.append('## 消融条件')
    lines.append('')
    for cond, config in CONDITIONS.items():
        lines.append(f'- **{cond}**: {cond_desc[cond]}')
    lines.append('')
    lines.append('## 各条件结果（均值±标准差）')
    lines.append('')
    lines.append('| 条件 | 峰值感染 | 峰值日 | 总感染 | 峰值防护 | 延后入院 |')
    lines.append('|------|---------|--------|--------|---------|---------|')
    for cond in CONDITIONS:
        r = summary.loc[cond]
        lines.append(f"| {cond} | {r['peak_infected_mean']:.1f}±{r['peak_infected_std']:.1f} | "
                     f"{r['peak_day_mean']:.0f}±{r['peak_day_std']:.0f} | "
                     f"{r['total_infected_mean']:.1f}±{r['total_infected_std']:.1f} | "
                     f"{r['peak_protection_mean']:.3f} | {r['deferred_admissions_mean']:.1f}±{r['deferred_admissions_std']:.1f} |")
    lines.append('')
    lines.append('## 归因（变化%）')
    lines.append('')
    lines.append('**口径（全文唯一）**：变化% = (消融均值 − 基线均值) / 基线均值 × 100；')
    lines.append('**正值 = 移除该组件后指标上升**（该组件在完整模型中起抑制作用）。')
    lines.append('')
    lines.append('| 条件 | 峰值感染 | 总感染 | 峰值防护 | 延后入院 |')
    lines.append('|------|---------|--------|---------|---------|')
    for cond in CONDITIONS:
        row = attrib.loc[cond]
        lines.append(f"| {cond} | {row['peak_infected_change_pct']:.1f} | "
                     f"{row['total_infected_change_pct']:.1f} | "
                     f"{row['peak_protection_change_pct']:.1f} | "
                     f"{row['deferred_admissions_change_pct']:.1f} |")
    lines.append('')
    lines.append('## 注意事项')
    lines.append('')
    lines.append('1. 住院资源在当前模型中**不反馈传播动力学**（入院不隔离传染源），因此')
    lines.append('   no_hospital_constraint 对峰值感染的"贡献"应理解为配对随机流下的噪声水平，')
    lines.append('   其真实影响体现在"延后入院"指标上。传播学耦合（住院隔离）列为未来工作。')
    lines.append('2. 配对种子下，不同条件消耗随机数序列不同，个体层面的差异含有随机成分；')
    lines.append('   请以均值±标准差解读，勿以单次运行差异归因。')
    lines.append('')
    with open(os.path.join(out_dir, 'ablation_attribution_report.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # 可视化
    conds = list(CONDITIONS.keys())
    means = [summary.loc[c, 'peak_infected_mean'] for c in conds]
    stds = [summary.loc[c, 'peak_infected_std'] for c in conds]
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#2ecc71' if c == 'baseline' else '#e74c3c' for c in conds]
    ax.bar(conds, means, yerr=stds, capsize=4, color=colors)
    ax.set_ylabel('Peak infected (mean±std)')
    ax.set_title(f'Ablation (n={N_RUNS}/condition, paired seeds)')
    ax.tick_params(axis='x', rotation=30)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, 'ablation_attribution.png'), dpi=150)
    plt.close(fig)

    record_manifest('ablation', '消融归因审计（5条件×10配对重复）',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'runs_per_condition': N_RUNS,
                     'conditions': str(list(CONDITIONS.keys())),
                     'hospital_beds': 50, 'icu_beds': 10,
                     'media_amplification': MEDIA_AMPLIFICATION,
                     'attribution_convention': '(ablated_mean - baseline_mean)/baseline_mean*100; positive = rises when removed',
                     'protection_efficiency': 0.85},
                    ['ablation_per_run.csv', 'ablation_summary.csv', 'ablation_attribution.csv',
                     'ablation_attribution_report.md', 'ablation_attribution.png'])


if __name__ == '__main__':
    main()
