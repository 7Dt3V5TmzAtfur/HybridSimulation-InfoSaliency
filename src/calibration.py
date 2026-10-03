# -*- coding: utf-8 -*-
"""
参数校准模块（确定性等效系统 + 网格搜索）

方法说明（与论文 §3.4.4 一致）：
- 直接在随机 ABM 上做梯度优化（旧实现）在方法论上不成立：目标函数含仿真噪声，
  L-BFGS-B 的梯度估计无意义，且单次评估代价高。
- 本模块构造与 HybridEpidemicModel **期望动力学同构**的确定性替代系统
  （DeterministicSurrogate）：相同的 SEIR 转移、蚊媒差分方程、信息显著性-风险感知-
  防护行为方程、防护调制（ε），感染 hazard 与 ABM 的单步伯努利抽样期望一致。
- 校准在替代系统上做**网格搜索**（论文口径），报告率 ρ（感染→报告病例的比例）
  对每个网格点用最小二乘闭式解（标准做法：法定传染病存在漏报）。
- 拟合参数随后代入 ABM 复核替代系统与个体仿真的机制一致性（见 exp04）。
"""

import numpy as np
import pandas as pd

from src.hybrid_model import MosquitoParams, SEIRParams

# 与模型默认一致的信息-行为参数
INFO_WEIGHT = 0.6
SOCIAL_WEIGHT = 0.3
PERSONAL_WEIGHT = 0.1
INERTIA = 0.3
KAPPA = 1.5
DECAY_RATE = 0.1
MOSQUITO_PER_HUMAN = 5.0  # 蚊子/人口比例（与参考配置 N=1000, M=5000 一致）


class DeterministicSurrogate:
    """与 HybridEpidemicModel 期望动力学同构的确定性替代系统。"""

    def __init__(self, population: int,
                 seir_params: SEIRParams = None,
                 media_amplification: float = 1.0,
                 mosquito_params: MosquitoParams = None):
        self.population = population
        self.sp = seir_params or SEIRParams()
        self.media_amplification = media_amplification
        self.mp = mosquito_params or MosquitoParams()

    def run(self, num_days: int, i0: int, e0: int):
        """日步长显式欧拉积分。

        Returns:
            dict with arrays: S, E, I, R, incidence (每日新感染), protection
        """
        N = float(self.population)
        sp, mp = self.sp, self.mp
        M = max(1.0, MOSQUITO_PER_HUMAN * N)

        S, E, I, R = N - i0 - e0, float(e0), float(i0), 0.0
        Me = Mi = 0.0
        risk_prev = 0.0

        S_arr = np.empty(num_days); E_arr = np.empty(num_days)
        I_arr = np.empty(num_days); R_arr = np.empty(num_days)
        inc_arr = np.empty(num_days); prot_arr = np.empty(num_days)

        for t in range(num_days):
            # 信息显著性（与 InformationSaliencyModel 相同）
            sal = min(1.0, (I / N) * self.media_amplification * np.exp(-DECAY_RATE * t / 100))
            # 风险感知（与 RiskPerceptionModel 相同；个人经历期望 = (E+I)/N）
            target = (INFO_WEIGHT * sal + SOCIAL_WEIGHT * (I / N)
                      + PERSONAL_WEIGHT * ((E + I) / N))
            risk_level = (1 - INERTIA) * target + INERTIA * risk_prev
            risk_prev = risk_level
            # 防护行为（与 BehaviorModel 相同）
            P = 1.0 / (1.0 + np.exp(-KAPPA * (risk_level - 0.5)))
            prot_arr[t] = P

            # 蚊媒差分方程（与 MosquitoDynamicModel 相同）
            new_exposed_m = mp.biting_rate * mp.transmission_human_to_mosquito * I \
                * max(0.0, (M - Mi - Me)) / M
            new_infected_m = Me / mp.extrinsic_incubation_period
            death_m = Mi / mp.mosquito_lifespan
            Me = max(0.0, Me + new_exposed_m - new_infected_m)
            Mi = max(0.0, Mi + new_infected_m - death_m)
            risk_m = min(1.0, mp.biting_rate * mp.transmission_mosquito_to_human
                         * (Mi / M) * mp.seasonal_factor)

            # 感染 hazard：两通道均受防护调制（与模型 step() 相同）
            beta_eff = sp.beta_base * (1 - sp.protection_efficiency * P)
            hazard = min(1.0, beta_eff * I / N
                         + risk_m * (1 - sp.protection_efficiency * P))
            new_infections = hazard * S

            # SEIR 转移（期望动力学）
            e_to_i = sp.sigma * E
            i_to_r = sp.gamma * I
            S = S - new_infections
            E = E + new_infections - e_to_i
            I = I + e_to_i - i_to_r
            R = R + i_to_r

            S_arr[t] = S; E_arr[t] = E; I_arr[t] = I; R_arr[t] = R
            inc_arr[t] = new_infections

        return {'S': S_arr, 'E': E_arr, 'I': I_arr, 'R': R_arr,
                'incidence': inc_arr, 'protection': prot_arr}


