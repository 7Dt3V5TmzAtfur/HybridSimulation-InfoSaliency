#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
归因审计脚本（Ablation-Attribution Analysis）
分析混合仿真模型中各组件对结果的贡献度

方法论：消融实验（Ablation Study）
- 逐个移除或禁用关键组件
- 对比结果变化
- 计算各组件的贡献度

作者：AI Research Assistant
日期：2026-09-28
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import numpy as np
import pandas as pd
from src.hybrid_model import HybridEpidemicModel, SEIRParams, DESParams
import matplotlib.pyplot as plt


def run_ablation_experiment(ablation_config: dict, population_size: int = 1000, 
                            n_days: int = 200, seed: int = 42) -> dict:
    """
    运行消融实验
    
    Args:
        ablation_config: 消融配置
        population_size: 人口数量
        n_days: 仿真天数
        seed: 随机种子
    
    Returns:
        实验结果字典
    """
    # 创建模型参数
    seir_params = SEIRParams(
        beta_base=0.3,
        sigma=0.2,
        gamma=0.1,
        hospitalization_rate=0.15,
        detection_rate=0.3
    )
    
    des_params = DESParams(
        hospital_beds=50,  # 减少床位，使资源约束生效
        icu_beds=10,       # 减少ICU床位
        testing_capacity=100,
        avg_hospital_stay=7,
        avg_icu_stay=14,
        test_result_time=1
    )
    
    # 确定是否启用信息-行为反馈
    enable_feedback = not ablation_config.get('disable_behavior_feedback', False)
    
    # 创建模型
    model = HybridEpidemicModel(
        population_size=population_size,
        seir_params=seir_params,
        des_params=des_params,
        media_amplification=1.5,
        enable_info_behavior_feedback=enable_feedback
    )
    
    # 应用消融配置
    if 'disable_info_saliency' in ablation_config and ablation_config['disable_info_saliency']:
        model.info_model.media_amplification = 0.0
    
    if 'disable_hospital_constraint' in ablation_config and ablation_config['disable_hospital_constraint']:
        # 移除医疗资源约束：无限床位
        model.hospital.params.hospital_beds = 100000
        model.hospital.params.icu_beds = 100000
    
    # 运行仿真
    np.random.seed(seed)
    model.seed_infection(5)
    model.run(num_days=n_days)
    
    # 获取结果
    results_df = model.get_results()
    
    # 提取关键指标
    infected_history = results_df['I'].tolist()
    peak_infected = max(infected_history)
    peak_day = infected_history.index(peak_infected)
    total_infected = results_df['R'].iloc[-1]
    
    protection_history = results_df['avg_protection'].tolist()
    peak_protection = max(protection_history)
    
    hospital_rejected = model.hospital.rejected_count
    
    return {
        'peak_infected': peak_infected,
        'peak_day': peak_day,
        'total_infected': total_infected,
        'peak_protection': peak_protection,
        'hospital_rejected': hospital_rejected,
        'results': results_df
    }


def compute_attribution(baseline_result: dict, ablation_result: dict, metric: str) -> float:
    """
    计算消融组件对特定指标的贡献度
    
    Args:
        baseline_result: 基线结果
        ablation_result: 消融结果
        metric: 指标名称
    
    Returns:
        贡献度（百分比）
    """
    baseline_value = baseline_result[metric]
    ablation_value = ablation_result[metric]
    
    if baseline_value == 0:
        return 0.0
    
    # 贡献度 = (基线值 - 消融值) / 基线值 * 100%
    attribution = (baseline_value - ablation_value) / baseline_value * 100
    
    return attribution


