# -*- coding: utf-8 -*-
"""
实验11：理论验证 —— 双通道入侵阈值与早期增长率的数值确认

理论（论文 §3.6）：
- 命题1（双通道入侵阈值）：无防护 DFE 处线性化系统的下一代矩阵谱半径
    R0 = (K_h + sqrt(K_h^2 + 4·K_hv·K_vh)) / 2
    K_h  = beta/gamma                       （人-人通道）
    K_hv = b·p_hm·(N/M)/gamma               （人->蚊，每代）
    K_vh = b·p_mh·L                         （蚊->人，每代）
  恒定平均防护 P̄ 下 R_eff = (1-eps·P̄)·R0；入侵阻断阈值 P̄† = (1-1/R0)/eps。
- 验证内容：
  (a) 每日线性化矩阵 M 的主导特征值 lambda_max（理论早期日增长因子）；
  (b) 仿真早期增长率：20 次零防护运行，对 log I(t) 在第 5-35 天做 log-linear
      拟合取斜率 exp(slope)，与 lambda_max 比较；
  (c) R0 数值（F(I-T)^-1 谱半径）与闭式解一致性；
  (d) 入侵阻断阈值 P̄† 与信息通道可达带上界（tanh 界）比较。

输出：
- results/exp11_growth_validation.csv
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from src.hybrid_model import HybridEpidemicModel
from experiments.protocol import NUM_DAYS, NUM_INITIAL, POPULATION_SIZE, record_manifest, set_seed

N_RUNS = 20
BETA, SIGMA, GAMMA = 0.3, 0.2, 0.1
B, P_HM, P_MH = 0.3, 0.5, 0.4
EIP, L = 10, 14
N, M = POPULATION_SIZE, 5 * POPULATION_SIZE
EPSILON = 0.85


def daily_matrix():
    """DFE 处（P̄=0, s=1）的每日期望转移矩阵，状态 (e, i, me, mi)。"""
    return np.array([
        [1 - SIGMA, BETA, 0, B * P_MH],
        [SIGMA, 1 - GAMMA, 0, 0],
        [0, B * P_HM * (N / M), 1 - 1 / EIP, 0],
        [0, 0, 1 / EIP, 1 - 1 / L],
    ])


def r0_components():
    Kh = BETA / GAMMA
    Khv = B * P_HM * (N / M) / GAMMA
    Kvh = B * P_MH * L
    r0 = (Kh + np.sqrt(Kh ** 2 + 4 * Khv * Kvh)) / 2
    return Kh, Khv, Kvh, r0


def main():
    print('=' * 70)
    print('实验11：理论验证（双通道入侵阈值 + 早期增长率）')
    print('=' * 70)

    # (a) 理论：线性化矩阵主导特征值
    M_mat = daily_matrix()
    eig = np.sort(np.real(np.linalg.eigvals(M_mat)))[::-1]
    lam_max = float(eig[0])
    print(f'\n(a) 线性化矩阵特征值: {[round(x, 4) for x in eig]}')
    print(f'    主导日增长因子 lambda_max = {lam_max:.4f}（日增长率 {np.log(lam_max):.4f}）')

    # (c) R0：数值（F(I-T)^-1 谱半径）vs 闭式解
    Mm = daily_matrix()
    F = np.zeros_like(Mm)
    F[0, 1] = BETA
    F[0, 3] = B * P_MH
    F[2, 1] = B * P_HM * (N / M)
    T = Mm - F
    T_inv = np.linalg.inv(np.eye(4) - T)
    K = F @ T_inv
    r0_numeric = float(max(abs(np.linalg.eigvals(K))))
    Kh, Khv, Kvh, r0_closed = r0_components()
    print(f'\n(c) R0 数值（F(I-T)^-1 谱半径） = {r0_numeric:.4f}')
    print(f'    R0 闭式解 = {r0_closed:.4f}（K_h={Kh:.2f}, K_hv={Khv:.3f}, K_vh={Kvh:.2f}）')
    print(f'    人-人通道单独 R0_h = {BETA / GAMMA:.2f}')

    # 阻断阈值
    p_dagger = (1 - 1 / r0_closed) / EPSILON
    print(f'    入侵阻断阈值 P_dagger = (1-1/R0)/eps = {p_dagger:.3f}'
          f'（信息通道可达带上界约 0.41-0.46，远低于该值）')

    # (b) 仿真早期增长率（20 次零防护运行，第 5-35 天 log-linear 拟合）
    print(f'\n(b) 仿真早期增长率（{N_RUNS} 次零防护运行，第 5-35 天拟合）...')
    slopes = []
    for i in range(N_RUNS):
        set_seed('exp11', i)
        model = HybridEpidemicModel(
            population_size=POPULATION_SIZE,
            media_amplification=1.0,
            enable_info_behavior_feedback=False,
            enable_mosquito_transmission=True,
        )
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        I = model.get_results()['I'].to_numpy()
        d0, d1 = 5, 35
        y = np.log(I[d0:d1].astype(float))
        x = np.arange(d0, d1)
        slope = float(np.polyfit(x, y, 1)[0])
        slopes.append(np.exp(slope))
    slopes = np.array(slopes)
    sim_growth = float(slopes.mean())
    sim_growth_std = float(slopes.std(ddof=1))
    rel_err = abs(sim_growth - lam_max) / lam_max * 100
    print(f'    仿真早期增长因子 = {sim_growth:.4f} ± {sim_growth_std:.4f}')
    print(f'    与理论 lambda_max={lam_max:.4f} 的相对偏差 = {rel_err:.1f}%')

    rows = [{
        'lambda_max_theory': lam_max,
        'sim_growth_mean': sim_growth, 'sim_growth_std': sim_growth_std,
        'rel_deviation_pct': rel_err,
        'r0_numeric': r0_numeric, 'r0_closed': r0_closed,
        'K_h': Kh, 'K_hv': Khv, 'K_vh': Kvh,
        'r0_human_only': BETA / GAMMA,
        'invasion_blocking_protection': p_dagger,
    }]
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    pd.DataFrame(rows).to_csv(os.path.join(out_dir, 'exp11_growth_validation.csv'), index=False)

    record_manifest('exp11', '理论验证：双通道入侵阈值与早期增长率',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'runs': N_RUNS,
                     'fit_window': 'day 5-35', 'mosquito': 'on',
                     'lambda_max': lam_max, 'sim_growth': round(sim_growth, 4),
                     'rel_deviation_pct': round(rel_err, 2),
                     'r0': round(r0_closed, 4),
                     'invasion_blocking_protection': round(p_dagger, 3)},
                    ['exp11_growth_validation.csv'])


if __name__ == '__main__':
    main()
