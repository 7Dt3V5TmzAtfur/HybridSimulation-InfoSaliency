# -*- coding: utf-8 -*-
"""统计投稿稿正文词数（Interact/T&F 10,000 词限制口径）。"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, '..', 'Journal of Simulation', 'submission', 'manuscript.tex')

tex = io.open(TEX, encoding='utf-8').read()
body = tex[tex.index(r'\begin{abstract}'): tex.index(r'\appendix')]
body = re.sub(r'(?m)^%.*$', '', body)
body = re.sub(r'\\begin\{(table|figure)\*?\}.*?\\end\{\1\*?\}', ' TABLEFIG ', body, flags=re.S)
body = re.sub(r'\\(sub)?section\*?\{([^}]*)\}', lambda m: m.group(2), body)
body = re.sub(r'\\cite\{[^}]*\}', ' CITE ', body)
body = re.sub(r'\\ref\{[^}]*\}', ' REF ', body)
body = re.sub(r'\\[a-zA-Z]+\*?', ' ', body)
body = re.sub(r'[{}$&~^]', ' ', body)
words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-.%]*", body))

n_tables = tex.count(r'\begin{table}')
n_figs = tex.count(r'\begin{figure}')
abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.S).group(1)
abs_words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-.%]*", abstract))

est = words + n_figs * 250 + n_tables * 120
print(f'摘要词数: {abs_words} (限 200)')
print(f'正文词数（摘要至结论，不含图表内容）: {words}')
print(f'表 {n_tables} 张 + 图 {n_figs} 幅 → 含图表估算 ≈ {est} 词 (限 10,000)')
