# -*- coding: utf-8 -*-
"""
实验8：机制对照 —— 经典 awareness 扩散基线 vs 本文信息显著性机制

目的：回应"与 awareness-epidemic 文献的正面实验比较"。
基线采用该文献的代表性机制结构（对应 Funk et al. (2009) 一类模型的骨架，
**非其精确复现**——基线的角色是机制类对照，不是文献基准复算）：

    A(t+1) = clip( A(t) + p_A·A(t)·S(t)/N + q·I(t)/N − d_A·A(t), 0, 1 )
    防护水平 P(t) = m·A(t)，两通道均按 (1 − ε·P) 调制（与本文模型同一调制形式）

- 知情通过接触扩散（p_A·A·S/N），感染者直接进入知情（q·I/N 项），并随时间遗忘（d_A）
- 公平比较准则：匹配时间平均防护水平（本文机制 ≈0.336；基线倍率 m* 按“动态臂的
  时间平均防护 = 0.336”用试点运行定点迭代确定后冻结并报告）
- 2 机制 × 3 模式（动态 / 恒定 / 零）× 10 次配对种子；本文机制臂用同一模型、
  同一种子集，恒定臂 P* 取本文机制动态臂的时间平均防护（与 exp05 同配方）

实现说明：基线为自包含实现，复用 src.hybrid_model 的蚊媒模型类与 SEIR 参数，
不含 DES/检测/住院抽签（已证明与传播解耦，见论文 §4.7），两机制的传播骨架一致。
本脚本不修改 src/（版本卫生：现有实验结果不受影响）。

输出：
- results/exp08_awareness_comparison.csv
- results/exp08_per_run.csv
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from scipy import stats

from src.hybrid_model import HybridEpidemicModel, MosquitoDynamicModel, MosquitoParams, SEIRParams
from experiments.protocol import NUM_DAYS, NUM_INITIAL, POPULATION_SIZE, record_manifest, set_seed

N_RUNS = 10
MEDIA_AMPLIFICATION = 1.0
EPSILON = 0.85

# awareness 基线参数（代表性参数化；公平性由"匹配时间平均防护"保证）
P_A = 0.25   # 知情的接触扩散系数
Q = 0.8      # 由感染率驱动的自发知情系数
D_A = 0.1    # 知情遗忘率
TARGET_PROTECTION = 0.336  # 与本文机制匹配的平均防护水平（exp02/exp05 实测）


class AwarenessABM:
    """自包含 ABM：与 HybridEpidemicModel 相同的 SEIR+蚊媒个体随机转移，
    行为模块替换为 awareness 扩散（动态）或冻结知情（恒定）。"""

    def __init__(self, population_size: int, m: float, mode: str, a_fixed: float = 0.0,
                 seir_params: SEIRParams = None, mosquito_params: MosquitoParams = None,
                 p_a: float = None, q: float = None, d_a: float = None):
        self.N = population_size
        self.m = m
        self.mode = mode          # 'dynamic' | 'constant'
        self.a_fixed = a_fixed    # 恒定模式下的 A
        self.p_A = p_a if p_a is not None else P_A   # 知情接触扩散系数（可覆盖）
        self.q = q if q is not None else Q           # 感染驱动知情系数（可覆盖）
        self.d_A = d_a if d_a is not None else D_A   # 知情遗忘率（可覆盖）
        self.sp = seir_params or SEIRParams()
        self.mosquito = MosquitoDynamicModel(mosquito_params or MosquitoParams())
        self.states = np.full(population_size, 'S', dtype=object)
        self.A = 0.0
        self.I_history = []
        self.protection_history = []

    def seed_infection(self, num_initial: int):
        idx = np.random.choice(self.N, num_initial, replace=False)
        self.states[idx] = 'I'

    def _transitions(self, day: int, P: float):
        """与 HybridEpidemicModel.step 完全一致的转移语义：
        只有"当日开始时"处于 E/I 状态的个体才获得 σ/γ 抽签（当日新感染者
        不在同日获得 σ 抽签）；感染 hazard 使用当日开始时的 I 计数。"""
        e_idx0 = np.where(self.states == 'E')[0]
        i_idx0 = np.where(self.states == 'I')[0]
        I = len(i_idx0)
        mosquito_risk = self.mosquito.update(I, day)
        beta_eff = self.sp.beta_base * (1 - EPSILON * P)
        hazard = min(1.0, beta_eff * I / self.N + mosquito_risk * (1 - EPSILON * P))
        s_idx = np.where(self.states == 'S')[0]
        new_infections = s_idx[np.random.random(len(s_idx)) < hazard]
        self.states[new_infections] = 'E'
        to_i = e_idx0[np.random.random(len(e_idx0)) < self.sp.sigma]
        self.states[to_i] = 'I'
        to_r = i_idx0[np.random.random(len(i_idx0)) < self.sp.gamma]
        self.states[to_r] = 'R'

    def step(self, day: int):
        S = int(np.sum(self.states == 'S'))
        I = int(np.sum(self.states == 'I'))
        if self.mode == 'dynamic':
            self.A = min(1.0, max(0.0, self.A + self.p_A * self.A * S / self.N
                                  + self.q * I / self.N - self.d_A * self.A))
        else:
            self.A = self.a_fixed
        P = min(1.0, self.m * self.A)
        self.protection_history.append(P)
        self._transitions(day, P)
        self.I_history.append(int(np.sum(self.states == 'I')))

    def run(self, num_days: int):
        for day in range(num_days):
            self.step(day)
        peak = int(max(self.I_history))
        return {
            'peak_infected': peak,
            'peak_day': int(np.argmax(self.I_history)),
            'total_infected': int(np.sum(self.states == 'R')),
            'time_avg_protection': float(np.mean(self.protection_history)),
            'protection_min': float(min(self.protection_history)),
            'protection_max': float(max(self.protection_history)),
            'time_avg_A': float(self.A) if self.mode == 'constant' else None,
        }


def run_awareness_arm(mode: str, m: float, a_fixed: float = 0.0) -> list:
    out = []
    for i in range(N_RUNS):
        set_seed('exp08', i)
        abm = AwarenessABM(POPULATION_SIZE, m=m, mode=mode, a_fixed=a_fixed)
        abm.seed_infection(NUM_INITIAL)
        r = abm.run(NUM_DAYS)
        mode_label = 'dynamic' if mode == 'dynamic' else ('zero' if m == 0 else 'constant')
        r.update({'mechanism': 'awareness', 'mode': mode_label, 'run': i,
                  'protection_level': m * a_fixed if mode_label == 'constant' else np.nan})
        out.append(r)
    return out


def run_ours_arm(mode: str, protection_override: float = None) -> list:
    out = []
    for i in range(N_RUNS):
        set_seed('exp08', i)
        model = HybridEpidemicModel(
            population_size=POPULATION_SIZE,
            media_amplification=MEDIA_AMPLIFICATION,
            enable_info_behavior_feedback=(mode == 'dynamic'),
            enable_mosquito_transmission=True,
            protection_override=protection_override if mode != 'dynamic' else None,
        )
        model.seed_infection(num_initial=NUM_INITIAL)
        model.run(num_days=NUM_DAYS)
        df = model.get_results()
        mode_label = 'dynamic' if mode == 'dynamic' else (
            'zero' if not protection_override else 'constant')
        out.append({
            'mechanism': 'ours', 'mode': mode_label, 'run': i,
            'peak_infected': int(df['I'].max()),
            'peak_day': int(df['I'].idxmax()),
            'total_infected': int(df['R'].iloc[-1]),
            'time_avg_protection': float(df['avg_protection'].mean()),
            'protection_min': float(df['avg_protection'].min()),
            'protection_max': float(df['avg_protection'].max()),
            'time_avg_A': None,
            'protection_level': protection_override if mode_label == 'constant' else np.nan,
        })
    return out


def calibrate_m() -> float:
    """二分标定 m*：动态臂时间平均防护 = TARGET_PROTECTION（响应对 m 单调递增）。"""
    lo, hi = 0.1, 2.0
    for it in range(9):
        m = 0.5 * (lo + hi)
        runs = run_awareness_arm('dynamic', m)
        avg_prot = float(np.mean([r['time_avg_protection'] for r in runs]))
        print(f'  [m* 试点 {it}] m={m:.4f} → 时间平均防护 {avg_prot:.4f}')
        if abs(avg_prot - TARGET_PROTECTION) < 0.004:
            break
        if avg_prot < TARGET_PROTECTION:
            lo = m
        else:
            hi = m
    print(f'  m* 冻结为 {m:.4f}')
    return m


def main():
    print('=' * 70)
    print(f'实验8：机制对照（awareness 扩散基线 vs 本文机制，3 模式 × {N_RUNS} 次配对种子）')
    print('=' * 70)

    print('\n[1/3] 标定基线倍率 m*（目标：时间平均防护 = 0.336）')
    m_star = calibrate_m()

    print('\n[2/3] 运行 awareness 基线三臂...')
    aware_dynamic = run_awareness_arm('dynamic', m_star)
    a_bar = float(np.mean([r['time_avg_protection'] for r in aware_dynamic]) / m_star)
    print(f'  动态臂时间平均知情 Ā = {a_bar:.4f}（恒定臂取 A ≡ Ā，防护 = m*·Ā ≈ 0.336）')
    aware_constant = run_awareness_arm('constant', m_star, a_fixed=a_bar)
    aware_zero = run_awareness_arm('constant', m=0.0, a_fixed=a_bar)

    print('[3/3] 运行本文机制三臂（同种子集）...')
    ours_dynamic = run_ours_arm('dynamic')
    p_star_ours = float(np.mean([r['time_avg_protection'] for r in ours_dynamic]))
    print(f'  本文机制时间平均防护 P* = {p_star_ours:.4f}')
    ours_constant = run_ours_arm('constant', protection_override=p_star_ours)
    ours_zero = run_ours_arm('constant', protection_override=0.0)

    records = aware_dynamic + aware_constant + aware_zero + ours_dynamic + ours_constant + ours_zero
    per_run = pd.DataFrame(records)
    per_run['arm'] = per_run['mechanism'] + '_' + per_run['mode']
    agg = per_run.groupby('arm').agg(
        peak_mean=('peak_infected', 'mean'), peak_std=('peak_infected', 'std'),
        total_mean=('total_infected', 'mean'), total_std=('total_infected', 'std'),
    )
    for mech in ('awareness', 'ours'):
        z = agg.loc[f'{mech}_zero']
        for mode in ('dynamic', 'constant'):
            agg.loc[f'{mech}_{mode}', 'peak_reduction_pct'] = (
                (z['peak_mean'] - agg.loc[f'{mech}_{mode}', 'peak_mean']) / z['peak_mean'] * 100)
        a = per_run.loc[per_run['arm'] == f'{mech}_dynamic', 'peak_infected'].to_numpy(float)
        b = per_run.loc[per_run['arm'] == f'{mech}_constant', 'peak_infected'].to_numpy(float)
        t, p = stats.ttest_ind(a, b, equal_var=False)
        agg.loc[f'{mech}_dynamic', 'marginal_t'] = t
        agg.loc[f'{mech}_dynamic', 'marginal_p'] = p
        agg.loc[f'{mech}_dynamic', 'marginal_pp'] = (b.mean() - a.mean()) / b.mean() * 100

    print('\n=== 机制对照（均值±标准差；降低% 相对各自零防护臂） ===')
    for arm in ('awareness_zero', 'awareness_constant', 'awareness_dynamic',
                'ours_zero', 'ours_constant', 'ours_dynamic'):
        r = agg.loc[arm]
        red = '' if arm.endswith('zero') else f"（{r['peak_reduction_pct']:+.1f}%）"
        marg = '' if arm.endswith('zero') or arm.endswith('constant') else \
            f" | 动态边际 {r['marginal_pp']:+.1f}pp（p={r['marginal_p']:.3g}）"
        print(f"{arm}: 峰值 {r['peak_mean']:.1f}±{r['peak_std']:.1f}{red}，"
              f"总感染 {r['total_mean']:.1f}±{r['total_std']:.1f}{marg}")

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    per_run.to_csv(os.path.join(out_dir, 'exp08_per_run.csv'), index=False)
    agg.reset_index().to_csv(os.path.join(out_dir, 'exp08_awareness_comparison.csv'), index=False)

    record_manifest('exp08', '机制对照：awareness 扩散基线 vs 本文信息显著性机制（匹配平均防护）',
                    {'population': POPULATION_SIZE, 'days': NUM_DAYS,
                     'initial_infected': NUM_INITIAL, 'runs_per_arm': N_RUNS,
                     'awareness_params': f'p_A={P_A}, q={Q}, d_A={D_A}',
                     'm_star': round(m_star, 4), 'a_bar': round(a_bar, 4),
                     'target_protection': TARGET_PROTECTION,
                     'p_star_ours': round(p_star_ours, 4), 'mosquito': 'on'},
                    ['exp08_awareness_comparison.csv', 'exp08_per_run.csv'])


if __name__ == '__main__':
    main()
