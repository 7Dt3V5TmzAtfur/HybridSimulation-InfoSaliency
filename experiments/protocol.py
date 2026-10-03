# -*- coding: utf-8 -*-
"""
实验再生协议（Regeneration Protocol）

所有实验脚本共用。约定：
- 每次运行独立种子：seed = BASE_SEED[exp] * 1000 + run_index
- 结果文件使用固定规范名（无版本后缀），历史版本由 git 管理
- 每次重跑将协议元数据写入 results/RUN_MANIFEST.yml
"""

import os
import subprocess
import sys
from datetime import datetime

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 各实验的基础种子（run_index 从 0 开始）
BASE_SEED = {
    'exp01': 101,
    'exp02': 202,
    'exp03': 303,
    'exp04': 404,
    'exp05': 505,
    'exp06': 606,
    'ablation': 707,
    'exp07': 808,
    'exp08': 909,
    'exp09': 1111,
    'exp10': 1212,
    'exp11': 1313,
}

# 全局共享配置
POPULATION_SIZE = 1000
NUM_DAYS = 200
NUM_INITIAL = 10  # 初始感染人数


def set_seed(exp: str, run_index: int):
    """按协议设置每次运行的独立种子。"""
    np.random.seed(BASE_SEED[exp] * 1000 + run_index)


def git_commit() -> str:
    """返回当前代码版本（git commit hash）。"""
    try:
        out = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return 'unknown(working-tree)'


def python_deps() -> dict:
    deps = {}
    for m in ('numpy', 'pandas', 'matplotlib', 'scipy'):
        try:
            mod = __import__(m)
            deps[m] = getattr(mod, '__version__', 'unknown')
        except ImportError:
            deps[m] = 'missing'
    return deps


def record_manifest(exp: str, description: str, config: dict, outputs: list):
    """把一次实验运行的协议元数据追加到 results/RUN_MANIFEST.yml。"""
    manifest_path = os.path.join(REPO_ROOT, 'results', 'RUN_MANIFEST.yml')
    lines = []
    if not os.path.exists(manifest_path):
        lines.append('# RUN_MANIFEST — 实验再生协议记录')
        lines.append('# 每次重跑追加一节；种子公式：seed = BASE_SEED[exp]*1000 + run_index')
        lines.append('# 本文件由 experiments/protocol.py 自动生成，请勿手改数字')
        lines.append('')
    lines.append(f'- experiment: {exp}')
    lines.append(f'  description: {description}')
    lines.append(f'  run_at: {datetime.now().isoformat(timespec="seconds")}')
    lines.append(f'  code_version: {git_commit()}')
    lines.append(f'  base_seed: {BASE_SEED[exp]}')
    lines.append(f'  seed_rule: BASE_SEED*1000 + run_index')
    for k, v in config.items():
        lines.append(f'  {k}: {v}')
    lines.append('  dependencies:')
    for k, v in python_deps().items():
        lines.append(f'    {k}: "{v}"')
    lines.append(f'  python: "{sys.version.split()[0]}"')
    lines.append('  outputs:')
    for o in outputs:
        lines.append(f'    - {o}')
    lines.append('')
    with open(manifest_path, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'[manifest] 已记录 {exp} -> results/RUN_MANIFEST.yml')
