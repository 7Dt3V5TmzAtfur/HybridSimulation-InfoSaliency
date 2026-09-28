# 模型说明文档

## 一、模型概述

本项目实现了一个**信息显著性驱动的登革热混合仿真模型**，将ABM（Agent-Based Model）、SD（System Dynamics）和DES（Discrete Event Simulation）三层耦合，模拟登革热传播过程中信息-行为-疫情的动态交互。

---

## 二、核心类说明

### 2.1 Agent类

**位置**：`src/hybrid_model.py`

**功能**：表示个体Agent，包含状态、风险感知、防护行为等属性

**属性**：
```python
@dataclass
class Agent:
    id: int                      # Agent唯一标识
    state: str                   # 状态：'S', 'E', 'I', 'R'
    risk_perception: float       # 风险感知 [0, 1]
    protection_level: float      # 防护水平 [0, 1]
    info_saliency: float         # 信息显著性感知 [0, 1]
    infected_day: int            # 感染天数
    exposed_day: int             # 潜伏天数
    detected: bool               # 是否已检测
    hospital_admitted: bool      # 是否已住院
    in_queue: bool               # 是否在等待队列
    queue_start_time: int        # 进入队列时间
```

**使用示例**：
```python
from src.hybrid_model import Agent

agent = Agent(id=0, state='S')
agent.risk_perception = 0.5
agent.protection_level = 0.8
```

---

### 2.2 SEIRParams类

**位置**：`src/hybrid_model.py`

**功能**：SEIR模型参数配置

**属性**：
```python
@dataclass
class SEIRParams:
    beta_base: float = 0.3           # 基础传播率
    sigma: float = 0.2               # 潜伏期倒数（1/5天）
    gamma: float = 0.1               # 恢复率倒数（1/10天）
    hospitalization_rate: float = 0.15  # 住院率
    detection_rate: float = 0.3      # 检测率
```

**参数说明**：
- `beta_base`：基础传播率，范围[0.1, 0.5]，登革热典型值0.2-0.4
- `sigma`：潜伏期转移率，1/σ为平均潜伏期（5天）
- `gamma`：恢复率，1/γ为平均感染期（10天）
- `hospitalization_rate`：感染者住院概率，登革热典型值10-20%
- `detection_rate`：感染者被检测概率

---

### 2.3 DESParams类

**位置**：`src/hybrid_model.py`

**功能**：医疗资源离散事件仿真参数

**属性**：
```python
@dataclass
class DESParams:
    hospital_beds: int = 200         # 医院床位数
    icu_beds: int = 50               # ICU床位数
    testing_capacity: int = 100      # 每日检测能力
    avg_hospital_stay: int = 7       # 平均住院天数
    avg_icu_stay: int = 14           # 平均ICU天数
    test_result_time: int = 1        # 检测结果时间（天）
```

**参数调整建议**：
- 根据目标地区实际医疗资源调整床位数量
- 登革热重症率约5-10%，ICU需求相应调整
- 检测能力根据当地实验室 capacity 设置

---

### 2.4 InformationSaliencyModel类

**位置**：`src/hybrid_model.py`

**功能**：计算信息显著性

**方法**：
```python
def update(self, infected_count: int, total_population: int, day: int) -> float:
    """
    更新信息显著性
    
    公式：S(t) = min(1.0, (I/N) * media_amp * exp(-decay * t/100))
    
    Args:
        infected_count: 当前感染人数
        total_population: 总人口
        day: 当前天数
    
    Returns:
        信息显著性值 [0, 1]
    """
```

**参数说明**：
- `media_amplification`：媒体放大系数，范围[0.5, 5.0]
  - 0.5：低媒体关注
  - 1.0：正常媒体关注
  - 2.0-5.0：高媒体关注（疫情爆发期）
- `decay_rate`：信息衰减率，默认0.1，模拟信息疲劳

---

### 2.5 RiskPerceptionModel类

**位置**：`src/hybrid_model.py`

