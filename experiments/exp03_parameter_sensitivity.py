# -*- coding: utf-8 -*-
"""
实验3：媒体放大系数 α 的参数敏感性

设计（见 results/RUN_MANIFEST.yml）：
- α ∈ {0.5, 1.0, 1.5, 2.0, 3.0, 5.0}，每组 10 次独立重复（seed = 303*1000 + i）
- 报告均值±标准差；α=0.5 为参照组
- 阈值分析：预设定成功标准"峰值降低≥20%"（research_framework.md 的事先约定，
  非外部文献阈值），在更细的 α 网格上检验能否达到
输出：
- results/exp03_sensitivity.csv       主网格（均值±标准差）
- results/exp03_threshold.csv         细网格阈值分析
- results/exp03_parameter_sensitivity.png
- results/exp03_threshold_analysis.png
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
from experiments.protocol import (NUM_DAYS, NUM_INITIAL, POPULATION_SIZE,
                                  record_manifest, set_seed)

ALPHA_GRID = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
N_RUNS = 10
THRESHOLD_PCT = 20.0  # 预设定成功标准（峰值降低百分比）
THRESHOLD_GRID = [round(x, 2) for x in np.arange(0.5, 10.01, 0.5)]
N_RUNS_THRESHOLD = 5


def run_alpha(alpha: float, n_runs: int, exp: str = 'exp03') -> list:
    out = []
    for i in range(n_runs):
        set_seed(exp, i)
        model = HybridEpidemicModel(
            population_size=POPULATION_SIZE,
            media_amplification=alpha,
            enable_info_behavior_feedback=True,
            enable_mosquito_transmission=True,
        )
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        df = model.get_results()
        out.append({
            'media_amplification': alpha, 'run': i,
            'peak_infected': int(df['I'].max()),
            'total_infected': int(df['R'].iloc[-1]),
            'peak_day': int(df['I'].idxmax()),
            'max_protection': float(df['avg_protection'].max()),
        })
    return out


def main():
    print('=' * 70)
    print(f'实验3：媒体放大系数敏感性（α 网格 × 每组{N_RUNS}次；阈值分析 {THRESHOLD_GRID[0]}–{THRESHOLD_GRID[-1]} × {N_RUNS_THRESHOLD}次）')
    print('=' * 70)

    rows = []
    for alpha in ALPHA_GRID:
        rows += run_alpha(alpha, N_RUNS)
    per_run = pd.DataFrame(rows)
    agg = per_run.groupby('media_amplification').agg(
        peak_mean=('peak_infected', 'mean'), peak_std=('peak_infected', 'std'),
        total_mean=('total_infected', 'mean'), total_std=('total_infected', 'std'),
        peak_day_mean=('peak_day', 'mean'), max_protection_mean=('max_protection', 'mean'),
    ).reset_index()
    ref = agg.loc[agg['media_amplification'] == ALPHA_GRID[0]].iloc[0]
    agg['peak_reduction_pct'] = (ref['peak_mean'] - agg['peak_mean']) / ref['peak_mean'] * 100
    agg['total_reduction_pct'] = (ref['total_mean'] - agg['total_mean']) / ref['total_mean'] * 100

    print('\n=== 主网格（均值±标准差，参照 α=%s） ===' % ALPHA_GRID[0])
    for _, r in agg.iterrows():
        print(f"α={r['media_amplification']:.1f}: 峰值 {r['peak_mean']:.1f}±{r['peak_std']:.1f} "
              f"({r['peak_reduction_pct']:+.2f}%)，总感染 {r['total_mean']:.1f}±{r['total_std']:.1f}")

    # 阈值分析（细网格）
    trows = []
    for alpha in THRESHOLD_GRID:
        trows += run_alpha(alpha, N_RUNS_THRESHOLD, exp='exp03')
    tper_run = pd.DataFrame(trows)
    tagg = tper_run.groupby('media_amplification').agg(
        peak_mean=('peak_infected', 'mean'), peak_std=('peak_infected', 'std')).reset_index()
    tref = tagg['peak_mean'].iloc[0]
    tagg['peak_reduction_pct'] = (tref - tagg['peak_mean']) / tref * 100
    reached = tagg[tagg['peak_reduction_pct'] >= THRESHOLD_PCT]
    if len(reached):
        crit = reached['media_amplification'].iloc[0]
        print(f'\n[阈值分析] 预设定标准（峰值降低≥{THRESHOLD_PCT}%）在 α={crit:.2f} 首次达到')
    else:
        crit = np.nan
        best = tagg.loc[tagg['peak_reduction_pct'].idxmax()]
        print(f'\n[阈值分析] 测试范围内未达到 {THRESHOLD_PCT}%；最大降低 {best["peak_reduction_pct"]:.2f}%（α={best["media_amplification"]:.1f}）')

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    per_run.to_csv(os.path.join(out_dir, 'exp03_per_run.csv'), index=False)
    agg.to_csv(os.path.join(out_dir, 'exp03_sensitivity.csv'), index=False)
    tagg.to_csv(os.path.join(out_dir, 'exp03_threshold.csv'), index=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(agg['media_amplification'], agg['peak_mean'], yerr=agg['peak_std'],
                marker='o', capsize=4, color='#2980b9', label='Peak infected (mean±std)')
    ax.axhline(ref['peak_mean'], color='gray', linestyle='--', alpha=0.7, label='Reference α=0.5')
    ax.set_xlabel('Media amplification α'); ax.set_ylabel('Peak infected')
    ax.set_title(f'Parameter sensitivity (n={N_RUNS}/group)')
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, 'exp03_parameter_sensitivity.png'), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(tagg['media_amplification'], tagg['peak_reduction_pct'], marker='.', color='#8e44ad')
    ax.axhline(THRESHOLD_PCT, color='red', linestyle='--', linewidth=2,
               label=f'Pre-specified threshold ({THRESHOLD_PCT:.0f}%)')
    ax.set_xlabel('Media amplification α'); ax.set_ylabel('Peak reduction vs α=0.5 [%]')
    ax.set_title(f'Threshold analysis (n={N_RUNS_THRESHOLD}/point)')
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, 'exp03_threshold_analysis.png'), dpi=150)
    plt.close(fig)

    record_manifest('exp03', '媒体放大系数敏感性与阈值分析',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'alpha_grid': str(ALPHA_GRID),
                     'runs_per_group': N_RUNS, 'threshold_pct': THRESHOLD_PCT,
                     'threshold_grid': f'{THRESHOLD_GRID[0]}..{THRESHOLD_GRID[-1]} step 0.5',
                     'threshold_runs': N_RUNS_THRESHOLD, 'critical_alpha': None if np.isnan(crit) else float(crit),
                     'mosquito': 'on', 'protection_efficiency': 0.85},
                    ['exp03_sensitivity.csv', 'exp03_per_run.csv', 'exp03_threshold.csv',
                     'exp03_parameter_sensitivity.png', 'exp03_threshold_analysis.png'])


if __name__ == '__main__':
    main()
