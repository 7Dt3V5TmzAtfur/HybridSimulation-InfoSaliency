"""
数据加载与预处理模块
支持登革热公开数据集
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
import os


class DengueDataLoader:
    """登革热数据加载器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
    
    def load_opendengue(self, filepath: str, 
                       country: str = "Brazil",
                       start_year: int = 2010,
                       end_year: int = 2023) -> pd.DataFrame:
        """
        加载OpenDengue数据集
        
        OpenDengue: https://opendengue.org/data.html
        包含102个国家1924-2023年的登革热病例数据
        
        Args:
            filepath: CSV文件路径
            country: 选择国家
            start_year: 起始年份
            end_year: 结束年份
        
        Returns:
            时间序列DataFrame (date, cases)
        """
        df = pd.read_csv(filepath)
        
        # OpenDengue数据格式
        # 列名可能包括: country, location, date, total_cases, etc.
        # 需要根据实际数据格式调整
        
        # 筛选国家和时间范围
        if 'country' in df.columns:
            df = df[df['country'] == country]
        
        # 提取日期和病例数
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        elif 'year' in df.columns and 'month' in df.columns:
            df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        
        # 筛选时间范围
        df = df[(df['date'].dt.year >= start_year) & 
                (df['date'].dt.year <= end_year)]
        
        # 提取病例数（可能的列名）
        case_cols = ['total_cases', 'cases', 'confirmed_cases', 'dengue_cases']
        case_col = None
        for col in case_cols:
            if col in df.columns:
                case_col = col
                break
        
        if case_col is None:
            raise ValueError(f"未找到病例数列，可用列: {df.columns.tolist()}")
        
        # 聚合到月度
        df = df.groupby(df['date'].dt.to_period('M'))[case_col].sum().reset_index()
        df['date'] = df['date'].dt.to_timestamp()
        df = df.sort_values('date').reset_index(drop=True)
        
        return df[['date', case_col]].rename(columns={case_col: 'cases'})
    
    def load_kaggle_dengue(self, filepath: str) -> pd.DataFrame:
        """
        加载Kaggle登革热数据集
        
        Kaggle: https://www.kaggle.com/datasets/arashnic/epidemy
        
        Args:
            filepath: CSV文件路径
        
        Returns:
            时间序列DataFrame (date, cases)
        """
        df = pd.read_csv(filepath)
        
        # 根据Kaggle数据格式调整
        # 可能包含: date, cases, weather_features, etc.
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        case_col = 'cases' if 'cases' in df.columns else df.columns[1]
        
        df = df.sort_values('date').reset_index(drop=True)
        return df[['date', case_col]].rename(columns={case_col: 'cases'})
    
    def load_cdc_dengue(self, filepath: str, 
                       territory: str = "Puerto Rico") -> pd.DataFrame:
        """
        加载CDC登革热数据
        
        CDC: https://www.cdc.gov/dengue/data-research/facts-stats/current-data.html
        
        Args:
            filepath: CSV文件路径
            territory: 选择地区（如Puerto Rico, American Samoa等）
        
        Returns:
            时间序列DataFrame (date, cases)
        """
        df = pd.read_csv(filepath)
        
        # CDC数据格式
        if 'Jurisdiction' in df.columns:
            df = df[df['Jurisdiction'] == territory]
        
        if 'Date' in df.columns:
            df['date'] = pd.to_datetime(df['Date'])
        elif 'Year' in df.columns and 'Month' in df.columns:
            df['date'] = pd.to_datetime(df[['Year', 'Month']].assign(Day=1))
        
        case_col = 'Total Cases' if 'Total Cases' in df.columns else 'Cases'
        
        df = df.sort_values('date').reset_index(drop=True)
        return df[['date', case_col]].rename(columns={case_col: 'cases'})
    
    def load_custom_csv(self, filepath: str, 
                       date_col: str = 'date',
                       cases_col: str = 'cases') -> pd.DataFrame:
        """
        加载自定义CSV数据
        
        Args:
            filepath: CSV文件路径
            date_col: 日期列名
            cases_col: 病例数列名
        
        Returns:
            时间序列DataFrame (date, cases)
        """
        df = pd.read_csv(filepath)
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)
        return df[[date_col, cases_col]].rename(columns={date_col: 'date', cases_col: 'cases'})
    
    def preprocess_for_simulation(self, df: pd.DataFrame,
                                  population: int = 1000000) -> Tuple[pd.DataFrame, dict]:
        """
        预处理数据用于仿真
        
        Args:
            df: 原始数据DataFrame
            population: 人口规模
        
        Returns:
            (预处理后的DataFrame, 元数据字典)
        """
        # 计算基本统计
        metadata = {
            'population': population,
            'total_cases': df['cases'].sum(),
            'peak_cases': df['cases'].max(),
            'peak_date': df.loc[df['cases'].idxmax(), 'date'],
            'mean_cases': df['cases'].mean(),
            'std_cases': df['cases'].std(),
            'time_span_days': (df['date'].max() - df['date'].min()).days
        }
        
        # 转换为日度数据（如果是月度）
        if len(df) < 365:
            # 假设是月度数据，转换为日度
            daily_data = []
            for _, row in df.iterrows():
                days_in_month = row['date'].days_in_month
                daily_cases = row['cases'] / days_in_month
                for i in range(days_in_month):
                    daily_data.append({
                        'date': row['date'] + pd.Timedelta(days=i),
                        'cases': daily_cases
                    })
            df = pd.DataFrame(daily_data)
        
        # 归一化病例数（转换为占总人口比例）
        df['cases_normalized'] = df['cases'] / population
        
        # 计算滚动平均（平滑噪声）
        df['cases_smooth'] = df['cases'].rolling(window=7, min_periods=1).mean()
        
        return df, metadata


