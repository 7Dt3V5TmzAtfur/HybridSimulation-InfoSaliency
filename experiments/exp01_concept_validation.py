"""
实验1：概念验证
验证信息显著性驱动的混合仿真框架可行性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.hybrid_model import HybridEpidemicModel, SEIRParams, DESParams
from src.visualization import EpidemicVisualizer, generate_summary_statistics


def run_concept_validation():
    """运行概念验证实验"""
    
    print("=" * 60)
    print("实验1：概念验证")
    print("=" * 60)
    
    # 设置随机种子
    np.random.seed(42)
    
    # 参数设置
    population_size = 1000
    num_days = 200
    
    # 创建模型（启用信息-行为反馈）
    print("\n[1/3] 创建混合仿真模型...")
    model = HybridEpidemicModel(
        population_size=population_size,
        seir_params=SEIRParams(
            beta_base=0.3,
            sigma=0.2,
            gamma=0.1,
            hospitalization_rate=0.15,
            detection_rate=0.3
        ),
        des_params=DESParams(
            hospital_beds=200,
            icu_beds=50,
            testing_capacity=100
        ),
        media_amplification=1.5,
        enable_info_behavior_feedback=True
    )
    
    # 种子感染
    print("[2/3] 种子感染（初始10人）...")
    model.seed_infection(num_initial=10)
    
    # 运行仿真
    print(f"[3/3] 运行仿真（{num_days}天）...")
    model.run(num_days=num_days)
    
    # 获取结果
    results = model.get_results()
    
    # 生成统计
    stats = generate_summary_statistics(results)
    
    print("\n" + "=" * 60)
    print("实验结果")
    print("=" * 60)
    print(f"峰值感染人数: {stats['peak_infected']:.0f}")
    print(f"峰值出现日期: 第{stats['peak_day']}天")
    print(f"总感染人数: {stats['total_infected']:.0f} ({stats['attack_rate']*100:.1f}%)")
    print(f"最大防护水平: {stats['max_protection']:.3f}")
    print(f"最大信息显著性: {stats['max_info_saliency']:.3f}")
    print(f"最大医院床位使用: {stats['max_hospital_beds']:.0f}")
    print(f"最大ICU床位使用: {stats['max_icu_beds']:.0f}")
    print(f"被拒绝入院次数: {stats['total_rejected']:.0f}")
    
    # 可视化
    print("\n生成可视化图表...")
    viz = EpidemicVisualizer(results)
    
    # 保存图表
    os.makedirs('results', exist_ok=True)
    save_path = 'results/exp01_concept_validation.png'
    viz.plot_epidemic_curves(save_path=save_path, show_info_effect=True)
    
    print(f"\n✅ 实验完成！图表已保存到: {save_path}")
    
    return results, stats


def run_comparison_experiment():
    """运行对比实验：有/无信息-行为反馈"""
    
    print("\n" + "=" * 60)
    print("对比实验：信息-行为反馈效应")
    print("=" * 60)
    
    np.random.seed(42)
    
    population_size = 1000
    num_days = 200
    
    # 实验组：启用信息-行为反馈
    print("\n[实验组] 启用信息-行为反馈...")
    model_exp = HybridEpidemicModel(
        population_size=population_size,
        media_amplification=1.5,
        enable_info_behavior_feedback=True
    )
    model_exp.seed_infection(num_initial=10)
    model_exp.run(num_days=num_days)
    results_exp = model_exp.get_results()
    
    # 对照组：禁用信息-行为反馈
    print("[对照组] 禁用信息-行为反馈...")
    model_ctrl = HybridEpidemicModel(
        population_size=population_size,
        media_amplification=1.5,
        enable_info_behavior_feedback=False
    )
    model_ctrl.seed_infection(num_initial=10)
    model_ctrl.run(num_days=num_days)
    results_ctrl = model_ctrl.get_results()
    
    # 计算效应量
    peak_exp = results_exp['I'].max()
    peak_ctrl = results_ctrl['I'].max()
    peak_reduction = (peak_ctrl - peak_exp) / peak_ctrl * 100
    
    total_exp = results_exp['R'].iloc[-1]
    total_ctrl = results_ctrl['R'].iloc[-1]
    total_reduction = (total_ctrl - total_exp) / total_ctrl * 100
    
    print("\n" + "=" * 60)
    print("对比结果")
    print("=" * 60)
    print(f"{'指标':<20} {'实验组':<15} {'对照组':<15} {'效应量':<15}")
    print("-" * 60)
    print(f"{'峰值感染':<20} {peak_exp:<15.0f} {peak_ctrl:<15.0f} ↓{peak_reduction:.1f}%")
    print(f"{'总感染':<20} {total_exp:<15.0f} {total_ctrl:<15.0f} ↓{total_reduction:.1f}%")
    print(f"{'峰值防护水平':<20} {results_exp['avg_protection'].max():<15.3f} {results_ctrl['avg_protection'].max():<15.3f} -")
    
    # 可视化对比
    print("\n生成对比图表...")
    viz = EpidemicVisualizer(results_exp)
    
    os.makedirs('results', exist_ok=True)
    save_path = 'results/exp01_comparison.png'
    viz.plot_comparison(
        results_list=[results_exp, results_ctrl],
        labels=['With Info-Behavior Feedback', 'Without Info-Behavior Feedback'],
        save_path=save_path
    )
    
    print(f"\n✅ 对比实验完成！图表已保存到: {save_path}")
    
    return results_exp, results_ctrl


if __name__ == "__main__":
    # 运行概念验证
    results, stats = run_concept_validation()
    
    # 运行对比实验
    results_exp, results_ctrl = run_comparison_experiment()
    
    print("\n" + "=" * 60)
    print("实验1完成")
    print("=" * 60)
