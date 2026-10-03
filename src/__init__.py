"""
信息显著性驱动的传染病混合仿真模型
"""

from .hybrid_model import (
    Agent,
    SEIRParams,
    DESParams,
    InformationSaliencyModel,
    RiskPerceptionModel,
    BehaviorModel,
    HospitalDES,
    HybridEpidemicModel
)
from .data_loader import DengueDataLoader, create_synthetic_dengue_data
from .calibration import (
    DeterministicSurrogate,
    estimate_basic_reproduction_number,
    grid_calibrate,
    weekly_aggregate,
)
from .visualization import EpidemicVisualizer, generate_summary_statistics

__version__ = '2.0.0'
__all__ = [
    'Agent', 'SEIRParams', 'DESParams',
    'InformationSaliencyModel', 'RiskPerceptionModel', 'BehaviorModel',
    'HospitalDES', 'HybridEpidemicModel',
    'DengueDataLoader', 'create_synthetic_dengue_data',
    'DeterministicSurrogate', 'grid_calibrate', 'weekly_aggregate',
    'estimate_basic_reproduction_number',
    'EpidemicVisualizer', 'generate_summary_statistics'
]
