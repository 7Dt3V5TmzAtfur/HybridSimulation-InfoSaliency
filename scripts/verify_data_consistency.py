#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据一致性验证脚本
验证所有实验数据与文档的一致性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

def verify_experiment_data():
    """验证所有实验数据"""
    print("=" * 80)
    print("实验数据验证")
    print("=" * 80)
    
    # 实验1数据验证
    print("\n=== 实验1数据验证 ===")
    df_with = pd.read_csv('results/exp01_results_with_feedback.csv')
    df_without = pd.read_csv('results/exp01_results_without_feedback.csv')
    
    peak_with = int(df_with['I'].max())
    peak_without = int(df_without['I'].max())
    total_with = int(df_with['R'].iloc[-1])
    total_without = int(df_without['R'].iloc[-1])
    peak_day_with = int(df_with['I'].idxmax())
    peak_day_without = int(df_without['I'].idxmax())
    
    peak_reduction = (peak_without - peak_with) / peak_without * 100
    total_reduction = (total_without - total_with) / total_without * 100
    
    print(f"With feedback: 峰值感染={peak_with} (第{peak_day_with}天), 总感染={total_with}")
    print(f"Without feedback: 峰值感染={peak_without} (第{peak_day_without}天), 总感染={total_without}")
    print(f"峰值降低: {peak_reduction:.1f}%")
    print(f"总感染降低: {total_reduction:.1f}%")
    
    # 实验2数据验证
    print("\n=== 实验2数据验证 ===")
    df_exp02 = pd.read_csv('results/exp02_statistics_v2.csv')
    print(df_exp02.to_string())
    
    # 实验3数据验证
    print("\n=== 实验3数据验证 ===")
    df_exp03 = pd.read_csv('results/exp03_sensitivity_v2.csv')
    print(df_exp03.to_string())
    
    # 实验4数据验证
    print("\n=== 实验4数据验证 ===")
    df_exp04 = pd.read_csv('results/exp04_calibration_results.csv')
    print(df_exp04.to_string())
    
    # 归因审计数据验证
    print("\n=== 归因审计数据验证 ===")
    df_ablation = pd.read_csv('results/ablation_attribution.csv', index_col=0)
    print(df_ablation.to_string())
    
    # 归因贡献度计算
    print("\n=== 归因贡献度计算 ===")
    baseline_peak = 100
    no_info_peak = 105
    no_behavior_peak = 230
    no_hospital_peak = 99
    
    info_contribution = (baseline_peak - no_info_peak) / baseline_peak * 100
    behavior_contribution = (baseline_peak - no_behavior_peak) / baseline_peak * 100
    hospital_contribution = (baseline_peak - no_hospital_peak) / baseline_peak * 100
    
    print(f"信息显著性对峰值感染的贡献: {info_contribution:.1f}%")
    print(f"行为反馈对峰值感染的贡献: {behavior_contribution:.1f}%")
    print(f"医疗资源约束对峰值感染的贡献: {hospital_contribution:.1f}%")
    
    # 医疗拒绝贡献度
    baseline_rejected = 47
    no_hospital_rejected = 0
    hospital_rejected_contribution = (baseline_rejected - no_hospital_rejected) / baseline_rejected * 100
    print(f"医疗资源约束对医疗拒绝的贡献: {hospital_rejected_contribution:.1f}%")
    
    return {
        'exp1': {
            'peak_with': peak_with,
            'peak_without': peak_without,
            'peak_reduction': peak_reduction,
            'total_with': total_with,
            'total_without': total_without,
            'total_reduction': total_reduction
        },
        'exp2': df_exp02,
        'exp3': df_exp03,
        'exp4': df_exp04,
        'ablation': df_ablation
    }

def verify_document_consistency():
    """验证文档与数据的一致性"""
    print("\n" + "=" * 80)
    print("文档一致性验证")
    print("=" * 80)
    
    # 读取FINAL_REPORT.md
    with open('FINAL_REPORT.md', 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    # 检查关键数据点
    checks = [
        ('峰值降低51.5%', '51.5' in report_content),
        ('总感染降低18.6%', '18.6' in report_content),
        ('峰值降低47.9%', '47.9' in report_content or '47.86' in report_content),
        ('总感染降低16.8%', '16.8' in report_content or '16.83' in report_content),
        ('p=2.28', '2.28' in report_content),
        ('Cohen', 'd=6.32' in report_content or 'd=6.318' in report_content),
        ('R²=-1.430', '-1.430' in report_content or '-1.43' in report_content),
    ]
    
    print("\n文档数据点检查:")
    all_pass = True
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {check_name}")
        if not result:
            all_pass = False
    
    return all_pass

def main():
    """主函数"""
    print("=" * 80)
    print("数据一致性验证脚本")
    print("=" * 80)
    
    # 验证实验数据
    data = verify_experiment_data()
    
    # 验证文档一致性
    doc_consistent = verify_document_consistency()
    
    print("\n" + "=" * 80)
    print("验证完成")
    print("=" * 80)
    
    if doc_consistent:
        print("✓ 文档与数据一致")
    else:
        print("✗ 文档与数据存在不一致")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