**功能**：更新个体风险感知

**方法**：
```python
def update_agent(self, agent: Agent, info_saliency: float, 
                social_influence: float, personal_experience: float) -> float:
    """
    更新个体风险感知
    
    公式：R_target = w_info * S + w_social * Social + w_personal * Personal
         R(t+1) = (1 - α) * R_target + α * R(t)
    
    Args:
        agent: 个体Agent
        info_saliency: 信息显著性
        social_influence: 社会影响（周围人感染比例）
        personal_experience: 个人经历（是否感染或接触感染者）
    
    Returns:
        风险感知值 [0, 1]
    """
```

**参数说明**：
- `info_weight`：信息权重，默认0.6
- `social_weight`：社会影响权重，默认0.3
- `personal_weight`：个人经历权重，默认0.1
- `inertia`：行为惯性，默认0.3，避免风险感知剧烈波动

---

### 2.6 BehaviorModel类

**位置**：`src/hybrid_model.py`

**功能**：更新防护行为

**方法**：
```python
def update_protection(self, agent: Agent) -> float:
    """
    更新防护行为
    
    公式：P = 1 / (1 + exp(-k * (R - 0.5)))
    
    Args:
        agent: 个体Agent
    
    Returns:
        防护水平 [0, 1]
    """
```

**参数说明**：
- `sensitivity`：风险感知敏感度，默认1.5
  - 值越大，防护行为对风险感知的响应越陡峭
  - 值越小，防护行为变化越平缓

---

### 2.7 HospitalDES类

**位置**：`src/hybrid_model.py`

**功能**：医院资源离散事件仿真

**方法**：
```python
def request_admission(self, agent: Agent, day: int, severe: bool = False) -> bool:
    """请求住院"""

def request_test(self, agent: Agent, day: int) -> bool:
    """请求检测"""

def process_daily(self, day: int) -> Tuple[int, int]:
    """处理每日事件（出院、检测完成、等待队列）"""
```

**队列管理**：
- 使用最小堆（heapq）管理事件队列
- 按事件时间排序处理
- 支持容量溢出统计

---

### 2.8 HybridEpidemicModel类

**位置**：`src/hybrid_model.py`

**功能**：主混合仿真模型，耦合ABM+SD+DES三层

**初始化**：
```python
def __init__(self, population_size: int = 1000, 
             seir_params: SEIRParams = None,
             des_params: DESParams = None,
             media_amplification: float = 1.0,
             enable_info_behavior_feedback: bool = True):
    """
    初始化混合仿真模型
    
    Args:
        population_size: 人口规模
        seir_params: SEIR参数
        des_params: DES参数
        media_amplification: 媒体放大系数
        enable_info_behavior_feedback: 是否启用信息-行为反馈
    """
```

**主要方法**：
```python
def seed_infection(self, num_initial: int = 5):
    """种子感染"""

def step(self, day: int):
    """单步仿真（1天）"""

def run(self, num_days: int = 200):
    """运行仿真"""

def get_results(self) -> pd.DataFrame:
    """获取结果DataFrame"""
```

**结果DataFrame列**：
- `day`：天数
- `S`, `E`, `I`, `R`：各状态人数
- `info_saliency`：信息显著性
- `avg_risk`：平均风险感知
- `avg_protection`：平均防护水平
- `hospital_beds`：占用医院床位数
- `hospital_icu`：占用ICU床位数
- `rejected`：累计被拒绝入院次数
- `effective_beta`：有效传播率

---

## 三、数据加载模块

### 3.1 DengueDataLoader类

**位置**：`src/data_loader.py`

**功能**：加载和预处理登革热公开数据集

**支持的数据源**：
1. OpenDengue（推荐）
2. Kaggle Dengue Dataset
3. CDC Dengue Data
4. 自定义CSV

