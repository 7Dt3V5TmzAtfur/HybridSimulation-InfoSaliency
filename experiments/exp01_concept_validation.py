# -*- coding: utf-8 -*-
"""
实验1：概念验证 —— 信息-行为反馈机制的存在性

设计（见 results/RUN_MANIFEST.yml）：
- 实验组：完整信息-行为反馈（蚊媒开）
- 对照组：禁用信息-行为反馈（防护=0，蚊媒开）
- 20 次独立重复（seed = 101*1000 + i），初始感染 10 人，media_amplification=1.0
输出：
- results/exp01_summary.csv           两组指标的均值±标准差
- results/exp01_per_run.csv           每次运行的原始指标（可审计）
- results/exp01_concept_validation.png 单次代表性轨迹对比
- results/exp01_comparison.png        聚合分布对比
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.hybrid_model import HybridEpidemicModel
from experiments.protocol import (BASE_SEED, NUM_DAYS, NUM_INITIAL,
                                  POPULATION_SIZE, record_manifest, set_seed)

N_RUNS = 20
MEDIA_AMPLIFICATION = 1.0


def make_model(feedback: bool) -> HybridEpidemicModel:
    return HybridEpidemicModel(
        population_size=POPULATION_SIZE,
        media_amplification=MEDIA_AMPLIFICATION,
        enable_info_behavior_feedback=feedback,
        enable_mosquito_transmission=True,
    )


def run_once(feedback: bool, run_index: int) -> dict:
    set_seed('exp01', run_index)
    model = make_model(feedback)
    model.seed_infection(num_initial=NUM_INITIAL)
    model.run(num_days=NUM_DAYS)
    df = model.get_results()
    peak = int(df['I'].max())
    return {
        'run': run_index,
        'peak_infected': peak,
        'peak_day': int(df['I'].idxmax()),
        'total_infected': int(df['R'].iloc[-1]),
    }


def main():
    print('=' * 70)
    print(f'实验1：概念验证（N={POPULATION_SIZE}, {NUM_DAYS}天, 初始感染={NUM_INITIAL}, '
          f'α={MEDIA_AMPLIFICATION}, 每组{N_RUNS}次独立重复）')
    print('=' * 70)

    rows = []
    for arm, feedback in (('with_feedback', True), ('without_feedback', False)):
        print(f'[{arm}] 运行 {N_RUNS} 次...')
        for i in range(N_RUNS):
            r = run_once(feedback, i)
            r['arm'] = arm
            rows.append(r)
    per_run = pd.DataFrame(rows)

    summary = per_run.groupby('arm').agg(
        peak_mean=('peak_infected', 'mean'), peak_std=('peak_infected', 'std'),
        peak_day_mean=('peak_day', 'mean'), peak_day_std=('peak_day', 'std'),
        total_mean=('total_infected', 'mean'), total_std=('total_infected', 'std'),
    )
    fb = summary.loc['with_feedback']
    nofb = summary.loc['without_feedback']
    summary['peak_reduction_pct'] = np.nan
    summary.loc['with_feedback', 'peak_reduction_pct'] = (
        (nofb['peak_mean'] - fb['peak_mean']) / nofb['peak_mean'] * 100)
    summary['total_reduction_pct'] = np.nan
    summary.loc['with_feedback', 'total_reduction_pct'] = (
        (nofb['total_mean'] - fb['total_mean']) / nofb['total_mean'] * 100)

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    os.makedirs(out_dir, exist_ok=True)
    per_run.to_csv(os.path.join(out_dir, 'exp01_per_run.csv'), index=False)
    summary.to_csv(os.path.join(out_dir, 'exp01_summary.csv'))

    print('\n=== 汇总（均值±标准差） ===')
    for arm in ('with_feedback', 'without_feedback'):
        r = summary.loc[arm]
        print(f"{arm}: 峰值 {r['peak_mean']:.1f}±{r['peak_std']:.1f}（第{r['peak_day_mean']:.0f}±{r['peak_day_std']:.0f}天），"
              f"总感染 {r['total_mean']:.1f}±{r['total_std']:.1f}")
    print(f"实验组相对对照组：峰值降低 {summary.loc['with_feedback','peak_reduction_pct']:.1f}%，"
          f"总感染降低 {summary.loc['with_feedback','total_reduction_pct']:.1f}%")

    # 代表性单次轨迹（run 0，两组同种子）
    trajs = {}
    for arm, feedback in (('with_feedback', True), ('without_feedback', False)):
        set_seed('exp01', 0)
        model = make_model(feedback)
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        trajs[arm] = model.get_results()

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    ax = axes[0]
    ax.plot(trajs['with_feedback']['I'], label='With info-behavior feedback', color='#2ecc71')
    ax.plot(trajs['without_feedback']['I'], label='Without (protection=0)', color='#e74c3c', alpha=0.8)
    ax.set_ylabel('Infected (I)'); ax.legend(); ax.grid(alpha=0.3)
    ax.set_title(f'Concept validation: single run (seed={BASE_SEED["exp01"]*1000})')
    ax = axes[1]
    ax.plot(trajs['with_feedback']['avg_protection'], label='Avg protection', color='#2980b9')
    ax.plot(trajs['with_feedback']['info_saliency'], label='Info saliency', color='#8e44ad')
    ax.set_ylabel('Level [0,1]'); ax.set_xlabel('Day'); ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, 'exp01_concept_validation.png'), dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, metric, label in ((axes[0], 'peak_infected', 'Peak infected'),
                              (axes[1], 'total_infected', 'Total infected')):
        data = [per_run.loc[per_run['arm'] == a, metric] for a in ('with_feedback', 'without_feedback')]
        ax.boxplot(data, tick_labels=['feedback', 'no feedback'])
        ax.set_ylabel(label); ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, 'exp01_comparison.png'), dpi=150)
    plt.close(fig)

    record_manifest('exp01', '概念验证：信息-行为反馈开/关对比',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'media_amplification': MEDIA_AMPLIFICATION,
                     'runs_per_arm': N_RUNS, 'mosquito': 'on',
                     'protection_efficiency': 0.85},
                    ['exp01_summary.csv', 'exp01_per_run.csv',
                     'exp01_concept_validation.png', 'exp01_comparison.png'])


if __name__ == '__main__':
    main()