def create_synthetic_dengue_data(num_days: int = 365 * 3,
                                 population: int = 1000000,
                                 peak_month: int = 3,
                                 seasonality: float = 0.8) -> pd.DataFrame:
    """
    创建合成登革热数据（用于演示和测试）
    
    登革热特征：
    - 季节性（雨季高峰）
    - 多年周期性
    - 突发疫情
    
    Args:
        num_days: 天数
        population: 人口规模
        peak_month: 高峰月份（1-12）
        seasonality: 季节性强度（0-1）
    
    Returns:
        合成数据DataFrame (date, cases)
    """
    dates = pd.date_range(start='2020-01-01', periods=num_days, freq='D')
    
    # 季节性成分
    day_of_year = np.arange(num_days)
    seasonal = 0.5 * (1 + np.sin(2 * np.pi * (day_of_year - 90) / 365))
    
    # 基础传播率
    base_rate = 0.0001 * population
    
    # 添加随机波动
    noise = np.random.poisson(lam=base_rate * seasonal, size=num_days)
    
    # 添加突发疫情（每年一次）
    for year in range(num_days // 365):
        outbreak_start = year * 365 + peak_month * 30
        if outbreak_start < num_days:
            outbreak_duration = 60
            outbreak_intensity = np.random.uniform(2, 5)
            for i in range(outbreak_duration):
                if outbreak_start + i < num_days:
                    noise[outbreak_start + i] *= outbreak_intensity
    
    df = pd.DataFrame({
        'date': dates,
        'cases': noise.astype(int)
    })
    
    return df


if __name__ == "__main__":
    # 测试合成数据
    print("生成合成登革热数据...")
    df = create_synthetic_dengue_data()
    print(f"数据形状: {df.shape}")
    print(f"时间范围: {df['date'].min()} 到 {df['date'].max()}")
    print(f"总病例数: {df['cases'].sum():,}")
    print(f"峰值病例: {df['cases'].max():,}")
    print(f"\n前5行:\n{df.head()}")
    
    # 保存测试数据
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/synthetic_dengue.csv", index=False)
    print("\n已保存到 data/synthetic_dengue.csv")
