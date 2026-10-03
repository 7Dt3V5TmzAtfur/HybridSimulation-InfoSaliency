# -*- coding: utf-8 -*-
"""
实验2：信息-行为反馈效应的定量对比（统计检验）

设计（见 results/RUN_MANIFEST.yml）：
- 实验组：完整信息-行为耦合（蚊媒开）
- 对照组：禁用信息-行为反馈（防护=0，蚊媒开）—— 注意：该对照隔离的是
  "内生防护行为"整体，而非"信息显著性"单通道；单通道贡献见实验5分解。
- 20 次独立重复（seed = 202*1000 + i），初始感染 10 人，media_amplification=1.0
- 统计：Welch t 检验（不假设方差齐性）、Cohen's d（合并标准差）及 95% CI（bootstrap）
输出：
- results/exp02_statistics.csv   两组统计检验结果
- results/exp02_per_run.csv      每次运行原始指标
- results/exp02_info_effect.png  均值轨迹±标准带
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
RNG = np.random.default_rng(20261003)  # 仅用于 bootstrap，与仿真种子分离


def run_arm(feedback: bool) -> list:
    out = []
    for i in range(N_RUNS):
        set_seed('exp02', i)
        model = HybridEpidemicModel(
            population_size=POPULATION_SIZE,
            media_amplification=MEDIA_AMPLIFICATION,
            enable_info_behavior_feedback=feedback,
            enable_mosquito_transmission=True,
        )
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        df = model.get_results()
        out.append({
            'run': i, 'arm': 'feedback' if feedback else 'control',
            'peak_infected': int(df['I'].max()),
            'peak_day': int(df['I'].idxmax()),
            'total_infected': int(df['R'].iloc[-1]),
            'time_avg_protection': float(df['avg_protection'].mean()),
            'max_protection': float(df['avg_protection'].max()),
        })
    return out


def cohens_d(a, b):
    """Cohen's d（合并标准差），及 bootstrap 95% CI。"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    na, nb = len(a), len(b)
    pooled = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    d = (a.mean() - b.mean()) / pooled
    boots = []
    combined_size = (na, nb)
    for _ in range(2000):
        ra = RNG.choice(a, size=na, replace=True)
        rb = RNG.choice(b, size=nb, replace=True)
        p2 = np.sqrt(((na - 1) * ra.var(ddof=1) + (nb - 1) * rb.var(ddof=1)) / (na + nb - 2))
        boots.append((ra.mean() - rb.mean()) / p2)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return d, lo, hi


def main():
    print('=' * 70)
    print(f'实验2：信息-行为反馈定量对比（每组{N_RUNS}次独立重复，Welch t 检验）')
    print('=' * 70)

    records = run_arm(True) + run_arm(False)
    per_run = pd.DataFrame(records)
    exp = per_run[per_run['arm'] == 'feedback']
    ctrl = per_run[per_run['arm'] == 'control']

    rows = []
    for metric in ('peak_infected', 'total_infected'):
        a = exp[metric].to_numpy(float)
        b = ctrl[metric].to_numpy(float)
        t, p = stats.ttest_ind(a, b, equal_var=False)
        d, dlo, dhi = cohens_d(a, b)
        rows.append({
            'metric': metric,
            'exp_mean': a.mean(), 'exp_std': a.std(ddof=1),
            'ctrl_mean': b.mean(), 'ctrl_std': b.std(ddof=1),
            'reduction_pct': (b.mean() - a.mean()) / b.mean() * 100,
            'welch_t': t, 'p_value': p,
            'cohens_d': d, 'd_ci95_low': dlo, 'd_ci95_high': dhi,
        })
        print(f"{metric}: 实验 {a.mean():.2f}±{a.std(ddof=1):.2f} vs 对照 {b.mean():.2f}±{b.std(ddof=1):.2f} | "
              f"降低 {rows[-1]['reduction_pct']:.2f}% | Welch t={t:.2f}, p={p:.3g} | d={d:.2f} [{dlo:.2f},{dhi:.2f}]")

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    per_run.to_csv(os.path.join(out_dir, 'exp02_per_run.csv'), index=False)
    pd.DataFrame(rows).to_csv(os.path.join(out_dir, 'exp02_statistics.csv'), index=False)

    # 均值轨迹 ± 标准带（重跑轨迹，仅绘图用）
    curves = {'feedback': [], 'control': []}
    for arm, feedback in (('feedback', True), ('control', False)):
        for i in range(N_RUNS):
            set_seed('exp02', i)
            model = HybridEpidemicModel(
                population_size=POPULATION_SIZE,
                media_amplification=MEDIA_AMPLIFICATION,
                enable_info_behavior_feedback=feedback,
                enable_mosquito_transmission=True,
            )
            model.seed_infection(num_initial=NUM_INITIAL)
            model.run(num_days=NUM_DAYS)
            curves[arm].append(model.get_results()['I'].to_numpy())
    fig, ax = plt.subplots(figsize=(12, 5.5))
    days = np.arange(NUM_DAYS)
    for arm, color in (('feedback', '#2ecc71'), ('control', '#e74c3c')):
        arr = np.vstack(curves[arm])
        ax.plot(days, arr.mean(axis=0), color=color, label=f'{arm} (mean)')
        ax.fill_between(days, arr.mean(axis=0) - arr.std(axis=0),
                        arr.mean(axis=0) + arr.std(axis=0), color=color, alpha=0.2)
    ax.set_xlabel('Day'); ax.set_ylabel('Infected (I)')
    ax.set_title(f'Info-behavior feedback effect (n={N_RUNS}/arm, mean±std)')
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, 'exp02_info_effect.png'), dpi=150)
    plt.close(fig)

    p_star = per_run.loc[per_run['arm'] == 'feedback', 'time_avg_protection'].mean()
    print(f'\n实验组时间平均防护水平 P* = {p_star:.4f}（供实验5恒定防护对照使用）')

    record_manifest('exp02', '信息-行为反馈定量对比（Welch t + Cohen d）',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'media_amplification': MEDIA_AMPLIFICATION,
                     'runs_per_arm': N_RUNS, 'mosquito': 'on',
                     'protection_efficiency': 0.85, 'control': 'protection=0 (feedback off)',
                     'time_avg_protection_exp_arm': round(float(p_star), 4)},
                    ['exp02_statistics.csv', 'exp02_per_run.csv', 'exp02_info_effect.png'])


if __name__ == '__main__':
    main()