**方法**：
```python
def load_opendengue(self, filepath: str, country: str = "Brazil",
                   start_year: int = 2010, end_year: int = 2023) -> pd.DataFrame:
    """加载OpenDengue数据集"""

def load_kaggle_dengue(self, filepath: str) -> pd.DataFrame:
    """加载Kaggle登革热数据集"""

def load_cdc_dengue(self, filepath: str, territory: str = "Puerto Rico") -> pd.DataFrame:
    """加载CDC登革热数据"""

def load_custom_csv(self, filepath: str, date_col: str = 'date',
                   cases_col: str = 'cases') -> pd.DataFrame:
    """加载自定义CSV数据"""

def preprocess_for_simulation(self, df: pd.DataFrame,
                              population: int = 1000000) -> Tuple[pd.DataFrame, dict]:
    """预处理数据用于仿真"""
```

**使用示例**：
```python
from src.data_loader import DengueDataLoader

loader = DengueDataLoader()
df = loader.load_opendengue(
    filepath='data/opendengue.csv',
    country='Brazil',
    start_year=2015,
    end_year=2023
)

df_processed, metadata = loader.preprocess_for_simulation(df, population=212000000)
```

---

### 3.2 合成数据生成

**函数**：`create_synthetic_dengue_data`

**功能**：生成合成登革热数据用于测试

**参数**：
```python
def create_synthetic_dengue_data(num_days: int = 365 * 3,
                                 population: int = 1000000,
                                 peak_month: int = 3,
                                 seasonality: float = 0.8) -> pd.DataFrame:
    """
    创建合成登革热数据
    
    Args:
        num_days: 天数
        population: 人口规模
        peak_month: 高峰月份（1-12）
        seasonality: 季节性强度（0-1）
    
    Returns:
        合成数据DataFrame (date, cases)
    """
```

**特征**：
- 季节性（雨季高峰）
- 多年周期性
- 突发疫情（每年一次）
- 随机波动

---

## 四、参数校准模块

### 4.1 ModelCalibrator类

**位置**：`src/calibration.py`

**功能**：使用真实数据校准模型参数

**方法**：
```python
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

def validate(self, params: np.ndarray, test_ratio: float = 0.2) -> Dict:
    """
    验证模型（训练集/测试集分割）
    
    Returns:
        验证结果字典（train_rmse, test_rmse, train_r2, test_r2）
    """
```

**优化方法**：L-BFGS-B（支持边界约束的拟牛顿法）

**目标函数**：均方根误差（RMSE）+ 正则化项

**使用示例**：
```python
from src.calibration import ModelCalibrator

calibrator = ModelCalibrator(real_data, population=1000000)
optimal_params, min_error = calibrator.calibrate()
validation_results = calibrator.validate(optimal_params)
```

---

### 4.2 基本再生数估计

**函数**：`estimate_basic_reproduction_number`

**公式**：R0 = β / γ

**使用示例**：
```python
from src.calibration import estimate_basic_reproduction_number

R0 = estimate_basic_reproduction_number(optimal_params)
print(f"基本再生数 R0: {R0:.2f}")
```

---

## 五、可视化模块

### 5.1 EpidemicVisualizer类

**位置**：`src/visualization.py`

**功能**：生成论文级别的可视化图表

**方法**：
```python
def plot_epidemic_curves(self, save_path: str = None, show_info_effect: bool = True):
    """绘制流行病曲线（SEIR + 信息显著性 + 医疗资源）"""

def plot_comparison(self, results_list: List[pd.DataFrame], 
                   labels: List[str], save_path: str = None):
    """绘制多场景对比图"""

def plot_parameter_sensitivity(self, param_name: str, param_values: List[float],
                              results_list: List[pd.DataFrame], save_path: str = None):
    """绘制参数敏感性分析图"""

def plot_heatmap_analysis(self, results_df: pd.DataFrame, save_path: str = None):
    """绘制热力图分析"""
```

**图表样式**：
- 论文级别质量（dpi=300）
- 白底网格样式
- 自动调整布局

---

### 5.2 汇总统计

**函数**：`generate_summary_statistics`

