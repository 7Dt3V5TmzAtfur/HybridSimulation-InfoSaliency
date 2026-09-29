"""
实验4：登革热数据校准
使用真实登革热数据校准模型参数
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
from src.data_loader import DengueDataLoader, create_synthetic_dengue_data
from src.calibration import ModelCalibrator, estimate_basic_reproduction_number
from src.visualization import EpidemicVisualizer


def run_dengue_calibration_with_synthetic_data():
    """使用合成数据演示校准流程"""
    
    print("=" * 60)
    print("实验4：登革热数据校准（合成数据演示）")
    print("=" * 60)
    
    # 生成合成登革热数据（减少人口规模以加速校准）
    print("\n[1/4] 生成合成登革热数据...")
    real_data = create_synthetic_dengue_data(
        num_days=365,  # 1年（减少天数）
        population=5000,  # 减少人口规模
        peak_month=3,
        seasonality=0.8
    )
    
    print(f"数据形状: {real_data.shape}")
    print(f"时间范围: {real_data['date'].min()} 到 {real_data['date'].max()}")
    print(f"总病例数: {real_data['cases'].sum():,}")
    print(f"峰值病例: {real_data['cases'].max():,}")
    
    # 保存合成数据
    os.makedirs('data', exist_ok=True)
    real_data.to_csv('data/synthetic_dengue_calibration.csv', index=False)
    print(f"\n合成数据已保存到: data/synthetic_dengue_calibration.csv")
    
    # 创建校准器
    print("\n[2/4] 创建模型校准器...")
    population = 5000
    calibrator = ModelCalibrator(real_data, population=population)
    
    # 校准参数
    print("\n[3/4] 开始参数校准...")
    initial_params = np.array([0.3, 0.2, 0.1, 1.0])
    optimal_params, min_error = calibrator.calibrate(initial_params=initial_params)
    
    # 验证模型
    print("\n[4/4] 验证模型...")
    validation_results = calibrator.validate(optimal_params, test_ratio=0.2)
    
    # 计算R0
    R0 = estimate_basic_reproduction_number(optimal_params)
    print(f"\n基本再生数 R0: {R0:.2f}")
    
    # 使用最优参数运行完整仿真
    print("\n使用最优参数运行完整仿真...")
    seir_params = SEIRParams(
        beta_base=optimal_params[0],
        sigma=optimal_params[1],
        gamma=optimal_params[2]
    )
    
    model = HybridEpidemicModel(
        population_size=population,
        seir_params=seir_params,
        media_amplification=optimal_params[3],
        enable_info_behavior_feedback=True
    )
    model.seed_infection(num_initial=10)
    model.run(num_days=len(real_data))
    
    results = model.get_results()
    
    # 可视化
    print("\n生成可视化图表...")
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    
    # 1. 病例数对比
    ax1 = axes[0]
    dates = pd.to_datetime(real_data['date'])
    ax1.plot(dates, real_data['cases'], 'k-', label='Real Data', linewidth=2, alpha=0.7)
    ax1.plot(dates, results['I'], 'r-', label='Simulated', linewidth=2)
    ax1.set_ylabel('Daily Cases')
    ax1.set_title('Dengue Cases: Real vs Simulated')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 标注拟合指标
    ax1.text(0.02, 0.95, f'RMSE: {min_error:.1f}\nR2 (train): {validation_results["train_r2"]:.3f}\nR2 (test): {validation_results["test_r2"]:.3f}',
            transform=ax1.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 2. 信息显著性与行为
    ax2 = axes[1]
    ax2.plot(dates, results['info_saliency'], label='Information Saliency', color='purple', linewidth=2)
    ax2.plot(dates, results['avg_risk'], label='Risk Perception', color='brown', linewidth=2)
    ax2.plot(dates, results['avg_protection'], label='Protection Level', color='cyan', linewidth=2)
    ax2.set_ylabel('Level [0, 1]')
    ax2.set_title('Information and Behavioral Dynamics')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1.1)
    
    # 3. 医疗资源使用
    ax3 = axes[2]
    ax3.plot(dates, results['hospital_beds'], label='Hospital Beds', color='darkred', linewidth=2)
    ax3.plot(dates, results['hospital_icu'], label='ICU Beds', color='darkorange', linewidth=2)
    ax3.set_ylabel('Bed Count')
    ax3.set_xlabel('Date')
    ax3.set_title('Healthcare Resource Utilization')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    os.makedirs('results', exist_ok=True)
    save_path = 'results/exp04_dengue_calibration.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n[OK] 实验完成！图表已保存到: {save_path}")
    
    # 输出校准结果
    print("\n" + "=" * 60)
    print("校准结果汇总")
    print("=" * 60)
    print(f"最优参数:")
    print(f"  beta_base (传播率): {optimal_params[0]:.4f}")
    print(f"  sigma (潜伏期倒数): {optimal_params[1]:.4f}")
    print(f"  gamma (恢复率倒数): {optimal_params[2]:.4f}")
    print(f"  media_amplification (媒体放大): {optimal_params[3]:.4f}")
    print(f"\n拟合指标:")
    print(f"  RMSE: {min_error:.2f}")
    print(f"  训练集 R2: {validation_results['train_r2']:.3f}")
    print(f"  测试集 R2: {validation_results['test_r2']:.3f}")
    print(f"\n基本再生数 R0: {R0:.2f}")
    
    return {
        'optimal_params': optimal_params,
        'min_error': min_error,
        'validation_results': validation_results,
        'R0': R0,
        'results': results
    }


def run_real_data_calibration_example():
    """真实数据校准示例（需要下载数据）"""
    
    print("\n" + "=" * 60)
    print("真实数据校准示例")
    print("=" * 60)
    
    print("\n说明：")
    print("要使用真实登革热数据进行校准，请：")
    print("1. 下载OpenDengue数据集: https://opendengue.org/data.html")
    print("2. 将CSV文件保存到 data/opendengue.csv")
    print("3. 取消下方代码的注释并运行")
    
    # 取消注释以使用真实数据
    """
    print("\n[1/3] 加载真实登革热数据...")
    loader = DengueDataLoader()
    real_data = loader.load_opendengue(
        filepath='data/opendengue.csv',
        country='Brazil',
        start_year=2015,
        end_year=2023
    )
    
    print(f"数据形状: {real_data.shape}")
    print(f"时间范围: {real_data['date'].min()} 到 {real_data['date'].max()}")
    
    print("\n[2/3] 校准模型...")
    population = 212000000  # 巴西人口
    calibrator = ModelCalibrator(real_data, population=population)
    
    initial_params = np.array([0.3, 0.2, 0.1, 1.0])
    optimal_params, min_error = calibrator.calibrate(initial_params=initial_params)
    
    print("\n[3/3] 验证模型...")
    validation_results = calibrator.validate(optimal_params, test_ratio=0.2)
    
    R0 = estimate_basic_reproduction_number(optimal_params)
    print(f"\n基本再生数 R0: {R0:.2f}")
    
    # 保存校准结果
    import json
    calibration_results = {
        'optimal_params': optimal_params.tolist(),
        'min_error': float(min_error),
        'validation_results': validation_results,
        'R0': float(R0)
    }
    
    with open('results/calibration_results.json', 'w') as f:
        json.dump(calibration_results, f, indent=2)
    
    print("\n校准结果已保存到: results/calibration_results.json")
    """
    
    return None


if __name__ == "__main__":
    # 使用合成数据演示校准流程
    calibration_results = run_dengue_calibration_with_synthetic_data()
    
    # 显示真实数据校准示例
    run_real_data_calibration_example()
    
    print("\n" + "=" * 60)
    print("实验4完成")
    print("=" * 60)
