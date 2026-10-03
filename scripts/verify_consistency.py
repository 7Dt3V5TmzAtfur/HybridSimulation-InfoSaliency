# -*- coding: utf-8 -*-
"""
一致性校验（论文 ↔ 结果文件 ↔ RUN_MANIFEST ↔ 代码版本）

用途：机械防范"论文数字 / 结果 CSV / 代码版本"三者脱钩（本项目的实际病史）。
已安装为本地 pre-commit 钩子（.git/hooks/pre-commit）；也可手动运行：
    python scripts/verify_consistency.py

检查项：
1. 论文关键数字：从 results/*.csv 重算并与 docs/paper_main.md、README.md 逐项比对
2. RUN_MANIFEST：覆盖全部预期实验，且论文 §3.5.3 引用的生成哈希
   出现在 manifest 记录的 code_version 中
3. staged 变更触及 src/ 或 experiments/ 时：打印"按协议重跑"提醒
   （重跑在代码提交之后进行属正常流程，此处仅提醒，不阻断）

退出码：0=通过；1=数字不一致（提交应被拒绝）。
紧急旁路：git commit --no-verify（须在提交说明中注明原因）。
"""

import io
import os
import re
import subprocess
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = os.path.join(REPO, 'docs', 'paper_main.md')
README = os.path.join(REPO, 'README.md')
MANIFEST = os.path.join(REPO, 'results', 'RUN_MANIFEST.yml')

EXPECTED_EXPERIMENTS = ['exp01', 'exp02', 'exp03', 'exp04', 'exp05', 'exp06',
                        'exp07', 'exp08', 'ablation']

failures = []
warnings = []


def check(name: str, ok: bool, detail: str = ''):
    if ok:
        print(f'  PASS  {name}')
    else:
        print(f'  FAIL  {name}  {detail}')
        failures.append(f'{name} {detail}')


def text_of(path: str) -> str:
    return io.open(path, encoding='utf-8').read()


