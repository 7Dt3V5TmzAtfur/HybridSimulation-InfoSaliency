# -*- coding: utf-8 -*-
"""
实验10：awareness 基线参数敏感性 —— 动态边际结论对 (p_A, d_A) 的稳健性

动机（评审意见）：实验8 的"+22.5pp 显著动态边际"结论依赖 awareness 基线的单一参数化
（p_A=0.25, q=0.8, d_A=0.1）。本实验在 (p_A, d_A) 的 3×3 网格上（q 固定 0.8）
重复机制对照（每配置二分标定 m* 匹配平均防护 0.336，动态/恒定两臂 × 5 次），
检验动态边际的符号与显著性是否稳健。

设计（见 results/RUN_MANIFEST.yml）：
- 网格：p_A ∈ {0.15, 0.25, 0.35} × d_A ∈ {0.05, 0.1, 0.2}，q=0.8
- 每配置：m* 二分标定（3 试点种子，容差 0.01）→ 动态臂 5 次 + 恒定臂 5 次
  （A ≡ 动态臂时间平均知情），seed = 1212*1000 + i
- 复用 exp08 的 AwarenessABM 实现（导入，不复制）

输出：
- results/exp10_awareness_sensitivity.csv
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from scipy import stats

from experiments.exp08_awareness_baseline import (AwarenessABM, D_A, P_A, Q,
                                                  NUM_DAYS, NUM_INITIAL,
                                                  POPULATION_SIZE, TARGET_PROTECTION)
from experiments.protocol import record_manifest, set_seed

N_RUNS = 5
P_A_GRID = [0.15, 0.25, 0.35]
D_A_GRID = [0.05, 0.1, 0.2]


def run_aware(m: float, mode: str, p_a: float, d_a: float, a_fixed: float = 0.0) -> list:
    out = []
    for i in range(N_RUNS):
        set_seed('exp10', i)
        abm = AwarenessABM(POPULATION_SIZE, m=m, mode=mode, a_fixed=a_fixed,
                           p_a=p_a, d_a=d_a)
        abm.seed_infection(NUM_INITIAL)
        r = abm.run(NUM_DAYS)
        r.update({'p_A': p_a, 'd_A': d_a, 'mode': mode, 'run': i})
        out.append(r)
    return out


def calibrate_m(p_a: float, d_a: float) -> float:
    lo, hi = 0.1, 2.0
    m = 0.5
    for _ in range(7):
        m = 0.5 * (lo + hi)
        runs = run_aware(m, 'dynamic', p_a, d_a)
        avg = float(np.mean([r['time_avg_protection'] for r in runs]))
        if abs(avg - TARGET_PROTECTION) < 0.01:
            break
        if avg < TARGET_PROTECTION:
            lo = m
        else:
            hi = m
    return m


def main():
    print('=' * 70)
    print(f'实验10：awareness 参数敏感性（(p_A,d_A) 3×3，q=0.8，每臂 {N_RUNS} 次）')
    print('=' * 70)

    rows = []
    for p_a in P_A_GRID:
        for d_a in D_A_GRID:
            m_star = calibrate_m(p_a, d_a)
            dynamic = run_aware(m_star, 'dynamic', p_a, d_a)
            a_bar = float(np.mean([r['time_avg_protection'] for r in dynamic]) / m_star)
            constant = run_aware(m_star, 'constant', p_a, d_a, a_fixed=a_bar)

            a = np.array([r['peak_infected'] for r in dynamic], float)
            b = np.array([r['peak_infected'] for r in constant], float)
            t, p = stats.ttest_ind(a, b, equal_var=False)
            margin = (b.mean() - a.mean()) / b.mean() * 100
            rows.append({
                'p_A': p_a, 'd_A': d_a, 'm_star': m_star, 'a_bar': a_bar,
                'dynamic_peak': a.mean(), 'dynamic_peak_std': a.std(ddof=1),
                'constant_peak': b.mean(), 'constant_peak_std': b.std(ddof=1),
                'dynamic_margin_pp': margin, 'welch_t': t, 'p_value': p,
            })
            print(f'p_A={p_a:.2f} d_A={d_a:.2f}: m*={m_star:.3f} | '
                  f'动态 {a.mean():.1f} vs 恒定 {b.mean():.1f} | 边际 {margin:+.1f}pp（p={p:.3g}）')

    agg = pd.DataFrame(rows)
    n_sig = int((agg['p_value'] < 0.05).sum())
    n_pos = int((agg['dynamic_margin_pp'] > 0).sum())
    print(f'\n9 配置中：动态边际为正 {n_pos}/9，显著（p<0.05）{n_sig}/9')

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    agg.to_csv(os.path.join(out_dir, 'exp10_awareness_sensitivity.csv'), index=False)

    record_manifest('exp10', 'awareness 基线参数敏感性（(p_A,d_A) 3×3 mini-sweep）',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'runs_per_arm': N_RUNS,
                     'p_A_grid': str(P_A_GRID), 'd_A_grid': str(D_A_GRID), 'q': Q,
                     'target_protection': TARGET_PROTECTION,
                     'n_margin_positive': n_pos, 'n_margin_significant': n_sig},
                    ['exp10_awareness_sensitivity.csv'])


if __name__ == '__main__':
    main()