def weekly_aggregate(daily: np.ndarray, period: int = 7) -> np.ndarray:
    """日度序列按 period 天求和聚合（末尾不足整周截断）。"""
    n = (len(daily) // period) * period
    return daily[:n].reshape(-1, period).sum(axis=1)


def grid_calibrate(data_weekly: np.ndarray, population: int,
                   beta_grid=None, sigma_grid=None, gamma_grid=None,
                   alpha_grid=None, i0_grid=None) -> pd.DataFrame:
    """替代系统上的网格搜索。

    Args:
        data_weekly: 周报告病例数组
        population: 总人口（蚊子种群按 MOSQUITO_PER_HUMAN 比例缩放）
        各网格：β（日传播率）、σ（潜伏期倒数/日）、γ（恢复率倒数/日）、
                α（媒体放大系数）、I0（初始感染数）
        报告率 ρ 对每个组合用最小二乘闭式解：ρ* = <model, data> / <model, model>

    Returns:
        按校准 RMSE 升序的 DataFrame（含 r2、rho、R0 等）
    """
    beta_grid = beta_grid or [0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    sigma_grid = sigma_grid or [0.1, 0.2, 0.3]
    gamma_grid = gamma_grid or [0.05, 0.1, 0.15, 0.2]
    alpha_grid = alpha_grid or [0.5, 1.0, 2.0]
    i0_grid = i0_grid or [1e5, 5e5, 2e6]

    num_days = len(data_weekly) * 7
    data = np.asarray(data_weekly, float)
    d_dot_d = float(data @ data)
    d_mean = data.mean()
    ss_tot = float(((data - d_mean) ** 2).sum())

    rows = []
    for beta in beta_grid:
        for sigma in sigma_grid:
            for gamma in gamma_grid:
                for alpha in alpha_grid:
                    for i0 in i0_grid:
                        sim = DeterministicSurrogate(
                            population,
                            SEIRParams(beta_base=beta, sigma=sigma, gamma=gamma),
                            media_amplification=alpha,
                        ).run(num_days, i0=int(i0), e0=int(i0))
                        model_weekly = weekly_aggregate(sim['incidence'])
                        m_dot_m = float(model_weekly @ model_weekly)
                        if m_dot_m <= 0:
                            continue
                        rho = float(model_weekly @ data) / m_dot_m
                        if not (0.0 < rho <= 1.0):
                            continue  # 报告率必须落在 (0,1]
                        fitted = rho * model_weekly
                        rmse = float(np.sqrt(((fitted - data) ** 2).mean()))
                        ss_res = float(((fitted - data) ** 2).sum())
                        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
                        rows.append({
                            'beta': beta, 'sigma': sigma, 'gamma': gamma,
                            'media_amp': alpha, 'i0': i0, 'rho': rho,
                            'rmse': rmse, 'r2': r2, 'R0_human': beta / gamma,
                        })
    return pd.DataFrame(rows).sort_values('rmse').reset_index(drop=True)


def estimate_basic_reproduction_number(params: dict) -> float:
    """人类通道的基本再生数 R0 = beta / gamma（蚊媒通道未计入，见论文说明）。"""
    return params['beta'] / params['gamma']