def main():
    """主函数"""
    print("=" * 80)
    print("归因审计（Ablation-Attribution Analysis）")
    print("=" * 80)
    print()
    
    # 定义消融实验配置
    ablation_configs = {
        'baseline': {},
        'no_info_saliency': {'disable_info_saliency': True},
        'no_behavior_feedback': {'disable_behavior_feedback': True},
        'no_hospital_constraint': {'disable_hospital_constraint': True}
    }
    
    # 运行所有消融实验
    results = {}
    for config_name, config in ablation_configs.items():
        print(f"运行实验: {config_name}")
        results[config_name] = run_ablation_experiment(config)
        print(f"  峰值感染: {results[config_name]['peak_infected']}")
        print(f"  峰值防护: {results[config_name]['peak_protection']:.3f}")
        print(f"  医疗拒绝: {results[config_name]['hospital_rejected']}")
        print()
    
    # 计算归因
    baseline = results['baseline']
    metrics = ['peak_infected', 'peak_protection', 'hospital_rejected']
    
    attribution_df = pd.DataFrame(index=ablation_configs.keys(), columns=metrics)
    
    for config_name in ablation_configs.keys():
        if config_name == 'baseline':
            continue
        
        for metric in metrics:
            attribution = compute_attribution(baseline, results[config_name], metric)
            attribution_df.loc[config_name, metric] = attribution
    
    # 填充基线行
    for metric in metrics:
        attribution_df.loc['baseline', metric] = 0.0
    
    print("=" * 80)
    print("归因分析结果（贡献度百分比）")
    print("=" * 80)
    print(attribution_df.to_string())
    print()
    
    # 保存结果
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    os.makedirs(output_dir, exist_ok=True)
    
    attribution_df.to_csv(os.path.join(output_dir, 'ablation_attribution.csv'))
    print(f"归因结果已保存到: {os.path.join(output_dir, 'ablation_attribution.csv')}")
    
    # 生成可视化
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 图1：峰值感染对比
    ax = axes[0, 0]
    config_names = list(results.keys())
    peak_infected_values = [results[c]['peak_infected'] for c in config_names]
    colors = ['#2ecc71' if c == 'baseline' else '#e74c3c' for c in config_names]
    ax.bar(config_names, peak_infected_values, color=colors)
    ax.set_ylabel('Peak Infected')
    ax.set_title('Peak Infected Comparison')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    
    # 图2：峰值防护对比
    ax = axes[0, 1]
    peak_protection_values = [results[c]['peak_protection'] for c in config_names]
    ax.bar(config_names, peak_protection_values, color=colors)
    ax.set_ylabel('Peak Protection Level')
    ax.set_title('Peak Protection Level Comparison')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    
    # 图3：医疗拒绝对比
    ax = axes[1, 0]
    hospital_rejected_values = [results[c]['hospital_rejected'] for c in config_names]
    ax.bar(config_names, hospital_rejected_values, color=colors)
    ax.set_ylabel('Hospital Rejected Count')
    ax.set_title('Hospital Rejected Count Comparison')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    
    # 图4：归因热力图
    ax = axes[1, 1]
    attribution_numeric = attribution_df.astype(float)
    im = ax.imshow(attribution_numeric.values, cmap='RdYlGn', aspect='auto')
    ax.set_xticks(range(len(attribution_numeric.columns)))
    ax.set_yticks(range(len(attribution_numeric.index)))
    ax.set_xticklabels(attribution_numeric.columns, rotation=45, ha='right')
    ax.set_yticklabels(attribution_numeric.index)
    ax.set_title('Attribution Heatmap (%)')
    
    # 添加数值标注
    for i in range(len(attribution_numeric.index)):
        for j in range(len(attribution_numeric.columns)):
            value = attribution_numeric.values[i, j]
            ax.text(j, i, f'{value:.1f}', ha='center', va='center', 
                   fontsize=9, color='black' if abs(value) < 50 else 'white')
    
    plt.colorbar(im, ax=ax, label='Attribution (%)')
    
    plt.tight_layout()
    
    # 保存可视化
    fig_path = os.path.join(output_dir, 'ablation_attribution.png')
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"可视化已保存到: {fig_path}")
    
    # 生成详细报告
    report_lines = []
    report_lines.append("# 归因审计报告（Ablation-Attribution Report）")
    report_lines.append("")
    report_lines.append("## 实验配置")
    report_lines.append("")
    report_lines.append(f"- 人口数量: 1000")
    report_lines.append(f"- 仿真天数: 200")
    report_lines.append(f"- 随机种子: 42")
    report_lines.append("")
    report_lines.append("## 消融实验配置")
    report_lines.append("")
    for config_name, config in ablation_configs.items():
        if config_name == 'baseline':
            report_lines.append(f"- **{config_name}**: 完整模型")
        else:
            desc = []
            if 'disable_info_saliency' in config:
                desc.append("禁用信息显著性")
            if 'disable_behavior_feedback' in config:
                desc.append("禁用行为反馈")
            if 'disable_hospital_constraint' in config:
                desc.append("移除医疗资源约束")
            if 'disable_risk_inertia' in config:
                desc.append("移除风险感知惯性")
            if 'disable_social_influence' in config:
                desc.append("移除社会影响")
            report_lines.append(f"- **{config_name}**: {', '.join(desc)}")
    report_lines.append("")
    report_lines.append("## 实验结果")
    report_lines.append("")
    report_lines.append("| 实验配置 | 峰值感染 | 峰值日 | 峰值防护 | 医疗拒绝 |")
    report_lines.append("|---------|---------|--------|---------|---------|")
    for config_name in config_names:
        r = results[config_name]
        report_lines.append(f"| {config_name} | {r['peak_infected']} | {r['peak_day']} | {r['peak_protection']:.3f} | {r['hospital_rejected']} |")
    report_lines.append("")
    report_lines.append("## 归因分析（贡献度百分比）")
    report_lines.append("")
    report_lines.append("解读说明：负值表示移除该组件后指标上升（该组件有效降低了指标），正值表示移除该组件后指标下降（该组件有效提升了指标）。")
    report_lines.append("")
    report_lines.append("| 实验配置 | 峰值感染 | 峰值防护 | 医疗拒绝 |")
    report_lines.append("|---------|---------|---------|---------|")
    for config_name in attribution_df.index:
        row = attribution_df.loc[config_name]
        report_lines.append(f"| {config_name} | {row['peak_infected']:.1f} | {row['peak_protection']:.1f} | {row['hospital_rejected']:.1f} |")
    report_lines.append("")
    report_lines.append("## 关键发现")
    report_lines.append("")
    
    # 分析关键发现
    info_saliency_attr = attribution_df.loc['no_info_saliency', 'peak_infected']
    behavior_attr = attribution_df.loc['no_behavior_feedback', 'peak_infected']
    hospital_attr = attribution_df.loc['no_hospital_constraint', 'hospital_rejected']
    
    report_lines.append(f"1. **信息显著性贡献**: 移除信息显著性后，峰值感染变化 {info_saliency_attr:.1f}%。")
    if abs(info_saliency_attr) > 10:
        report_lines.append(f"   - 信息显著性对峰值感染有显著影响（贡献度 {abs(info_saliency_attr):.1f}%）。")
    else:
        report_lines.append(f"   - 信息显著性对峰值感染影响有限（贡献度 {abs(info_saliency_attr):.1f}%）。")
    report_lines.append("")
    
    report_lines.append(f"2. **行为反馈贡献**: 移除行为反馈后，峰值感染变化 {behavior_attr:.1f}%。")
    if abs(behavior_attr) > 10:
        report_lines.append(f"   - 行为反馈对峰值感染有显著影响（贡献度 {abs(behavior_attr):.1f}%）。")
    else:
        report_lines.append(f"   - 行为反馈对峰值感染影响有限（贡献度 {abs(behavior_attr):.1f}%）。")
    report_lines.append("")
    
    report_lines.append(f"3. **医疗资源约束贡献**: 移除医疗资源约束后，医疗拒绝人数变化 {hospital_attr:.1f}%。")
    if hospital_attr > 0:
        report_lines.append(f"   - 医疗资源约束是医疗拒绝的主要原因（贡献度 {hospital_attr:.1f}%）。")
    else:
        report_lines.append(f"   - 医疗资源约束对医疗拒绝影响有限。")
    report_lines.append("")
    
    report_lines.append("## 结论")
    report_lines.append("")
    report_lines.append("归因审计揭示了混合仿真模型中各组件的相对重要性。这些信息可用于：")
    report_lines.append("1. 模型简化：移除贡献度低的组件以降低计算复杂度")
    report_lines.append("2. 参数校准：优先校准贡献度高的组件参数")
    report_lines.append("3. 政策干预：针对贡献度高的组件设计干预策略")
    report_lines.append("")
    
    # 保存报告
    report_path = os.path.join(output_dir, 'ablation_attribution_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f"详细报告已保存到: {report_path}")
    
    print()
    print("=" * 80)
    print("归因审计完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
