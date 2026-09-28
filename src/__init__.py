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
from .calibration import ModelCalibrator, estimate_basic_reproduction_number
from .visualization import EpidemicVisualizer, generate_summary_statistics

__version__ = '1.0.0'
__all__ = [
    'Agent', 'SEIRParams', 'DESParams',
    'InformationSaliencyModel', 'RiskPerceptionModel', 'BehaviorModel',
    'HospitalDES', 'HybridEpidemicModel',
    'DengueDataLoader', 'create_synthetic_dengue_data',
    'ModelCalibrator', 'estimate_basic_reproduction_number',
    'EpidemicVisualizer', 'generate_summary_statistics'
]
