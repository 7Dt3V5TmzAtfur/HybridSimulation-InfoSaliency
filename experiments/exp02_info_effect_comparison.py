"""
实验2：信息效应定量对比
验证信息显著性对疫情控制的独立效应
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.hybrid_model import HybridEpidemicModel, SEIRParams, DESParams
from src.visualization import EpidemicVisualizer, generate_summary_statistics


def run_info_effect_experiment():
    """运行信息效应定量实验"""
    
    print("=" * 60)
    print("实验2：信息效应定量对比")
    print("=" * 60)
    
    np.random.seed(42)
    
    population_size = 1000
    num_days = 200
    num_runs = 10  # 多次运行取平均
    
    # 实验组：完整信息-行为耦合
    print(f"\n[实验组] 运行{num_runs}次仿真（信息-行为耦合）...")
    peaks_exp = []
    totals_exp = []
    
    for i in range(num_runs):
        model = HybridEpidemicModel(
            population_size=population_size,
            media_amplification=1.5,
            enable_info_behavior_feedback=True
        )
        model.seed_infection(num_initial=10)
        model.run(num_days=num_days)
        results = model.get_results()
        
        peaks_exp.append(results['I'].max())
        totals_exp.append(results['R'].iloc[-1])
    
    # 对照组：无行为反馈（防护水平固定为0）
    print(f"[对照组] 运行{num_runs}次仿真（无行为反馈）...")
    peaks_ctrl = []
    totals_ctrl = []
    
    for i in range(num_runs):
        model = HybridEpidemicModel(
            population_size=population_size,
            media_amplification=1.5,
            enable_info_behavior_feedback=False
        )
        model.seed_infection(num_initial=10)
        model.run(num_days=num_days)
        results = model.get_results()
        
        peaks_ctrl.append(results['I'].max())
        totals_ctrl.append(results['R'].iloc[-1])
    
    # 计算统计
    peak_exp_mean = np.mean(peaks_exp)
    peak_exp_std = np.std(peaks_exp)
    peak_ctrl_mean = np.mean(peaks_ctrl)
    peak_ctrl_std = np.std(peaks_ctrl)
    
    total_exp_mean = np.mean(totals_exp)
    total_exp_std = np.std(totals_exp)
    total_ctrl_mean = np.mean(totals_ctrl)
    total_ctrl_std = np.std(totals_ctrl)
    
    # 计算效应量
    peak_reduction = (peak_ctrl_mean - peak_exp_mean) / peak_ctrl_mean * 100
    total_reduction = (total_ctrl_mean - total_exp_mean) / total_ctrl_mean * 100
    
    print("\n" + "=" * 60)
    print("定量结果（均值±标准差）")
    print("=" * 60)
    print(f"{'指标':<20} {'实验组':<20} {'对照组':<20} {'效应量':<15}")
    print("-" * 75)
    print(f"{'峰值感染':<20} {peak_exp_mean:.1f}±{peak_exp_std:.1f}   {peak_ctrl_mean:.1f}±{peak_ctrl_std:.1f}   ↓{peak_reduction:.1f}%")
    print(f"{'总感染':<20} {total_exp_mean:.1f}±{total_exp_std:.1f}   {total_ctrl_mean:.1f}±{total_ctrl_std:.1f}   ↓{total_reduction:.1f}%")
    
    # 统计显著性检验
    from scipy import stats
    
    t_stat_peak, p_value_peak = stats.ttest_ind(peaks_exp, peaks_ctrl)
    t_stat_total, p_value_total = stats.ttest_ind(totals_exp, totals_ctrl)
    
    print("\n" + "=" * 60)
    print("统计检验（独立样本t检验）")
    print("=" * 60)
    print(f"峰值感染: t={t_stat_peak:.3f}, p={p_value_peak:.4f} {'***' if p_value_peak < 0.001 else '**' if p_value_peak < 0.01 else '*' if p_value_peak < 0.05 else 'ns'}")
    print(f"总感染:   t={t_stat_total:.3f}, p={p_value_total:.4f} {'***' if p_value_total < 0.001 else '**' if p_value_total < 0.01 else '*' if p_value_total < 0.05 else 'ns'}")
    
    # 可视化
    print("\n生成可视化图表...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 峰值感染箱线图
    ax1 = axes[0, 0]
    ax1.boxplot([peaks_exp, peaks_ctrl], labels=['With Feedback', 'Without Feedback'])
    ax1.set_ylabel('Peak Infected')
    ax1.set_title('Peak Infection Distribution')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. 总感染箱线图
    ax2 = axes[0, 1]
    ax2.boxplot([totals_exp, totals_ctrl], labels=['With Feedback', 'Without Feedback'])
    ax2.set_ylabel('Total Infected')
    ax2.set_title('Final Epidemic Size Distribution')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. 效应量柱状图
    ax3 = axes[1, 0]
    effects = [peak_reduction, total_reduction]
    labels = ['Peak Reduction', 'Total Reduction']
    colors = ['red', 'orange']
    bars = ax3.bar(labels, effects, color=colors, alpha=0.7)
    ax3.set_ylabel('Reduction (%)')
    ax3.set_title('Effect Size of Information-Behavior Feedback')
    ax3.axhline(y=20, color='green', linestyle='--', label='20% Threshold')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 添加数值标签
    for bar, effect in zip(bars, effects):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{effect:.1f}%', ha='center', va='bottom')
    
    # 4. 时间序列对比（单次运行）
    ax4 = axes[1, 1]
    model_exp = HybridEpidemicModel(
        population_size=population_size,
        media_amplification=1.5,
        enable_info_behavior_feedback=True
    )
    model_exp.seed_infection(num_initial=10)
    model_exp.run(num_days=num_days)
    results_exp = model_exp.get_results()
    
    model_ctrl = HybridEpidemicModel(
        population_size=population_size,
        media_amplification=1.5,
        enable_info_behavior_feedback=False
    )
    model_ctrl.seed_infection(num_initial=10)
    model_ctrl.run(num_days=num_days)
    results_ctrl = model_ctrl.get_results()
    
    dates = np.arange(num_days)
    ax4.plot(dates, results_exp['I'], label='With Feedback', color='blue', linewidth=2)
    ax4.plot(dates, results_ctrl['I'], label='Without Feedback', color='red', linewidth=2)
    ax4.set_xlabel('Day')
    ax4.set_ylabel('Infected Count')
    ax4.set_title('Infection Curves Comparison')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    os.makedirs('results', exist_ok=True)
    save_path = 'results/exp02_info_effect.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ 实验完成！图表已保存到: {save_path}")
    
    return {
        'peak_exp': peaks_exp,
        'peak_ctrl': peaks_ctrl,
        'total_exp': totals_exp,
        'total_ctrl': totals_ctrl,
        'peak_reduction': peak_reduction,
        'total_reduction': total_reduction,
        'p_value_peak': p_value_peak,
        'p_value_total': p_value_total
    }


if __name__ == "__main__":
    results = run_info_effect_experiment()
    
    print("\n" + "=" * 60)
    print("实验2完成")
    print("=" * 60)
