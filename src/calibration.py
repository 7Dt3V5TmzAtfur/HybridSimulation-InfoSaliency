"""
参数校准模块
用于将真实登革热数据拟合到混合仿真模型
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Tuple, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.hybrid_model import HybridEpidemicModel, SEIRParams, DESParams


class ModelCalibrator:
    """模型校准器"""
    
    def __init__(self, real_data: pd.DataFrame, population: int = 1000000):
        """
        初始化校准器
        
        Args:
            real_data: 真实数据DataFrame (date, cases)
            population: 人口规模
        """
        self.real_data = real_data.copy()
        self.population = population
        
        # 预处理真实数据
        self.real_cases = real_data['cases'].values
        self.num_days = len(self.real_cases)
    
    def objective_function(self, params: np.ndarray) -> float:
        """
        目标函数：计算模拟与真实数据的误差
        
        Args:
            params: 参数向量 [beta_base, sigma, gamma, media_amplification]
        
        Returns:
            误差值（均方根误差）
        """
        # 解包参数
        beta_base, sigma, gamma, media_amp = params
        
        # 创建模型
        seir_params = SEIRParams(
            beta_base=beta_base,
            sigma=sigma,
            gamma=gamma
        )
        
        model = HybridEpidemicModel(
            population_size=self.population,
            seir_params=seir_params,
            media_amplification=media_amp,
            enable_info_behavior_feedback=True
        )
        
        # 种子感染
        model.seed_infection(num_initial=10)
        
        # 运行仿真
        model.run(num_days=self.num_days)
        
        # 获取结果
        results = model.get_results()
        simulated_cases = results['I'].values
        
        # 计算误差（均方根误差）
        rmse = np.sqrt(np.mean((simulated_cases - self.real_cases) ** 2))
        
        # 添加正则化项（避免极端参数）
        regularization = 0.01 * np.sum(params ** 2)
        
        return rmse + regularization
    
    def calibrate(self, initial_params: np.ndarray = None,
                 bounds: list = None) -> Tuple[np.ndarray, float]:
        """
        校准模型参数
        
        Args:
            initial_params: 初始参数 [beta_base, sigma, gamma, media_amplification]
            bounds: 参数边界
        
        Returns:
            (最优参数, 最小误差)
        """
        if initial_params is None:
            initial_params = np.array([0.3, 0.2, 0.1, 1.0])
        
        if bounds is None:
            bounds = [
                (0.1, 0.5),  # beta_base
                (0.1, 0.5),  # sigma
                (0.05, 0.2),  # gamma
                (0.5, 3.0)   # media_amplification
            ]
        
        print("开始参数校准...")
        print(f"初始参数: beta={initial_params[0]:.3f}, sigma={initial_params[1]:.3f}, "
              f"gamma={initial_params[2]:.3f}, media_amp={initial_params[3]:.3f}")
        
        # 使用L-BFGS-B优化
        result = minimize(
            self.objective_function,
            initial_params,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 100, 'disp': True}
        )
        
        optimal_params = result.x
        min_error = result.fun
        
        print(f"\n校准完成!")
        print(f"最优参数: beta={optimal_params[0]:.3f}, sigma={optimal_params[1]:.3f}, "
              f"gamma={optimal_params[2]:.3f}, media_amp={optimal_params[3]:.3f}")
        print(f"最小误差(RMSE): {min_error:.2f}")
        
        return optimal_params, min_error
    
    def validate(self, params: np.ndarray, test_ratio: float = 0.2) -> Dict:
        """
        验证模型（训练集/测试集分割）
        
        Args:
            params: 校准后的参数
            test_ratio: 测试集比例
        
        Returns:
            验证结果字典
        """
        split_idx = int(self.num_days * (1 - test_ratio))
        
        # 使用给定参数运行完整仿真
        seir_params = SEIRParams(
            beta_base=params[0],
            sigma=params[1],
            gamma=params[2]
        )
        
        model = HybridEpidemicModel(
            population_size=self.population,
            seir_params=seir_params,
            media_amplification=params[3],
            enable_info_behavior_feedback=True
        )
        model.seed_infection(num_initial=10)
        model.run(num_days=self.num_days)
        
        full_results = model.get_results()
        
        # 训练集验证
        train_real = self.real_data.iloc[:split_idx]['cases'].values
        train_simulated = full_results['I'].values[:split_idx]
        train_rmse = np.sqrt(np.mean((train_simulated - train_real) ** 2))
        
        # 测试集验证
        test_real = self.real_data.iloc[split_idx:]['cases'].values
        test_simulated = full_results['I'].values[split_idx:]
        test_rmse = np.sqrt(np.mean((test_simulated - test_real) ** 2))
        
        # 计算R²
        train_ss_res = np.sum((train_real - train_simulated) ** 2)
        train_ss_tot = np.sum((train_real - np.mean(train_real)) ** 2)
        train_r2 = 1 - (train_ss_res / train_ss_tot) if train_ss_tot > 0 else 0
        
        test_ss_res = np.sum((test_real - test_simulated) ** 2)
        test_ss_tot = np.sum((test_real - np.mean(test_real)) ** 2)
        test_r2 = 1 - (test_ss_res / test_ss_tot) if test_ss_tot > 0 else 0
        
        validation_results = {
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_size': split_idx,
            'test_size': self.num_days - split_idx
        }
        
        print("\n验证结果:")
        print(f"训练集 RMSE: {train_rmse:.2f}, R²: {train_r2:.3f}")
        print(f"测试集 RMSE: {test_rmse:.2f}, R²: {test_r2:.3f}")
        
        return validation_results


def estimate_basic_reproduction_number(params: np.ndarray) -> float:
    """
    估计基本再生数R0
    
    R0 = beta / gamma
    
    Args:
        params: 参数向量 [beta_base, sigma, gamma, media_amplification]
    
    Returns:
        R0值
    """
    beta_base = params[0]
    gamma = params[2]
    R0 = beta_base / gamma
    return R0


if __name__ == "__main__":
    # 测试校准器
    from src.data_loader import create_synthetic_dengue_data
    
    print("生成合成数据用于测试校准...")
    synthetic_data = create_synthetic_dengue_data(num_days=365)
    
    calibrator = ModelCalibrator(synthetic_data, population=1000000)
    
    # 校准
    optimal_params, min_error = calibrator.calibrate()
    
    # 验证
    validation_results = calibrator.validate(optimal_params)
    
    # 计算R0
    R0 = estimate_basic_reproduction_number(optimal_params)
    print(f"\n基本再生数 R0: {R0:.2f}")