def main():
    print('=' * 70)
    print('一致性校验：论文 ↔ 结果文件 ↔ RUN_MANIFEST')
    print('=' * 70)

    paper = text_of(PAPER)

    # ---------- 1. 论文关键数字 ----------
    print('\n[1] 论文关键数字 vs 结果 CSV')

    s = pd.read_csv(os.path.join(REPO, 'results/exp02_statistics.csv'))
    r = s.iloc[0]
    check('exp02 峰值 142.55/222.35/35.89',
          abs(r.exp_mean - 142.55) < 0.01 and abs(r.ctrl_mean - 222.35) < 0.01
          and abs(r.reduction_pct - 35.89) < 0.01 and '35.89' in paper)
    check('exp02 d=-6.16', abs(r.cohens_d + 6.16) < 0.01)

    s = pd.read_csv(os.path.join(REPO, 'results/exp05_protection_decomposition.csv'))
    full = s[s.arm_label == 'full_model'].iloc[0]
    const = s[s.arm_label == 'constant_protection'].iloc[0]
    check('exp05 38.3/36.3/P*=0.3357',
          abs(full.peak_reduction_pct - 38.27) < 0.01
          and abs(const.peak_reduction_pct - 36.25) < 0.01
          and abs(const.protection - 0.3357) < 1e-3 and '0.3357' in paper)

    s = pd.read_csv(os.path.join(REPO, 'results/exp07_scale_validation.csv'))
    full7 = s[s.arm_label == 'full_model'].iloc[0]
    const7 = s[s.arm_label == 'constant_protection'].iloc[0]
    check('exp07 24.8/21.2/P*=0.3374',
          abs(full7.peak_reduction_pct - 24.8) < 0.05
          and abs(const7.peak_reduction_pct - 21.2) < 0.05
          and abs(const7.protection - 0.3374) < 1e-3 and '24.8' in paper)

    s = pd.read_csv(os.path.join(REPO, 'results/ablation_attribution.csv'), index_col=0)
    check('消融 +47.4/-3.2/-5.4/0.0',
          abs(s.loc['no_behavior_feedback', 'peak_infected_change_pct'] - 47.4) < 0.05
          and abs(s.loc['no_info_saliency', 'peak_infected_change_pct'] + 3.2) < 0.05
          and abs(s.loc['no_mosquito', 'peak_infected_change_pct'] + 5.4) < 0.05
          and abs(s.loc['no_hospital_constraint', 'peak_infected_change_pct']) < 0.05
          and '+47.4' in paper and '-5.4' in paper)

    s = pd.read_csv(os.path.join(REPO, 'results/exp04_calibration_results.csv'))
    r = s.iloc[0]
    check('exp04 R2=0.941/β=0.25/R0=2.50',
          abs(r.r2 - 0.941) < 0.0005 and abs(r.beta - 0.25) < 1e-9
          and abs(r.beta / r.gamma - 2.5) < 1e-9 and '0.941' in paper)

    ms = pd.read_csv(os.path.join(REPO, 'results/exp04_multiseason.csv'))
    ms['season'] = ms['season'].astype(str)
    r22 = ms[ms.season == '2022'].iloc[0]
    r17 = ms[ms.season == '2017'].iloc[0]
    check('多季节 2022=0.944 / 2017严苛=-0.097',
          abs(r22.strict_r2 - 0.944) < 0.0005 and abs(r17.strict_r2 + 0.097) < 0.0005
          and '0.944' in paper)

    e6 = pd.read_csv(os.path.join(REPO, 'results/exp06_behavior_sensitivity.csv'))
    p15 = e6[(e6.kappa == 1.5) & (e6.eta == 0.0)].iloc[0].peak_reduction_pct
    p05 = e6[(e6.kappa == 0.5) & (e6.eta == 0.0)].iloc[0].peak_reduction_pct
    check('exp06 κ=1.5/η=0=35.2 且 κ=0.5/η=0=46.5',
          abs(p15 - 35.2) < 0.05 and abs(p05 - 46.5) < 0.05
          and '35.2' in paper and '40%–48%' in paper)

    e8 = pd.read_csv(os.path.join(REPO, 'results/exp08_awareness_comparison.csv'), index_col=0)
    check('exp08 awareness动态49.3 / 本文动态33.2 / 边际22.5pp',
          abs(e8.loc['awareness_dynamic', 'peak_reduction_pct'] - 49.3) < 0.05
          and abs(e8.loc['ours_dynamic', 'peak_reduction_pct'] - 33.2) < 0.05
          and abs(e8.loc['awareness_dynamic', 'marginal_pp'] - 22.5) < 0.05
          and '+22.5' in paper)

    e1 = pd.read_csv(os.path.join(REPO, 'results/exp01_summary.csv'), index_col=0)
    delay = e1.loc['with_feedback', 'peak_day_mean'] - e1.loc['without_feedback', 'peak_day_mean']
    check('exp01 峰值延迟 18.5（论文无"18.6 天"）',
          abs(delay - 18.5) < 0.05 and '18.5 天' in paper and '18.6 天' not in paper)

    # ---------- 2. RUN_MANIFEST ----------
    print('\n[2] RUN_MANIFEST 覆盖与代码版本')
    man = text_of(MANIFEST) if os.path.exists(MANIFEST) else ''
    if not man:
        check('manifest 存在', False, 'results/RUN_MANIFEST.yml 缺失')
    else:
        entries = set(re.findall(r'^- experiment: (\S+)', man, re.M))
        check('覆盖全部实验', set(EXPECTED_EXPERIMENTS) <= entries,
              f'缺失: {set(EXPECTED_EXPERIMENTS) - entries}')
        versions = set(re.findall(r'^\s+code_version: (\S+)', man, re.M))
        m = re.search(r'提交 `([0-9a-f]{7,40})` 的代码上一次性生成', paper)
        if m:
            h = m.group(1)
            check('论文引用哈希 ∈ manifest 的 code_version',
                  any(v.startswith(h) for v in versions),
                  f'论文引用 {h}，manifest 记录 {sorted(versions)[:3]}')
        else:
            check('论文引用生成哈希', False, '§3.5.3 未找到"提交 `xxx` 的代码上一次性生成"')

    # ---------- 3. 代码变更提醒 ----------
    print('\n[3] 代码变更提醒')
    try:
        staged = subprocess.run(['git', 'diff', '--cached', '--name-only', 'HEAD'],
                                cwd=REPO, capture_output=True, text=True).stdout
    except Exception:
        staged = ''
    if any(p.startswith(('src/', 'experiments/')) for p in staged.splitlines()):
        warnings.append('staged 变更触及 src/ 或 experiments/ —— 按协议需在提交后'
                        '全量重跑并更新 RUN_MANIFEST（论文 §3.5.3 哈希随之更新）')
    for w in warnings:
        print(f'  WARN  {w}')

    print('\n' + '=' * 70)
    if failures:
        print(f'未通过 {len(failures)} 项 —— 请勿提交；先修复数字或按协议重新生成结果。')
        for f in failures:
            print(f'  - {f}')
        return 1
    print('全部通过。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
