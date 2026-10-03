# -*- coding: utf-8 -*-
"""摘要最后两处微调（-3 词 -> 199）。"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'Journal of Simulation', 'submission', 'manuscript.tex')

s = io.open(P, encoding='utf-8').read()
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', s, re.S)
a = m.group(1)
subs = [
 ("which confounds the contribution of protective-behaviour level with that of its dynamics",
  "which confounds the contributions of protective-behaviour level and dynamics"),
 ("and a population-scale replication", "and a scale replication"),
]
for old, new in subs:
    assert old in a, old[:50]
    a = a.replace(old, new)
s = s[:m.start(1)] + a + s[m.end(1):]
io.open(P, 'w', encoding='utf-8').write(s)
n = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-.%]*", a))
print('abstract words now (strict counter):', n)
