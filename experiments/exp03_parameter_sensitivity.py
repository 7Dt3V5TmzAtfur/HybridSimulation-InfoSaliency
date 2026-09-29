"""
实验3：参数敏感性分析
分析媒体放大系数对疫情控制效果的影响
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.hybrid_model import HybridEpidemicModel, SEIRParams, DESParams
from src.visualization import EpidemicVisualizer


def run_parameter_sensitivity():
    """运行参数敏感性分析"""
    
    print("=" * 60)
    print("实验3：参数敏感性分析")
    print("=" * 60)
    
    np.random.seed(42)
    
    population_size = 1000
    num_days = 200
    
    # 测试不同的媒体放大系数
    media_amplifications = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
    
    print(f"\n测试媒体放大系数: {media_amplifications}")
    print(f"每个参数运行10次仿真取平均\n")
    
    results_list = []
    peaks_list = []
    totals_list = []
    peak_days_list = []
    max_protections_list = []
    
    for media_amp in media_amplifications:
        print(f"媒体放大系数 = {media_amp}...", end=' ')
        
        peaks = []
        totals = []
        peak_days = []
        max_protections = []
        
        for i in range(10):
            model = HybridEpidemicModel(
                population_size=population_size,
                media_amplification=media_amp,
                enable_info_behavior_feedback=True
            )
            model.seed_infection(num_initial=10)
            model.run(num_days=num_days)
            results = model.get_results()
            
            peaks.append(results['I'].max())
            totals.append(results['R'].iloc[-1])
            peak_days.append(results['I'].idxmax())
            max_protections.append(results['avg_protection'].max())
        
        peaks_mean = np.mean(peaks)
        totals_mean = np.mean(totals)
        peak_days_mean = np.mean(peak_days)
        max_protections_mean = np.mean(max_protections)
        
        peaks_list.append(peaks_mean)
        totals_list.append(totals_mean)
        peak_days_list.append(peak_days_mean)
        max_protections_list.append(max_protections_mean)
        
        print(f"峰值={peaks_mean:.1f}, 总感染={totals_mean:.1f}")
        
        # 保存最后一次运行的结果用于可视化
        results_list.append(results)
    
    # 计算相对于baseline（media_amp=0.5）的降低
    baseline_peak = peaks_list[0]
    baseline_total = totals_list[0]
    
    peak_reductions = [(baseline_peak - p) / baseline_peak * 100 for p in peaks_list]
    total_reductions = [(baseline_total - t) / baseline_total * 100 for t in totals_list]
    
    print("\n" + "=" * 60)
    print("敏感性分析结果")
    print("=" * 60)
    print(f"{'媒体放大':<12} {'峰值感染':<12} {'峰值降低':<12} {'总感染':<12} {'总感染降低':<12} {'峰值日':<12} {'最大防护':<12}")
    print("-" * 84)
    
    for i, media_amp in enumerate(media_amplifications):
        print(f"{media_amp:<12.1f} {peaks_list[i]:<12.1f} {peak_reductions[i]:<12.1f}% {totals_list[i]:<12.1f} {total_reductions[i]:<12.1f}% {peak_days_list[i]:<12.1f} {max_protections_list[i]:<12.3f}")
    
    # 可视化
    print("\n生成可视化图表...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 峰值感染 vs 媒体放大
    ax1 = axes[0, 0]
    ax1.plot(media_amplifications, peaks_list, 'o-', linewidth=2, markersize=8, color='red')
    ax1.set_xlabel('Media Amplification Factor')
    ax1.set_ylabel('Peak Infected')
    ax1.set_title('Peak Infection vs Media Amplification')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    
    # 2. 峰值降低 vs 媒体放大
    ax2 = axes[0, 1]
    ax2.plot(media_amplifications, peak_reductions, 's-', linewidth=2, markersize=8, color='orange')
    ax2.axhline(y=20, color='green', linestyle='--', label='20% Threshold')
    ax2.set_xlabel('Media Amplification Factor')
    ax2.set_ylabel('Peak Reduction (%)')
    ax2.set_title('Peak Reduction vs Media Amplification')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    
    # 3. 总感染 vs 媒体放大
    ax3 = axes[1, 0]
    ax3.plot(media_amplifications, totals_list, '^-', linewidth=2, markersize=8, color='blue')
    ax3.set_xlabel('Media Amplification Factor')
    ax3.set_ylabel('Total Infected')
    ax3.set_title('Final Epidemic Size vs Media Amplification')
    ax3.grid(True, alpha=0.3)
    ax3.set_xscale('log')
    
    # 4. 最大防护水平 vs 媒体放大
    ax4 = axes[1, 1]
    ax4.plot(media_amplifications, max_protections_list, 'D-', linewidth=2, markersize=8, color='purple')
    ax4.set_xlabel('Media Amplification Factor')
    ax4.set_ylabel('Max Protection Level')
    ax4.set_title('Max Protection Level vs Media Amplification')
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 1.1)
    ax4.set_xscale('log')
    
    plt.tight_layout()
    
    os.makedirs('results', exist_ok=True)
    save_path = 'results/exp03_parameter_sensitivity.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n[OK] 实验完成！图表已保存到: {save_path}")
    
    # 生成综合对比图
    print("\n生成综合对比图...")
    
    viz = EpidemicVisualizer(results_list[0])
    save_path2 = 'results/exp03_scenario_comparison.png'
    viz.plot_comparison(
        results_list=results_list,
        labels=[f'media_amp={m}' for m in media_amplifications],
        save_path=save_path2
    )
    print(f"综合对比图已保存到: {save_path2}")
    
    return {
        'media_amplifications': media_amplifications,
        'peaks': peaks_list,
        'totals': totals_list,
        'peak_days': peak_days_list,
        'max_protections': max_protections_list,
        'peak_reductions': peak_reductions,
        'total_reductions': total_reductions
    }


def run_threshold_analysis():
    """运行阈值分析：确定20%效应量的临界媒体放大系数"""
    
    print("\n" + "=" * 60)
    print("阈值分析：确定20%效应量的临界值")
    print("=" * 60)
    
    np.random.seed(42)
    
    population_size = 1000
    num_days = 200
    
    # 精细搜索
    media_amplifications = np.linspace(0.5, 3.0, 20)
    
    peaks_list = []
    
    for media_amp in media_amplifications:
        peaks = []
        for i in range(5):
            model = HybridEpidemicModel(
                population_size=population_size,
                media_amplification=media_amp,
                enable_info_behavior_feedback=True
            )
            model.seed_infection(num_initial=10)
            model.run(num_days=num_days)
            results = model.get_results()
            peaks.append(results['I'].max())
        
        peaks_list.append(np.mean(peaks))
    
    # 计算相对于baseline的降低
    baseline_peak = peaks_list[0]
    peak_reductions = [(baseline_peak - p) / baseline_peak * 100 for p in peaks_list]
    
    # 找到20%阈值的临界值
    threshold_idx = None
    for i, reduction in enumerate(peak_reductions):
        if reduction >= 20:
            threshold_idx = i
            break
    
    if threshold_idx is not None:
        threshold_value = media_amplifications[threshold_idx]
        print(f"\n[OK] 达到20%效应量的临界媒体放大系数: {threshold_value:.3f}")
        print(f"   对应峰值降低: {peak_reductions[threshold_idx]:.1f}%")
    else:
        print("\n[FAIL] 在测试范围内未达到20%效应量")
    
    # 可视化
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(media_amplifications, peak_reductions, 'o-', linewidth=2, markersize=6)
    ax.axhline(y=20, color='red', linestyle='--', linewidth=2, label='20% Threshold')
    
    if threshold_idx is not None:
        ax.axvline(x=threshold_value, color='green', linestyle='--', linewidth=2, 
                  label=f'Critical Value: {threshold_value:.2f}')
        ax.plot(threshold_value, 20, 'ro', markersize=12, zorder=5)
    
    ax.set_xlabel('Media Amplification Factor', fontsize=12)
    ax.set_ylabel('Peak Reduction (%)', fontsize=12)
    ax.set_title('Threshold Analysis: Critical Media Amplification for 20% Effect', fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    os.makedirs('results', exist_ok=True)
    save_path = 'results/exp03_threshold_analysis.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n阈值分析图已保存到: {save_path}")
    
    return threshold_value if threshold_idx is not None else None


if __name__ == "__main__":
    # 运行敏感性分析
    sensitivity_results = run_parameter_sensitivity()
    
    # 运行阈值分析
    threshold = run_threshold_analysis()
    
    print("\n" + "=" * 60)
    print("实验3完成")
    print("=" * 60)
