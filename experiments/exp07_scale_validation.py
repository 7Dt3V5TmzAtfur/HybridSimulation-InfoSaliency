# -*- coding: utf-8 -*-
"""
实验7：规模外部效度 —— 在 N=10⁴ 上复刻防护分解（三臂对照）

动机：主实验（exp02/exp05）在 N=1000 上进行；随机消亡/随机衰减在小种群更明显，
峰值降低与分解份额是否为小种群伪象需要规模对照。

设计（见 results/RUN_MANIFEST.yml）：
- 与 exp05 完全相同的三臂设计，人口 N=10⁴（蚊群按 5:1 比例同步缩放至 5×10⁴）
- (a) 完整模型；(b) 恒定防护臂（P* 取本规模下完整臂时间平均防护）；(c) 零防护臂
- 每臂 20 次独立重复，seed = 808*1000 + i
- 与 N=1000 的对照（exp02/exp05）逐项比较

输出：
- results/exp07_scale_validation.csv
- results/exp07_per_run.csv
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
from experiments.protocol import (NUM_DAYS, NUM_INITIAL, record_manifest, set_seed)

N_RUNS = 20
POP = 10_000
MEDIA_AMPLIFICATION = 1.0


def run_full_arm() -> list:
    out = []
    for i in range(N_RUNS):
        set_seed('exp07', i)
        model = HybridEpidemicModel(
            population_size=POP,
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
    out = []
    for i in range(N_RUNS):
        set_seed('exp07', i)
        model = HybridEpidemicModel(
            population_size=POP,
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
    print(f'实验7：规模外部效度（N={POP}，三臂 × {N_RUNS}次独立重复）')
    print('=' * 70)

    full = run_full_arm()
    p_star = float(np.mean([r['time_avg_protection'] for r in full]))
    print(f'\nN={POP} 完整臂时间平均防护 P* = {p_star:.4f}')

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

    a = per_run.loc[per_run['arm_label'] == 'full_model', 'peak_infected'].to_numpy(float)
    b = per_run.loc[per_run['arm_label'] == 'constant_protection', 'peak_infected'].to_numpy(float)
    t, p = stats.ttest_ind(a, b, equal_var=False)
    marginal_pct = (b.mean() - a.mean()) / b.mean() * 100
    share = marginal_pct / agg.loc['full_model', 'peak_reduction_pct'] * 100

    print('\n=== 分解结果（N=10⁴） ===')
    for arm in ('zero_protection', 'constant_protection', 'full_model'):
        r = agg.loc[arm]
        print(f"{arm}: 峰值 {r['peak_mean']:.0f}±{r['peak_std']:.0f}（vs 零防护 {r['peak_reduction_pct']:+.1f}%），"
              f"总感染 {r['total_mean']:.0f}±{r['total_std']:.0f}（{r['total_reduction_pct']:+.1f}%）")
    print(f"\n动态反馈边际（全模型 vs 恒定防护）：峰值再降 {marginal_pct:.1f}%（Welch t={t:.2f}, p={p:.3g}），"
          f"占整体下降的 {share:.1f}%")

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    per_run.to_csv(os.path.join(out_dir, 'exp07_per_run.csv'), index=False)
    agg.reset_index().to_csv(os.path.join(out_dir, 'exp07_scale_validation.csv'), index=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    labels = ('zero_protection', 'constant_protection', 'full_model')
    vals = [agg.loc[a_, 'peak_mean'] for a_ in labels]
    errs = [agg.loc[a_, 'peak_std'] for a_ in labels]
    colors = ('#e74c3c', '#f39c12', '#2ecc71')
    ax.bar(labels, vals, yerr=errs, capsize=5, color=colors)
    ax.set_ylabel('Peak infected (mean±std)')
    ax.set_title(f'Scale validation N={POP} (n={N_RUNS}/arm, P*={p_star:.3f})')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, 'exp07_scale_validation.png'), dpi=150)
    plt.close(fig)

    record_manifest('exp07', '规模外部效度：N=10⁴ 三臂防护分解',
                    {'population': POP, 'mosquito_population': 5 * POP,
                     'days': NUM_DAYS, 'initial_infected': NUM_INITIAL,
                     'runs_per_arm': N_RUNS, 'p_star': round(p_star, 4),
                     'marginal_peak_reduction_pct': round(float(marginal_pct), 2),
                     'marginal_p_value': float(p), 'mosquito': 'on'},
                    ['exp07_scale_validation.csv', 'exp07_per_run.csv',
                     'exp07_scale_validation.png'])


if __name__ == '__main__':
    main()
