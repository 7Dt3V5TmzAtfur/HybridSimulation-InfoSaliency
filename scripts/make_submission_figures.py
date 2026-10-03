# -*- coding: utf-8 -*-
"""生成 JOS 投稿图（300 dpi，英文标签）。数据源：results/*.csv。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, 'results')
OUT = os.path.join(REPO, 'Journal of Simulation', 'submission', 'figures')
os.makedirs(OUT, exist_ok=True)

C_CTRL = '#c0392b'
C_CONST = '#e67e22'
C_FULL = '#27ae60'


def fig_framework():
    """F1: four-layer hybrid simulation framework, vertical flow, mathtext."""
    fig, ax = plt.subplots(figsize=(8.2, 6.9))
    ax.axis('off')

    def box(x, y, w, h, title, body, color, title_fs=12.5, body_fs=9.2):
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color,
                                   edgecolor='black', linewidth=1.3))
        ax.text(x + w / 2, y + h - 0.016, title, fontsize=title_fs,
                fontweight='bold', ha='center', va='top')
        ax.text(x + w / 2, y + h - 0.052, body, fontsize=body_fs,
                ha='center', va='top', linespacing=1.5)

    def arrow(x, y1, y2):
        ax.annotate('', xy=(x, y2), xytext=(x, y1),
                    arrowprops=dict(arrowstyle='-|>', linewidth=1.7, color='black'))

    # ---- 顶部说明 ----
    ax.text(0.40, 0.992, 'Both transmission channels modulated by $(1-\\varepsilon\\,\\bar{P})$',
            fontsize=10.5, ha='center', va='top', style='italic')

    # ---- 层 1：SD ----
    box(0.16, 0.760, 0.52, 0.180, 'SD layer (information, behaviour)',
        r'saliency:  $S(t)=\mathrm{min}\left(1,\ (I/N)\,\alpha\,e^{-\lambda t/100}\right)$' + '\n'
        r'risk:  $R_i(t)=(1-\eta)\,R_{\mathrm{target}}+\eta\,R_i(t-1)$' + '\n'
        r'protection:  $P_i=\sigma\left(\kappa(R_i-\mu)\right),\ \ \bar{P}=\mathrm{mean}_i\,P_i$',
        '#d6eaf8')

    # ---- 层 2：ABM ----
    box(0.16, 0.470, 0.52, 0.130, 'ABM layer (individuals)',
        r'agents with states $S/E/I/R$' + '\n'
        r'stochastic transitions;  $\bar{P}$ enters both channels',
        '#d5f5e3')

    # ---- 层 3：蚊媒（左）与 DES（右）----
    box(0.005, 0.045, 0.375, 0.160, 'Mosquito layer',
        r'humans $\to E_m \to I_m \to$ humans' + '\n'
        r'incubation 10 d, lifespan 14 d' + '\n'
        r'$\mathrm{risk}_m = b\,p_{mh}\,(I_m/M)$',
        '#fadbd8')
    box(0.415, 0.045, 0.375, 0.160, 'DES layer (hospital)',
        r'beds / ICU / testing queues' + '\n'
        r'deferred admissions (counted once)' + '\n'
        r'capacity constraints',
        '#fdebd0')

    # ---- 右侧调制说明框 ----
    ax.text(0.895, 0.855,
            'modulation' + '\n'
            r'human: $\beta(1-\varepsilon\bar{P})\,I/N$' + '\n'
            r'mosquito: $\mathrm{risk}_m(1-\varepsilon\bar{P})$',
            fontsize=8.8, ha='center', va='center', linespacing=1.6,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#f2f4f4', edgecolor='gray'))

    # ---- SD <-> ABM ----
    arrow(0.32, 0.760, 0.600)
    ax.text(0.305, 0.680, r'saliency $S(t)$' + '\n' + r'risk targets $\downarrow$',
            fontsize=9, ha='right', va='center', linespacing=1.45)
    arrow(0.48, 0.600, 0.760)
    ax.text(0.495, 0.680, r'aggregate $(S,E,I,R)$' + '\n' + r'mean protection $\bar{P}$ $\uparrow$',
            fontsize=9, ha='left', va='center', linespacing=1.45)

    # ---- ABM <-> Mosquito ----
    arrow(0.10, 0.470, 0.205)
    ax.text(0.085, 0.3375, r'infected $I(t)$ $\downarrow$',
            fontsize=9, ha='right', va='center', linespacing=1.45)
    arrow(0.245, 0.205, 0.470)
    ax.text(0.262, 0.3375, r'$\mathrm{risk}_m$ $\uparrow$',
            fontsize=9, ha='left', va='center', linespacing=1.45)

    # ---- ABM <-> DES ----
    arrow(0.505, 0.470, 0.205)
    ax.text(0.490, 0.3375, r'admissions $\downarrow$',
            fontsize=9, ha='right', va='center', linespacing=1.45)
    arrow(0.665, 0.205, 0.470)
    ax.text(0.680, 0.3375, r'beds / ICU $\uparrow$',
            fontsize=9, ha='left', va='center', linespacing=1.45)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.savefig(os.path.join(OUT, 'fig1_framework.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(OUT, 'fig1_framework.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)


def fig_switch():
    """F2: 开关对比（exp02，均值±标准差轨迹）。"""
    n = 20
    curves = {}
    for arm, feedback in (('feedback', True), ('control', False)):
        arr = []
        for i in range(n):
            np.random.seed(202 * 1000 + i)
            from src.hybrid_model import HybridEpidemicModel
            m = HybridEpidemicModel(population_size=1000,
                                    media_amplification=1.0,
                                    enable_info_behavior_feedback=feedback,
                                    enable_mosquito_transmission=True)
            m.seed_infection(10)
            m.run(200)
            arr.append(m.get_results()['I'].to_numpy())
        curves[arm] = np.vstack(arr)
    days = np.arange(200)
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    for arm, color, label in (('feedback', C_FULL, 'Behavioural feedback (mean$\\pm$s.d.)'),
                              ('control', C_CTRL, 'Zero protection (mean$\\pm$s.d.)')):
        a = curves[arm]
        ax.plot(days, a.mean(axis=0), color=color, label=label)
        ax.fill_between(days, a.mean(axis=0) - a.std(axis=0),
                        a.mean(axis=0) + a.std(axis=0), color=color, alpha=0.2)
    ax.set_xlabel('Day'); ax.set_ylabel('Infectious individuals')
    ax.legend(frameon=False); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig2_switch.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(OUT, 'fig2_switch.png'), dpi=300)
    plt.close(fig)


def fig_decomposition():
    """F3: 分解对比（exp05 N=1000 vs exp07 N=10^4）。"""
    e5 = pd.read_csv(os.path.join(RES, 'exp05_protection_decomposition.csv'))
    e7 = pd.read_csv(os.path.join(RES, 'exp07_scale_validation.csv'))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=False)
    for ax, df, title in ((axes[0], e5, '(a) N = 1,000'),
                          (axes[1], e7, '(b) N = 10,000')):
        order = ('zero_protection', 'constant_protection', 'full_model')
        labels = ['Zero\nprotection', 'Constant\nprotection', 'Full\nmodel']
        vals = [df[df.arm_label == a].iloc[0].peak_mean for a in order]
        errs = [df[df.arm_label == a].iloc[0].peak_std for a in order]
        ax.bar(labels, vals, yerr=errs, capsize=4,
               color=[C_CTRL, C_CONST, C_FULL])
        for j, a in enumerate(order):
            r = df[df.arm_label == a].iloc[0]
            if a != 'zero_protection':
                ax.text(j, r.peak_mean + r.peak_std + max(vals) * 0.02,
                        f"-{r.peak_reduction_pct:.1f}%", ha='center', fontsize=9)
        ax.set_title(title); ax.grid(axis='y', alpha=0.3)
        ax.set_ylabel('Peak infectious individuals')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig3_decomposition.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(OUT, 'fig3_decomposition.png'), dpi=300)
    plt.close(fig)


def fig_calibration():
    """F4: 校准拟合 + 多季节外推。"""
    fit = pd.read_csv(os.path.join(RES, 'exp04_fit.csv'))
    ms = pd.read_csv(os.path.join(RES, 'exp04_multiseason.csv'))
    ms['season'] = ms['season'].astype(str)
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6))
    ax = axes[0]
    ax.bar(range(len(fit)), fit['data_cases'], color='#95a5a6', alpha=0.65,
           label='Reported weekly cases')
    ax.plot(range(len(fit)), fit['model_fitted_cases'], color=C_CTRL, linewidth=2,
            label='Fitted (grid-searched surrogate)')
    ax.set_xlabel('Week, 2019'); ax.set_ylabel('Weekly reported cases')
    ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.3)
    ax.set_title('(a) Calibration, Brazil 2019 ($R^2=0.941$)')
    ax = axes[1]
    ms = ms.sort_values('season')
    x = np.arange(len(ms))
    ax.bar(x - 0.2, ms['strict_r2'], width=0.4, label='Strict (frozen $I_0$)')
    ax.bar(x + 0.2, ms['loose_r2'], width=0.4, label='Loose (per-season $I_0$)')
    ax.axhline(0, color='black', linewidth=0.8)
    ax.axhline(0.941, color='gray', linestyle='--', linewidth=1)
    ax.text(len(ms) - 0.5, 0.97, '2019 in-sample', fontsize=8, ha='right')
    ax.set_xticks(x); ax.set_xticklabels(ms['season'], rotation=45)
    ax.set_ylabel('Out-of-sample $R^2$')
    ax.legend(frameon=False, fontsize=8); ax.grid(axis='y', alpha=0.3)
    ax.set_title('(b) Seasonal transfer, 2016-2023')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig4_calibration.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(OUT, 'fig4_calibration.png'), dpi=300)
    plt.close(fig)


def main():
    fig_framework()
    fig_switch()
    fig_decomposition()
    fig_calibration()
    print('figures ->', OUT)


if __name__ == '__main__':
    main()
