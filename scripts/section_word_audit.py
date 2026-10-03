# -*- coding: utf-8 -*-
"""按节统计稿件词数（诊断哪节薄）。"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, '..', 'Journal of Simulation', 'submission', 'manuscript.tex')

tex = io.open(TEX, encoding='utf-8').read()
body = tex[tex.index(r'\begin{document}'):]
secs = re.split(r'(\\(?:sub)*section\{[^}]*\})', body)
cur = 'front matter'
counts = {}
order = []
for part in secs:
    m = re.match(r'\\(sub)?section\{([^}]*)\}', part)
    if m:
        cur = ('  ' if m.group(1) else '') + m.group(2)[:58]
    t = re.sub(r'(?m)^%.*$', '', part)
    t = re.sub(r'\\begin\{(table|figure|equation|align)\*?\}.*?\\end\{\1\*?\}', ' ', t, flags=re.S)
    t = re.sub(r'\\cite\{[^}]*\}|\\ref\{[^}]*\}|\\label\{[^}]*\}', ' X ', t)
    t = re.sub(r'\\[a-zA-Z]+\*?', ' ', t)
    t = re.sub(r'[{}$&~^]', ' ', t)
    n = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-.%]*", t))
    if cur not in counts:
        order.append(cur)
        counts[cur] = 0
    counts[cur] += n
print('section words (excl. tables/figures/equations):')
for k in order:
    if counts[k] > 5:
        print(f'{counts[k]:5d}  {k}')
