"""更新所有文档，将旧的47.86%结果替换为34.3%"""
import os

def update_file(filepath, replacements):
    """更新文件中的文本"""
    if not os.path.exists(filepath):
        print(f"[FAIL] 文件不存在: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] 已更新: {filepath}")
        return True
    else:
        print(f"[SKIP] 无需更新: {filepath}")
        return False

# 定义替换规则
replacements = [
    # 峰值降低
    ('降低47.86%', '降低34.3%'),
    ('降低47.9%', '降低34.3%'),
    ('47.86%', '34.3%'),
    
    # p值和Cohen's d
    ('p=2.28×10⁻²¹', 'p<0.0001'),
    ('p=2.28e-21', 'p<0.0001'),
    ("Cohen's d=6.32", 'p<0.0001'),
    ('Cohen\'s d=6.32', 'p<0.0001'),
    
    # 总感染降低
    ('总感染降低16.83%', '总感染降低6.9%'),
    ('总感染降低16.8%', '总感染降低6.9%'),
    ('16.83%', '6.9%'),
    ('16.8%', '6.9%'),
    
    # p值和Cohen's d（总感染）
    ('p=4.89×10⁻²⁶', 'p=0.002'),
    ('p=4.89e-26', 'p=0.002'),
    ("Cohen's d=8.56", "Cohen's d=0.89"),
    ('Cohen\'s d=8.56', 'Cohen\'s d=0.89'),
    
    # 消融实验
    ('禁用后峰值上升130人', '禁用后峰值上升73.8%'),
    ('移除后峰值感染上升130人', '移除后峰值感染上升73.8%'),
    ('从100升至230', '从126升至219'),
    
    # 实验2详细数据
    ('111.25 ± 14.32', '147.0 ± 22.0'),
    ('213.35 ± 17.81', '223.9 ± 14.8'),
    ('785.05 ± 23.38', '901.8 ± 23.9'),
    ('943.90 ± 11.93', '968.2 ± 7.8'),
]

# 需要更新的文件（使用相对于脚本的路径）
files_to_update = [
    'docs/paper_main.md',
    'docs/experiments.md',
    'docs/discussion.md',
    'docs/conclusion.md',
    'FINAL_REPORT.md',
    'README.md',
]

print("=" * 70)
print("更新文档：将旧的47.86%结果替换为34.3%")
print("=" * 70)

updated_count = 0
for filepath in files_to_update:
    if update_file(filepath, replacements):
        updated_count += 1

print(f"\n{'=' * 70}")
print(f"更新完成: {updated_count}/{len(files_to_update)} 个文件已更新")
print(f"{'=' * 70}")
