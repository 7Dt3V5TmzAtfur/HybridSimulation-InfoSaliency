# -*- coding: utf-8 -*-
"""
实验6：行为侧参数敏感性（κ 防护敏感度、η 行为惯性）

动机：实验3 只扫描了媒体放大系数 α；审稿意见指出行为侧核心参数 κ、η 未做敏感性分析。
本实验扫描 κ ∈ {0.5, 1.0, 1.5, 2.0, 3.0} × η ∈ {0.0, 0.15, 0.3, 0.5}，
每组 5 次独立重复，并以相同种子集运行零防护参照臂，计算峰值降低百分比。

设计（见 results/RUN_MANIFEST.yml）：seed = 606*1000 + i。
输出：
- results/exp06_behavior_sensitivity.csv
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from src.hybrid_model import HybridEpidemicModel
from experiments.protocol import (NUM_DAYS, NUM_INITIAL, POPULATION_SIZE,
                                  record_manifest, set_seed)

KAPPA_GRID = [0.5, 1.0, 1.5, 2.0, 3.0]
ETA_GRID = [0.0, 0.15, 0.3, 0.5]
N_RUNS = 10
MEDIA_AMPLIFICATION = 1.0


def run_combo(kappa: float, eta: float, feedback: bool) -> list:
    out = []
    for i in range(N_RUNS):
        set_seed('exp06', i)
        model = HybridEpidemicModel(
            population_size=POPULATION_SIZE,
            media_amplification=MEDIA_AMPLIFICATION,
            enable_info_behavior_feedback=feedback,
            enable_mosquito_transmission=True,
        )
        model.behavior_model.sensitivity = kappa
        model.risk_model.inertia = eta
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        df = model.get_results()
        out.append({
            'kappa': kappa, 'eta': eta, 'run': i,
            'peak_infected': int(df['I'].max()),
            'total_infected': int(df['R'].iloc[-1]),
        })
    return out


def main():
    print('=' * 70)
    print(f'实验6：行为参数敏感性（κ×η = {len(KAPPA_GRID)}×{len(ETA_GRID)} 组，每组 {N_RUNS} 次 + 零防护参照）')
    print('=' * 70)

    rows = []
    for kappa in KAPPA_GRID:
        for eta in ETA_GRID:
            rows += run_combo(kappa, eta, feedback=True)
            print(f'κ={kappa:.1f}, η={eta:.2f} 完成')
    # 零防护参照臂（κ/η 不生效，跑一次即可）
    ref = run_combo(KAPPA_GRID[0], ETA_GRID[0], feedback=False)
    ref_peak = float(np.mean([r['peak_infected'] for r in ref]))

    per_run = pd.DataFrame(rows)
    agg = per_run.groupby(['kappa', 'eta']).agg(
        peak_mean=('peak_infected', 'mean'), peak_std=('peak_infected', 'std'),
        total_mean=('total_infected', 'mean'), total_std=('total_infected', 'std'),
    ).reset_index()
    agg['peak_reduction_pct'] = (ref_peak - agg['peak_mean']) / ref_peak * 100

    print(f'\n零防护参照峰值 = {ref_peak:.1f}')
    pivot = agg.pivot(index='kappa', columns='eta', values='peak_reduction_pct')
    print('\n峰值降低%（行=κ，列=η）：')
    print(pivot.round(1).to_string())

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    per_run.to_csv(os.path.join(out_dir, 'exp06_per_run.csv'), index=False)
    agg.to_csv(os.path.join(out_dir, 'exp06_behavior_sensitivity.csv'), index=False)

    record_manifest('exp06', '行为参数敏感性（κ、η）',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'runs_per_group': N_RUNS,
                     'kappa_grid': str(KAPPA_GRID), 'eta_grid': str(ETA_GRID),
                     'reference_peak_zero_protection': round(ref_peak, 1),
                     'mosquito': 'on', 'protection_efficiency': 0.85},
                    ['exp06_behavior_sensitivity.csv', 'exp06_per_run.csv'])


if __name__ == '__main__':
    main()
