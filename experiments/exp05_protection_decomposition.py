# -*- coding: utf-8 -*-
"""
实验5：防护分解 —— 恒定防护对照（分离"信息显著性动态反馈"与"静态防护水平"）

动机：实验2 的对照组是"防护=0"，其效应量度量的是"有无内生防护行为"的整体差异。
本实验加入第三臂：平均防护水平固定为 P*（实验组的时间平均防护），但不随信息动态变化。
- 若恒定防护臂复现实验组的大部分峰值下降，则"信息显著性驱动的动态反馈"的
  边际贡献 = 实验组 − 恒定防护臂；"信息显著性"单通道的边际贡献见消融 no_info_saliency。
- P* 由实验组 20 次运行的时间平均防护均值确定（内部一致性，不引入新自由参数）。

设计（见 results/RUN_MANIFEST.yml）：三臂 × 20 次独立重复，seed = 505*1000 + i。
输出：
- results/exp05_protection_decomposition.csv
- results/exp05_per_run.csv
- results/exp05_decomposition.png
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src.hybrid_model import HybridEpidemicModel
from experiments.protocol import (NUM_DAYS, NUM_INITIAL, POPULATION_SIZE,
                                  record_manifest, set_seed)

N_RUNS = 20
MEDIA_AMPLIFICATION = 1.0


def run_full_arm() -> list:
    """完整模型臂；同时返回时间平均防护（用于确定 P*）。"""
    out = []
    for i in range(N_RUNS):
        set_seed('exp05', i)
        model = HybridEpidemicModel(
            population_size=POPULATION_SIZE,
            media_amplification=MEDIA_AMPLIFICATION,
            enable_info_behavior_feedback=True,
            enable_mosquito_transmission=True,
        )
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        df = model.get_results()
        out.append({
            'arm': 'full', 'run': i, 'protection_level': np.nan,
            'peak_infected': int(df['I'].max()),
            'total_infected': int(df['R'].iloc[-1]),
            'time_avg_protection': float(df['avg_protection'].mean()),
        })
    return out


def run_fixed_arm(protection_override: float) -> list:
    """恒定防护臂：行为不更新，平均防护固定为 protection_override。"""
    out = []
    for i in range(N_RUNS):
        set_seed('exp05', i)
        model = HybridEpidemicModel(
            population_size=POPULATION_SIZE,
            media_amplification=MEDIA_AMPLIFICATION,
            enable_info_behavior_feedback=False,
            enable_mosquito_transmission=True,
            protection_override=protection_override,
        )
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        df = model.get_results()
        out.append({
            'arm': 'fixed', 'run': i, 'protection_level': protection_override,
            'peak_infected': int(df['I'].max()),
            'total_infected': int(df['R'].iloc[-1]),
            'time_avg_protection': protection_override,
        })
    return out


def main():
    print('=' * 70)
    print(f'实验5：防护分解（三臂 × {N_RUNS}次独立重复）')
    print('=' * 70)

    full = run_full_arm()
    p_star = float(np.mean([r['time_avg_protection'] for r in full]))
    print(f'\n实验组时间平均防护 P* = {p_star:.4f} → 恒定防护臂取 P = {p_star:.4f}')

    records = full + run_fixed_arm(p_star) + run_fixed_arm(0.0)
    per_run = pd.DataFrame(records)
    per_run['arm_label'] = per_run.apply(
        lambda r: 'full_model' if r['arm'] == 'full'
        else ('constant_protection' if r['protection_level'] > 0 else 'zero_protection'), axis=1)

    agg = per_run.groupby('arm_label').agg(
        peak_mean=('peak_infected', 'mean'), peak_std=('peak_infected', 'std'),
        total_mean=('total_infected', 'mean'), total_std=('total_infected', 'std'),
        protection=('protection_level', 'first'),
    )
    z = agg.loc['zero_protection']
    for arm in ('full_model', 'constant_protection'):
        agg.loc[arm, 'peak_reduction_pct'] = (z['peak_mean'] - agg.loc[arm, 'peak_mean']) / z['peak_mean'] * 100
        agg.loc[arm, 'total_reduction_pct'] = (z['total_mean'] - agg.loc[arm, 'total_mean']) / z['total_mean'] * 100
    agg.loc['zero_protection', 'peak_reduction_pct'] = 0.0
    agg.loc['zero_protection', 'total_reduction_pct'] = 0.0

    # 全模型 vs 恒定防护：动态反馈的边际贡献（Welch t）
    a = per_run.loc[per_run['arm_label'] == 'full_model', 'peak_infected'].to_numpy(float)
    b = per_run.loc[per_run['arm_label'] == 'constant_protection', 'peak_infected'].to_numpy(float)
    t, p = stats.ttest_ind(a, b, equal_var=False)
    marginal_pct = (b.mean() - a.mean()) / b.mean() * 100

    print('\n=== 分解结果 ===')
    for arm in ('zero_protection', 'constant_protection', 'full_model'):
        r = agg.loc[arm]
        print(f"{arm}: 峰值 {r['peak_mean']:.1f}±{r['peak_std']:.1f}（vs 零防护 {r['peak_reduction_pct']:+.1f}%），"
              f"总感染 {r['total_mean']:.1f}±{r['total_std']:.1f}")
    print(f"\n动态信息-行为反馈的边际贡献（全模型 vs 恒定防护）：峰值再降 {marginal_pct:.1f}%（Welch t={t:.2f}, p={p:.3g}）")
    share = marginal_pct / agg.loc['full_model', 'peak_reduction_pct'] * 100
    print(f"占整体峰值下降（{agg.loc['full_model','peak_reduction_pct']:.1f}%）的份额：{share:.1f}%")

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    per_run.to_csv(os.path.join(out_dir, 'exp05_per_run.csv'), index=False)
    agg.reset_index().to_csv(os.path.join(out_dir, 'exp05_protection_decomposition.csv'), index=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    labels = ('zero_protection', 'constant_protection', 'full_model')
    vals = [agg.loc[a, 'peak_mean'] for a in labels]
    errs = [agg.loc[a, 'peak_std'] for a in labels]
    colors = ('#e74c3c', '#f39c12', '#2ecc71')
    ax.bar(labels, vals, yerr=errs, capsize=5, color=colors)
    ax.set_ylabel('Peak infected (mean±std)')
    ax.set_title(f'Protection decomposition (n={N_RUNS}/arm, P*={p_star:.3f})')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, 'exp05_decomposition.png'), dpi=150)
    plt.close(fig)

    record_manifest('exp05', '防护分解：全模型 vs 恒定防护 vs 零防护',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'runs_per_arm': N_RUNS,
                     'p_star': round(p_star, 4),
                     'marginal_peak_reduction_pct': round(float(marginal_pct), 2),
                     'marginal_p_value': float(p), 'mosquito': 'on'},
                    ['exp05_protection_decomposition.csv', 'exp05_per_run.csv',
                     'exp05_decomposition.png'])


if __name__ == '__main__':
    main()
