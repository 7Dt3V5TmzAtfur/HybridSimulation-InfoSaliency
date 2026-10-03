# -*- coding: utf-8 -*-
"""
实验9：响应形状扫描 —— S 型中点 μ × 斜率 κ 对"动态边际"的影响

动机（评审意见）：核心诊断"动态边际小源于响应函数饱和"目前只由 μ=0.5 单点支持。
本实验把中点 μ ∈ {0.3,0.4,0.5,0.6,0.7} 与斜率 κ ∈ {1.5,3.0} 扫描开，
对每个 (μ,κ) 组合跑三臂分解（动态 / 恒定 P*(μ,κ) / 零防护），
报告动态边际随响应形状的变化——即"动态何时开始重要"的边界。

设计（见 results/RUN_MANIFEST.yml）：
- N=1000，200 天，初始 10 人，蚊媒开；seed = 1111*1000 + i（零防护臂同种子集，共享一次运行）
- 每臂 10 次独立重复；P* 取该组合完整臂时间平均防护
- 另记录早熄灭频率（最终规模<半数人口），量化小种群随机衰减机制

输出：
- results/exp09_response_shape.csv      每组合三臂汇总
- results/exp09_per_run.csv             每次运行原始指标
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from scipy import stats

from src.hybrid_model import HybridEpidemicModel
from experiments.protocol import NUM_DAYS, NUM_INITIAL, POPULATION_SIZE, record_manifest, set_seed

N_RUNS = 10
MEDIA_AMPLIFICATION = 1.0
MU_GRID = [0.3, 0.4, 0.5, 0.6, 0.7]
KAPPA_GRID = [1.5, 3.0]


def run_arm(mu: float, kappa: float, mode: str, protection_override: float = None) -> list:
    out = []
    for i in range(N_RUNS):
        set_seed('exp09', i)
        model = HybridEpidemicModel(
            population_size=POPULATION_SIZE,
            media_amplification=MEDIA_AMPLIFICATION,
            enable_info_behavior_feedback=(mode == 'dynamic'),
            enable_mosquito_transmission=True,
            protection_override=protection_override if mode != 'dynamic' else None,
        )
        model.behavior_model.midpoint = mu
        model.behavior_model.sensitivity = kappa
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        df = model.get_results()
        hist = df['I'].to_numpy()
        fade_out = bool(int(df['R'].iloc[-1]) < 0.5 * POPULATION_SIZE)  # 早熄灭：最终规模<半数人口
        out.append({
            'mu': mu, 'kappa': kappa, 'mode': mode, 'run': i,
            'protection_level': protection_override if mode == 'constant' else np.nan,
            'peak_infected': int(hist.max()),
            'total_infected': int(df['R'].iloc[-1]),
            'time_avg_protection': (protection_override if mode == 'constant'
                                    else float(df['avg_protection'].mean())),
            'fade_out': fade_out,
        })
    return out


def main():
    print('=' * 70)
    print(f'实验9：响应形状扫描（μ={MU_GRID} × κ={KAPPA_GRID}，每臂 {N_RUNS} 次 + 共享零防护臂）')
    print('=' * 70)

    # 零防护臂与 (μ,κ) 无关（行为不更新），运行一次并共享
    zero = []
    for i in range(N_RUNS):
        set_seed('exp09', i)
        model = HybridEpidemicModel(
            population_size=POPULATION_SIZE,
            media_amplification=MEDIA_AMPLIFICATION,
            enable_info_behavior_feedback=False,
            enable_mosquito_transmission=True,
        )
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        df = model.get_results()
        hist = df['I'].to_numpy()
        zero.append({
            'mu': np.nan, 'kappa': np.nan, 'mode': 'zero', 'run': i,
            'protection_level': 0.0,
            'peak_infected': int(hist.max()),
            'total_infected': int(df['R'].iloc[-1]),
            'time_avg_protection': 0.0,
            'fade_out': bool(int(df['R'].iloc[-1]) < 0.5 * POPULATION_SIZE),
        })
    zero_peak = float(np.mean([r['peak_infected'] for r in zero]))
    zero_fade = float(np.mean([r['fade_out'] for r in zero]))
    print(f'\n零防护臂：峰值 {zero_peak:.1f}，早熄灭频率 {zero_fade*100:.0f}%（N=1000，最终规模<50%）')

    rows = list(zero)
    summary = []
    for mu in MU_GRID:
        for kappa in KAPPA_GRID:
            full = run_arm(mu, kappa, 'dynamic')
            p_star = float(np.mean([r['time_avg_protection'] for r in full]))
            const = run_arm(mu, kappa, 'constant', protection_override=p_star)
            rows += full + const

            a = np.array([r['peak_infected'] for r in full], float)
            b = np.array([r['peak_infected'] for r in const], float)
            t, p = stats.ttest_ind(a, b, equal_var=False)
            margin = (b.mean() - a.mean()) / b.mean() * 100
            red_full = (zero_peak - a.mean()) / zero_peak * 100
            red_const = (zero_peak - b.mean()) / zero_peak * 100
            fadeout_full = float(np.mean([r['fade_out'] for r in full]))
            summary.append({
                'mu': mu, 'kappa': kappa, 'p_star': p_star,
                'full_peak': a.mean(), 'full_peak_std': a.std(ddof=1),
                'const_peak': b.mean(), 'const_peak_std': b.std(ddof=1),
                'full_reduction_pct': red_full, 'const_reduction_pct': red_const,
                'dynamic_margin_pp': margin, 'welch_t': t, 'p_value': p,
                'fadeout_full': fadeout_full,
            })
            print(f'μ={mu:.1f} κ={kappa:.1f}: P*={p_star:.3f} | 峰值降低 {red_full:.1f}%（恒定 {red_const:.1f}%）'
                  f' | 动态边际 {margin:+.1f}pp（p={p:.3g}） | 早熄灭 {fadeout_full*100:.0f}%')

    per_run = pd.DataFrame(rows)
    agg = pd.DataFrame(summary)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    per_run.to_csv(os.path.join(out_dir, 'exp09_per_run.csv'), index=False)
    agg.to_csv(os.path.join(out_dir, 'exp09_response_shape.csv'), index=False)

    record_manifest('exp09', '响应形状扫描：S型中点×斜率对动态边际的影响',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'runs_per_arm': N_RUNS,
                     'mu_grid': str(MU_GRID), 'kappa_grid': str(KAPPA_GRID),
                     'zero_peak': round(zero_peak, 1), 'zero_fadeout_pct': round(zero_fade * 100, 0),
                     'mosquito': 'on', 'protection_efficiency': 0.85},
                    ['exp09_response_shape.csv', 'exp09_per_run.csv'])


if __name__ == '__main__':
    main()
