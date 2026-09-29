#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修正文档中的错误数据
将旧数据（34.3%, 6.9%, 147.0, 223.9 等）修正为真实数据（47.86%, 16.83%, 111.25, 213.35 等）
"""

import os
import re

docs_dir = 'docs'

# 需要修正的数据映射
corrections = {
    # 实验2数据修正
    '34.3%': '47.86%',
    '6.9%': '16.83%',
    '147.0 ± 22.0': '111.25 ± 14.32',
    '223.9 ± 14.8': '213.35 ± 17.81',
    '901.8 ± 23.9': '785.05 ± 23.38',
    '968.2 ± 7.8': '943.90 ± 11.93',
    
    # 消融实验数据修正
    'baseline峰值感染=100': 'baseline峰值感染=126',
    'no_behavior_feedback峰值感染=230': 'no_behavior_feedback峰值感染=219',
    '从100升至230': '从126升至219',
    '从100到230': '从126到219',
    'baseline=100': 'baseline=126',
    'no_behavior_feedback=230': 'no_behavior_feedback=219',
}

# 修正所有markdown文件
modified_files = []
for filename in os.listdir(docs_dir):
    if filename.endswith('.md'):
        filepath = os.path.join(docs_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old, new in corrections.items():
            content = content.replace(old, new)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            modified_files.append(filename)
            print(f'[OK] 修正: {filename}')
        else:
            print(f'[-] 无需修正: {filename}')

print(f'\n文档修正完成，共修正 {len(modified_files)} 个文件')
