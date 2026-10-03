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
    """F1: 四层混合仿真框架与耦合。"""
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.axis('off')
    boxes = [
        (0.06, 0.74, 'ABM layer', 'Individual agents (S/E/I/R)\nRisk perception -> protection\nStochastic state transitions', '#d5f5e3'),
        (0.53, 0.74, 'SD layer', 'SEIR dynamics\nInformation saliency S(t)\nRisk perception & inertia', '#d6eaf8'),
        (0.53, 0.10, 'DES layer', 'Beds / ICU queues\nDeferred admissions\nCapacity constraints', '#fdebd0'),
        (0.06, 0.10, 'Mosquito layer', 'Human-mosquito-human\nExtrinsic incubation period\nSeasonal factor (fixed)', '#fadbd8'),
    ]
    for x, y, title, body, color in boxes:
        ax.add_patch(plt.Rectangle((x, y), 0.40, 0.20, facecolor=color,
                                   edgecolor='black', linewidth=1.2))
        ax.text(x + 0.02, y + 0.155, title, fontsize=11, fontweight='bold')
        ax.text(x + 0.02, y + 0.035, body, fontsize=8.5, va='bottom')
    arrows = [
        ((0.46, 0.87), (0.53, 0.87), 'aggregate\nS/E/I/R, protection', 'right'),
        ((0.53, 0.79), (0.46, 0.79), 'saliency -> risk\nbeta_eff(t)', 'left'),
        ((0.26, 0.74), (0.26, 0.30), 'infection risk <-> infected mosquitoes', 'mid'),
        ((0.73, 0.74), (0.73, 0.30), 'admission requests /\nresource availability', 'mid'),
    ]
    for (x1, y1), (x2, y2), label, side in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='<->', linewidth=1.2))
        if side == 'right':
            ax.text(0.495, 0.90, label, fontsize=7.5, ha='center')
        elif side == 'left':
            ax.text(0.495, 0.715, label, fontsize=7.5, ha='center')
        elif side == 'mid':
            ax.text((x1 + x2) / 2 + (0.012 if x1 < 0.4 else -0.012), (y1 + y2) / 2,
                    label, fontsize=7.5, rotation=90, va='center',
                    ha='left' if x1 < 0.4 else 'right')
    ax.text(0.5, 0.985, 'Both transmission channels modulated by (1 - eps * P_avg)',
            fontsize=9, ha='center', style='italic')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
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