**功能**：生成仿真结果汇总统计

**返回指标**：
- `peak_infected`：峰值感染人数
- `peak_day`：峰值出现日期
- `total_infected`：总感染人数
- `attack_rate`：攻击率（总感染/总人口）
- `max_protection`：最大防护水平
- `max_info_saliency`：最大信息显著性
- `max_hospital_beds`：最大医院床位使用
- `max_icu_beds`：最大ICU床位使用
- `total_rejected`：累计被拒绝入院次数

---

## 六、完整使用流程

### 6.1 快速开始

```python
import sys
sys.path.insert(0, 'dengue-hybrid-sim')

from src.hybrid_model import HybridEpidemicModel, SEIRParams, DESParams
from src.visualization import EpidemicVisualizer

# 1. 创建模型
model = HybridEpidemicModel(
    population_size=10000,
    seir_params=SEIRParams(beta_base=0.3, sigma=0.2, gamma=0.1),
    des_params=DESParams(hospital_beds=200, icu_beds=50),
    media_amplification=1.5,
    enable_info_behavior_feedback=True
)

# 2. 种子感染
model.seed_infection(num_initial=10)

# 3. 运行仿真
model.run(num_days=200)

# 4. 获取结果
results = model.get_results()

# 5. 可视化
viz = EpidemicVisualizer(results)
viz.plot_epidemic_curves(save_path='results/epidemic_curves.png')
```

### 6.2 数据校准流程

```python
from src.data_loader import DengueDataLoader
from src.calibration import ModelCalibrator

# 1. 加载数据
loader = DengueDataLoader()
real_data = loader.load_opendengue('data/opendengue.csv', country='Brazil')

# 2. 创建校准器
calibrator = ModelCalibrator(real_data, population=212000000)

# 3. 校准参数
optimal_params, min_error = calibrator.calibrate()

# 4. 验证模型
validation_results = calibrator.validate(optimal_params)

# 5. 使用最优参数运行仿真
from src.hybrid_model import HybridEpidemicModel, SEIRParams

model = HybridEpidemicModel(
    population_size=212000000,
    seir_params=SEIRParams(
        beta_base=optimal_params[0],
        sigma=optimal_params[1],
        gamma=optimal_params[2]
    ),
    media_amplification=optimal_params[3]
)
model.seed_infection(num_initial=100)
model.run(num_days=len(real_data))

results = model.get_results()
```

---

## 七、常见问题

### Q1: 如何调整模型以适应不同地区？

**A**: 调整以下参数：
- `population_size`：地区人口
- `hospital_beds`, `icu_beds`：医疗资源
- `testing_capacity`：检测能力
- 使用真实数据校准传播率参数

### Q2: 模型运行很慢怎么办？

**A**: 
- 减少人口规模（如从10000降到1000）
- 减少仿真天数
- 使用PyPy加速（需要修改代码）

### Q3: 如何添加新的行为机制？

**A**: 
1. 在`Agent`类中添加新属性
2. 在`BehaviorModel`类中添加新行为规则
3. 在`HybridEpidemicModel.step()`中调用新行为

### Q4: 如何处理缺失数据？

**A**: 使用`preprocess_for_simulation`方法自动处理：
```python
df_processed, metadata = loader.preprocess_for_simulation(df)
# 自动进行线性插值和滚动平均
```

---

## 八、技术细节

### 8.1 随机数生成

模型使用`numpy.random`进行随机采样，建议设置随机种子以保证可复现性：

```python
import numpy as np
np.random.seed(42)
```

### 8.2 性能优化

- 使用`numpy`向量化操作
- 使用`heapq`管理事件队列（O(log n)插入/删除）
- 避免在循环中创建新对象

### 8.3 数值稳定性

- 所有概率值限制在[0, 1]范围
- 使用`min/max`防止溢出
- S型函数避免指数溢出

---

**文档版本**：1.0  
**最后更新**：2026-09-28  
**作者**：AI Research Assistant
