# -*- coding: utf-8 -*-
"""
实验4：真实登革热数据校准（OpenDengue 巴西周报数据）

数据（见 results/RUN_MANIFEST.yml）：
- data/National_extract_V1_3.csv（OpenDengue v1.3 国家级抽取，实际提交数据）
- 国家：BRAZIL；口径：case_definition='Total'（该口径覆盖 2016-2023；'Probable' 仅覆盖
  2015）；分辨率：周
- 校准窗口：2019 自然年（52 周完整；2020 年数据在抽取中缺测，未采用）

方法（与 src/calibration.py 文档一致）：
1. 确定性替代系统（与 ABM 期望动力学同构，含蚊媒与信息-行为反馈、防护调制 ε）
2. 网格搜索 (β, σ, γ, α, I0)，报告率 ρ 每点闭式最小二乘
3. 最优参数代入 ABM（人口按比例缩放）复核替代系统一致性

输出：
- results/exp04_calibration_results.csv   最优参数与拟合指标
- results/exp04_grid_top.csv              网格前 20 名（可审计）
- results/exp04_fit.csv                   周数据 vs 拟合曲线
- results/exp04_surrogate_validation.csv  替代系统 vs ABM（每万人周发病率）
- results/exp04_dengue_calibration.png
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.calibration import (DeterministicSurrogate, estimate_basic_reproduction_number,
                             grid_calibrate, weekly_aggregate)
from src.data_loader import DengueDataLoader
from src.hybrid_model import HybridEpidemicModel, MosquitoParams, SEIRParams
from experiments.protocol import (BASE_SEED, record_manifest, set_seed)

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'data', 'National_extract_V1_3.csv')
COUNTRY = 'BRAZIL'
START, END = '2019-01-01', '2019-12-31'
POPULATION_BRAZIL_2019 = 211_000_000  # 2019 年巴西人口（World Bank，约值）
MOSQUITO_PER_HUMAN = 5.0              # 与参考配置 N=1000/M=5000 的比例一致

# ABM 复核运行配置（缩放人口，保持蚊/人比例）
ABM_POPULATION = 10_000
ABM_NUM_DAYS = 364
ABM_N_RUNS = 5


def main():
    print('=' * 70)
    print(f'实验4：真实数据校准（OpenDengue {COUNTRY} {START[:4]} 周报，替代系统网格搜索）')
    print('=' * 70)

    # [1/5] 加载真实数据
    loader = DengueDataLoader()
    data = loader.load_opendengue_national(DATA_FILE, country=COUNTRY,
                                           start=START, end=END,
                                           case_definition='Total')
    print(f'\n[1/5] 真实数据: {len(data)} 周，'
          f"{data['date'].min().date()} → {data['date'].max().date()}，"
          f"总病例 {data['cases'].sum():,.0f}，周峰值 {data['cases'].max():,.0f}")
    assert len(data) >= 50, f'校准窗口周数不足: {len(data)}'

    # [2/5] 网格搜索（替代系统）
    print('\n[2/5] 网格搜索（β×σ×γ×α×I0，报告率 ρ 闭式解）...')
    grid = grid_calibrate(data['cases'].to_numpy(), population=POPULATION_BRAZIL_2019)
    best = grid.iloc[0]
    print(grid.head(10).to_string())
    print(f"\n最优: β={best['beta']}, σ={best['sigma']}, γ={best['gamma']}, "
          f"α={best['media_amp']}, I0={best['i0']:.0f}, ρ={best['rho']:.4f}")
    print(f"RMSE={best['rmse']:.0f}, R²={best['r2']:.3f}, "
          f"R0(人类通道)={best['beta'] / best['gamma']:.2f}")

    # [3/5] 拟合曲线输出
    sim = DeterministicSurrogate(
        POPULATION_BRAZIL_2019,
        SEIRParams(beta_base=best['beta'], sigma=best['sigma'], gamma=best['gamma']),
        media_amplification=best['media_amp'],
    ).run(len(data) * 7, i0=int(best['i0']), e0=int(best['i0']))
    model_weekly = weekly_aggregate(sim['incidence'])
    fitted = best['rho'] * model_weekly[:len(data)]
    fit_df = pd.DataFrame({
        'date': data['date'], 'data_cases': data['cases'].to_numpy(),
        'model_fitted_cases': fitted,
        'model_true_weekly_infections': model_weekly[:len(data)],
    })
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    fit_df.to_csv(os.path.join(out_dir, 'exp04_fit.csv'), index=False)
    grid.head(20).to_csv(os.path.join(out_dir, 'exp04_grid_top.csv'), index=False)
    pd.DataFrame([best]).to_csv(os.path.join(out_dir, 'exp04_calibration_results.csv'), index=False)

    # [4/5] ABM 复核：替代系统 vs 个体仿真（缩放人口，机制一致性）
    print(f'\n[4/5] ABM 复核（N={ABM_POPULATION}, M={MOSQUITO_PER_HUMAN*ABM_POPULATION:.0f}, '
          f'{ABM_NUM_DAYS}天 × {ABM_N_RUNS}次）...')
    # 初始感染按 I0 比例缩放
    i0_scaled = max(5, int(round(best['i0'] * ABM_POPULATION / POPULATION_BRAZIL_2019)))
    abm_weekly = []
    for i in range(ABM_N_RUNS):
        set_seed('exp04', i)
        model = HybridEpidemicModel(
            population_size=ABM_POPULATION,
            seir_params=SEIRParams(beta_base=best['beta'], sigma=best['sigma'],
                                   gamma=best['gamma']),
            media_amplification=best['media_amp'],
            mosquito_params=MosquitoParams(
                mosquito_population=int(MOSQUITO_PER_HUMAN * ABM_POPULATION)),
            enable_info_behavior_feedback=True,
            enable_mosquito_transmission=True,
        )
        model.seed_infection(num_initial=i0_scaled)
        model.run(num_days=ABM_NUM_DAYS)
        s_arr = model.get_results()['S'].to_numpy()
        inc = -np.diff(s_arr)  # 每日新感染 = 易感者减少量（精确）
        abm_weekly.append(weekly_aggregate(inc, 7))
    surrogate_scaled = weekly_aggregate(sim['incidence'], 7) * ABM_POPULATION / POPULATION_BRAZIL_2019
    abm_arr = np.vstack(abm_weekly)
    n_weeks = min(len(surrogate_scaled), abm_arr.shape[1])
    val_df = pd.DataFrame({
        'week': np.arange(n_weeks),
        'surrogate_per_10k': surrogate_scaled[:n_weeks],
        'abm_per_10k_mean': abm_arr[:, :n_weeks].mean(axis=0),
        'abm_per_10k_std': abm_arr[:, :n_weeks].std(axis=0, ddof=1),
    })
    # 机制一致性：相关系数与 ABM 均值落在替代系统 ±2×(ABM 间标准差+5%) 内的周占比
    corr = float(np.corrcoef(val_df['surrogate_per_10k'], val_df['abm_per_10k_mean'])[0, 1])
    inside = float(np.mean(
        np.abs(val_df['abm_per_10k_mean'] - val_df['surrogate_per_10k'])
        <= 2 * val_df['abm_per_10k_std'] + 0.05 * val_df['surrogate_per_10k']))
    val_df.to_csv(os.path.join(out_dir, 'exp04_surrogate_validation.csv'), index=False)
    print(f'替代系统 vs ABM：周发病率相关系数 r={corr:.3f}；'
          f'ABM 均值落在替代系统±2σ内（+5%容差）的周占比 {inside*100:.0f}%')

    # [5/5] 可视化
    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=False)
    ax = axes[0]
    ax.bar(range(len(fit_df)), fit_df['data_cases'], color='#95a5a6', alpha=0.6,
           label='Reported weekly cases (Brazil 2019, OpenDengue)')
    ax.plot(range(len(fit_df)), fit_df['model_fitted_cases'], 'r-', linewidth=2,
            label=f'Fitted (ρ={best["rho"]:.3f})')
    ax.set_ylabel('Weekly cases')
    ax.set_title(f"Calibration: grid-searched surrogate (R²={best['r2']:.3f}, "
                 f"RMSE={best['rmse']:.0f}, R0_human={best['beta']/best['gamma']:.2f})")
    ax.legend(); ax.grid(alpha=0.3)
    ax = axes[1]
    ax.plot(val_df['week'], val_df['surrogate_per_10k'], 'k-', label='Surrogate (per 10k)')
    ax.plot(val_df['week'], val_df['abm_per_10k_mean'], 'b-', label='ABM mean (per 10k)')
    ax.fill_between(val_df['week'],
                    val_df['abm_per_10k_mean'] - val_df['abm_per_10k_std'],
                    val_df['abm_per_10k_mean'] + val_df['abm_per_10k_std'],
                    color='b', alpha=0.2, label='ABM ±std')
    ax.set_xlabel(f'Week (ABM verification, N={ABM_POPULATION})')
    ax.set_ylabel('Weekly incidence per 10k')
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, 'exp04_dengue_calibration.png'), dpi=150)
    plt.close(fig)

    record_manifest('exp04', '真实数据校准（OpenDengue 巴西2019周报，替代系统网格搜索+ABM复核）',
                    {'data_file': 'data/National_extract_V1_3.csv',
                     'country': COUNTRY, 'window': f'{START}..{END}',
                     'case_definition': 'Total', 'weeks': len(data),
                     'population_surrogate': POPULATION_BRAZIL_2019,
                     'mosquito_per_human': MOSQUITO_PER_HUMAN,
                     'best_beta': float(best['beta']), 'best_sigma': float(best['sigma']),
                     'best_gamma': float(best['gamma']), 'best_alpha': float(best['media_amp']),
                     'best_i0': float(best['i0']), 'reporting_rate_rho': float(best['rho']),
                     'rmse': float(best['rmse']), 'r2': float(best['r2']),
                     'R0_human': float(best['beta'] / best['gamma']),
                     'abm_population': ABM_POPULATION, 'abm_runs': ABM_N_RUNS,
                     'surrogate_abm_correlation': corr},
                    ['exp04_calibration_results.csv', 'exp04_grid_top.csv', 'exp04_fit.csv',
                     'exp04_surrogate_validation.csv', 'exp04_dengue_calibration.png'])


if __name__ == '__main__':
    main()
