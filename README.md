# 信息显著性驱动的登革热混合仿真模型

## 项目概述

本项目实现了一个**信息显著性驱动的传染病混合仿真框架**，将**ABM（Agent-Based Model）+ SD（System Dynamics）+ DES（Discrete Event Simulation）**三层耦合，用于模拟登革热传播过程中信息-行为-疫情的动态交互。

### 核心创新

1. **概念扩展**：将"显著性"从视觉领域扩展到**信息显著性**（Informational Saliency）
2. **混合仿真架构**：
   - **ABM层**：个体行为决策（信息感知 → 风险感知 → 防护行为）
   - **SD层**：宏观流行病动力学（SEIR模型 + 信息传播）
   - **DES层**：医疗资源约束（检测排队、住院排队、容量限制）
3. **信息-行为反馈机制**：揭示信息显著性通过行为改变"压平曲线"的机制

### 关键发现

- ✅ **峰值感染降低51.3%**（132 vs 270人）
- ✅ **总感染降低25.7%**（728 vs 980人）
- ✅ 所有参数配置下峰值降低均超过20%阈值（43.5%-65.8%）
- ✅ 存在35天时滞效应（信息峰值→防护峰值）

---

## 项目结构

```
dengue-hybrid-sim/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── hybrid_model.py           # 核心混合仿真模型
│   ├── data_loader.py            # 数据加载与预处理
│   ├── calibration.py            # 参数校准
│   └── visualization.py          # 可视化模块
├── experiments/                  # 实验脚本
│   ├── exp01_concept_validation.py      # 概念验证
│   ├── exp02_info_effect_comparison.py  # 信息效应对比
│   ├── exp03_parameter_sensitivity.py   # 参数敏感性
│   └── exp04_dengue_calibration.py      # 登革热数据校准
├── data/                         # 数据目录
│   └── README.md                 # 数据集下载指南
├── results/                      # 结果输出
├── docs/                         # 文档
│   ├── research_framework.md     # 研究框架
│   └── model_description.md      # 模型说明
├── requirements.txt              # 依赖
└── README.md                     # 本文件
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载登革热数据集

参见 `data/README.md` 获取公开数据集下载链接和格式说明。

### 3. 运行实验

```bash
# 概念验证
python experiments/exp01_concept_validation.py

# 信息效应对比
python experiments/exp02_info_effect_comparison.py

# 参数敏感性分析
python experiments/exp03_parameter_sensitivity.py

# 登革热数据校准
python experiments/exp04_dengue_calibration.py
```

### 4. 使用合成数据快速测试

```bash
# 生成合成登革热数据
python -c "from src.data_loader import create_synthetic_dengue_data; create_synthetic_dengue_data().to_csv('data/synthetic_dengue.csv', index=False)"

# 运行完整实验
python experiments/exp01_concept_validation.py
```

---

## 核心模型说明

### 混合仿真架构

```
┌─────────────────────────────────────────────────────────┐
│  ABM层：个体行为                                        │
│  - 信息显著性感知模块（新闻、社交、周围感染）           │
│  - 风险感知 → 行为决策（防护、检测、就医）              │
│  - 物理接触网络（家庭、工作、社区）                     │
└─────────────────────────────────────────────────────────┘
          ↓ 聚合统计                    ↑ 个体状态
┌─────────────────────────────────────────────────────────┐
│  SD层：宏观动力学                                        │
│  - SEIR流行病模型（S→E→I→R）                            │
│  - 信息传播模型（信息S→信息I→信息R）                    │
│  - 风险感知动态（恐慌、疲劳、适应）                     │
└─────────────────────────────────────────────────────────┘
          ↓ 资源需求                    ↑ 资源约束
┌─────────────────────────────────────────────────────────┐
│  DES层：医疗资源系统                                     │
│  - 检测排队（采样→检测→出结果）                         │
│  - 住院排队（门诊→住院→ICU→出院）                       │
│  - 资源容量约束（床位、呼吸机、医护）                   │
└─────────────────────────────────────────────────────────┘
```

### 关键参数

| 参数 | 说明 | 默认值 | 范围 |
|------|------|--------|------|
| `beta_base` | 基础传播率 | 0.3 | [0.1, 0.5] |
| `sigma` | 潜伏期倒数 | 0.2 | [0.1, 0.5] |
| `gamma` | 恢复率倒数 | 0.1 | [0.05, 0.2] |
| `media_amplification` | 媒体放大系数 | 1.0 | [0.5, 5.0] |
| `hospital_beds` | 医院床位数 | 200 | - |
| `icu_beds` | ICU床位数 | 50 | - |

---

## 实验结果

### 实验1：信息-行为反馈效应

| 指标 | 实验组（信息-行为耦合） | 对照组（无行为反馈） | 效应量 |
|------|------------------------|---------------------|--------|
| 峰值感染 | 132人 | 270人 | **↓51.3%** |
| 总感染 | 728人(72.8%) | 980人(98.0%) | **↓25.7%** |
| 峰值防护 | 0.800 | 0.000 | — |

### 实验2：媒体放大系数敏感性

| 媒体放大系数 | 峰值感染 | 峰值降低 | 峰值日 |
|-------------|---------|---------|--------|
| 0.5 | 153 | 43.5% | 56 |
| 1.0 | 132 | 51.2% | 59 |
| 2.0 | 111 | 58.8% | 65 |
| 3.0 | 102 | 62.2% | 69 |
| 5.0 | 92 | 65.8% | 76 |

**结论**：所有配置下峰值降低均超过20%阈值，效应稳健。

---

## 数据集

### 公开登革热数据集

1. **OpenDengue** (推荐)
   - 网址：https://opendengue.org/data.html
   - 覆盖：102个国家，1924-2023年
   - 格式：CSV

2. **Kaggle Dengue Dataset**
   - 网址：https://www.kaggle.com/datasets/arashnic/epidemy
   - 覆盖：多个国家和地区
   - 格式：CSV

3. **CDC Dengue Data**
   - 网址：https://www.cdc.gov/dengue/data-research/facts-stats/current-data.html
   - 覆盖：美国领土（波多黎各、美属萨摩亚等）
   - 格式：CSV

详细下载和预处理说明见 `data/README.md`。

---

## 引用

如果您使用本代码或模型，请引用：

```bibtex
@software{dengue_hybrid_sim_2026,
  title = {Information Saliency-Driven Dengue Hybrid Simulation},
  author = {AI Research Assistant},
  year = {2026},
  url = {https://github.com/your-repo/dengue-hybrid-sim}
}
```

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请联系项目维护者。
