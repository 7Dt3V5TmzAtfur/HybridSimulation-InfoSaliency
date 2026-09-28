"""
可视化模块
生成论文级别的图表
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import seaborn as sns
from typing import List, Dict, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# 设置论文级别图表样式
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

sns.set_style("whitegrid")


class EpidemicVisualizer:
    """传染病仿真可视化器"""
    
    def __init__(self, results_df: pd.DataFrame, real_data: Optional[pd.DataFrame] = None):
        """
        初始化可视化器
        
        Args:
            results_df: 仿真结果DataFrame
            real_data: 真实数据DataFrame（可选）
        """
        self.results = results_df
        self.real_data = real_data
        
        # 创建日期索引
        if 'date' in results_df.columns:
            self.dates = pd.to_datetime(results_df['date'])
        else:
            self.dates = pd.date_range(start='2020-01-01', periods=len(results_df))
    
    def plot_epidemic_curves(self, save_path: str = None, show_info_effect: bool = True):
        """
        绘制流行病曲线
        
        Args:
            save_path: 保存路径
            show_info_effect: 是否显示信息显著性效应
        """
        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
        # 1. SEIR曲线
        ax1 = axes[0]
        ax1.plot(self.dates, self.results['S'], label='Susceptible', color='blue', linewidth=2)
        ax1.plot(self.dates, self.results['E'], label='Exposed', color='orange', linewidth=2)
        ax1.plot(self.dates, self.results['I'], label='Infected', color='red', linewidth=2)
        ax1.plot(self.dates, self.results['R'], label='Recovered', color='green', linewidth=2)
        
        if self.real_data is not None:
            real_dates = pd.to_datetime(self.real_data['date'])
            ax1.plot(real_dates, self.real_data['cases'], 'k--', label='Real Data', 
                    linewidth=2, alpha=0.7)
        
        ax1.set_ylabel('Population Count')
        ax1.set_title('SEIR Epidemic Curves')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        
        # 标注峰值
        peak_idx = self.results['I'].idxmax()
        peak_date = self.dates[peak_idx]
        peak_value = self.results['I'].max()
        ax1.axvline(peak_date, color='red', linestyle='--', alpha=0.5)
        ax1.annotate(f'Peak: {peak_value:.0f}', 
                    xy=(peak_date, peak_value),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7))
        
        # 2. 信息显著性与行为
        if show_info_effect:
            ax2 = axes[1]
            ax2.plot(self.dates, self.results['info_saliency'], 
                    label='Information Saliency', color='purple', linewidth=2)
            ax2.plot(self.dates, self.results['avg_risk'], 
                    label='Average Risk Perception', color='brown', linewidth=2)
            ax2.plot(self.dates, self.results['avg_protection'], 
                    label='Average Protection Level', color='cyan', linewidth=2)
            ax2.set_ylabel('Level [0, 1]')
            ax2.set_title('Information Saliency and Behavioral Response')
            ax2.legend(loc='upper right')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, 1.1)
        
        # 3. 医疗资源使用
        ax3 = axes[2]
        ax3.plot(self.dates, self.results['hospital_beds'], 
                label='Hospital Beds Occupied', color='darkred', linewidth=2)
        ax3.plot(self.dates, self.results['hospital_icu'], 
                label='ICU Beds Occupied', color='darkorange', linewidth=2)
        ax3.set_ylabel('Bed Count')
        ax3.set_xlabel('Date')
        ax3.set_title('Healthcare Resource Utilization')
        ax3.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        
        plt.show()
    
    def plot_comparison(self, results_list: List[pd.DataFrame], 
                       labels: List[str],
                       save_path: str = None):
        """
        绘制多场景对比图
        
        Args:
            results_list: 多个仿真结果列表
            labels: 场景标签列表
            save_path: 保存路径
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        colors = plt.cm.Set2(np.linspace(0, 1, len(results_list)))
        
        # 1. 感染曲线对比
        ax1 = axes[0, 0]
        for i, (results, label) in enumerate(zip(results_list, labels)):
            dates = pd.date_range(start='2020-01-01', periods=len(results))
            ax1.plot(dates, results['I'], label=label, color=colors[i], linewidth=2)
        ax1.set_ylabel('Infected Count')
        ax1.set_title('Infection Curves Comparison')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 峰值统计
        ax2 = axes[0, 1]
        peaks = [results['I'].max() for results in results_list]
        x = np.arange(len(labels))
        bars = ax2.bar(x, peaks, color=colors)
        ax2.set_ylabel('Peak Infected')
        ax2.set_title('Peak Infection Comparison')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, rotation=45)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar, peak in zip(bars, peaks):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{peak:.0f}', ha='center', va='bottom')
        
        # 3. 总感染人数
        ax3 = axes[1, 0]
        total_infected = [results['R'].iloc[-1] for results in results_list]
        bars = ax3.bar(x, total_infected, color=colors)
        ax3.set_ylabel('Total Infected')
        ax3.set_title('Final Epidemic Size')
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, rotation=45)
        ax3.grid(True, alpha=0.3, axis='y')
        
        for bar, total in zip(bars, total_infected):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{total:.0f}', ha='center', va='bottom')
        
        # 4. 防护水平对比
        ax4 = axes[1, 1]
        for i, (results, label) in enumerate(zip(results_list, labels)):
            dates = pd.date_range(start='2020-01-01', periods=len(results))
            ax4.plot(dates, results['avg_protection'], label=label, 
                    color=colors[i], linewidth=2)
        ax4.set_ylabel('Protection Level')
        ax4.set_xlabel('Date')
        ax4.set_title('Behavioral Response Comparison')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 1.1)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"对比图已保存到: {save_path}")
        
        plt.show()
    
    def plot_parameter_sensitivity(self, param_name: str, param_values: List[float],
                                  results_list: List[pd.DataFrame],
                                  save_path: str = None):
        """
        绘制参数敏感性分析图
        
        Args:
            param_name: 参数名称
            param_values: 参数值列表
            results_list: 对应的仿真结果列表
            save_path: 保存路径
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 提取关键指标
        peaks = [results['I'].max() for results in results_list]
        totals = [results['R'].iloc[-1] for results in results_list]
        peak_days = [results['I'].idxmax() for results in results_list]
        max_protection = [results['avg_protection'].max() for results in results_list]
        
        # 1. 峰值感染 vs 参数
        ax1 = axes[0, 0]
        ax1.plot(param_values, peaks, 'o-', linewidth=2, markersize=8)
        ax1.set_xlabel(param_name)
        ax1.set_ylabel('Peak Infected')
        ax1.set_title(f'Peak Infection vs {param_name}')
        ax1.grid(True, alpha=0.3)
        
        # 2. 总感染 vs 参数
        ax2 = axes[0, 1]
        ax2.plot(param_values, totals, 's-', linewidth=2, markersize=8, color='orange')
        ax2.set_xlabel(param_name)
        ax2.set_ylabel('Total Infected')
        ax2.set_title(f'Final Size vs {param_name}')
        ax2.grid(True, alpha=0.3)
        
        # 3. 峰值日 vs 参数
        ax3 = axes[1, 0]
        ax3.plot(param_values, peak_days, '^-', linewidth=2, markersize=8, color='green')
        ax3.set_xlabel(param_name)
        ax3.set_ylabel('Peak Day')
        ax3.set_title(f'Peak Timing vs {param_name}')
        ax3.grid(True, alpha=0.3)
        
        # 4. 最大防护水平 vs 参数
        ax4 = axes[1, 1]
        ax4.plot(param_values, max_protection, 'D-', linewidth=2, markersize=8, color='purple')
        ax4.set_xlabel(param_name)
        ax4.set_ylabel('Max Protection Level')
        ax4.set_title(f'Max Protection vs {param_name}')
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 1.1)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"敏感性分析图已保存到: {save_path}")
        
        plt.show()
    
    def plot_heatmap_analysis(self, results_df: pd.DataFrame, save_path: str = None):
        """
        绘制热力图分析（时间-状态矩阵）
        
        Args:
            results_df: 仿真结果
            save_path: 保存路径
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 创建时间-状态矩阵
        states = ['S', 'E', 'I', 'R']
        data_matrix = results_df[states].T.values
        
        # 归一化
        data_normalized = data_matrix / data_matrix.sum(axis=0, keepdims=True)
        
        # 绘制热力图
        im = ax.imshow(data_normalized, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        
        ax.set_xlabel('Time Step')
        ax.set_ylabel('Epidemic State')
        ax.set_yticks(range(len(states)))
        ax.set_yticklabels(states)
        ax.set_title('State Distribution Over Time (Normalized)')
        
        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Proportion')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"热力图已保存到: {save_path}")
        
        plt.show()


def generate_summary_statistics(results_df: pd.DataFrame) -> Dict:
    """
    生成汇总统计
    
    Args:
        results_df: 仿真结果
    
    Returns:
        统计字典
    """
    stats = {
        'peak_infected': results_df['I'].max(),
        'peak_day': results_df['I'].idxmax(),
        'total_infected': results_df['R'].iloc[-1],
        'attack_rate': results_df['R'].iloc[-1] / len(results_df),
        'max_protection': results_df['avg_protection'].max(),
        'max_info_saliency': results_df['info_saliency'].max(),
        'max_hospital_beds': results_df['hospital_beds'].max(),
        'max_icu_beds': results_df['hospital_icu'].max(),
        'total_rejected': results_df['rejected'].iloc[-1]
    }
    
    return stats


if __name__ == "__main__":
    # 测试可视化
    from src.hybrid_model import HybridEpidemicModel
    
    print("运行测试仿真...")
    model = HybridEpidemicModel(population_size=10000)
    model.seed_infection(num_initial=10)
    model.run(num_days=200)
    
    results = model.get_results()
    
    print("\n生成可视化图表...")
    viz = EpidemicVisualizer(results)
    viz.plot_epidemic_curves(save_path='test_epidemic_curves.png')
    
    stats = generate_summary_statistics(results)
    print("\n汇总统计:")
    for key, value in stats.items():
        print(f"  {key}: {value:.2f}")
