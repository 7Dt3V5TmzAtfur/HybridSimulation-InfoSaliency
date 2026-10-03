# 登革热数据集下载指南

## 推荐数据集

### 1. OpenDengue（推荐）

**网址**：https://opendengue.org/data.html

**数据特点**：
- 覆盖102个国家和地区
- 时间跨度：1924-2023年
- 包含月度/年度病例数
- 免费开放获取

**本仓库数据**：`data/National_extract_V1_3.csv`（OpenDengue v1.3 国家级数据抽取，已提交）。
实验 4 使用的口径：国家=BRAZIL，case_definition=Total（该口径覆盖 2016-2023；Probable 仅覆盖 2015），周分辨率，2019 自然年（52 周）。

**加载代码（实际格式）**：
```python
from src.data_loader import DengueDataLoader

loader = DengueDataLoader()
df = loader.load_opendengue_national(
    filepath='data/National_extract_V1_3.csv',
    country='BRAZIL',
    start='2019-01-01',
    end='2019-12-31',
    case_definition='Total'   # 实际列: adm_0_name / calendar_start_date / dengue_total / T_res / case_definition_standardised
)
```

如需更新数据：访问上述网址，下载最新 national-level extract（CSV），替换 `data/National_extract_V1_3.csv`（旧版本由 git 管理）。

**旧版说明**：此前文档所述"下载后保存为 `data/opendengue.csv`"的简化格式与实际数据不符，
是 2026-10-03 之前"论文声称用真实数据、实际管线跑合成数据"不一致的根源之一，已修正。

---

### 2. Kaggle Dengue Dataset

**网址**：https://www.kaggle.com/datasets/arashnic/epidemy

**数据特点**：
- 包含气象特征（温度、湿度、降水）
- 多个地区数据
- 适合研究气候-登革热关系

**下载步骤**：
1. 注册Kaggle账号（如未有）
2. 访问上述网址
3. 点击"Download"
4. 解压后保存到 `data/kaggle_dengue/`

**数据格式**：
```csv
date,cases,temperature,humidity,precipitation
2020-01-01,123,28.5,0.75,12.3
2020-01-02,145,29.1,0.78,8.7
...
```

**加载代码**：
```python
from src.data_loader import DengueDataLoader

loader = DengueDataLoader()
df = loader.load_kaggle_dengue(filepath='data/kaggle_dengue/train.csv')
```

---

### 3. CDC Dengue Data（美国领土）

**网址**：https://www.cdc.gov/dengue/data-research/facts-stats/current-data.html

**数据特点**：
- 覆盖美国领土（波多黎各、美属萨摩亚等）
- 高质量官方数据
- 周度/月度更新

**下载步骤**：
1. 访问上述网址
2. 选择"Surveillance Data"
3. 下载CSV格式数据
4. 保存到 `data/cdc_dengue.csv`

**数据格式**：
```csv
Jurisdiction,Year,Month,Total Cases,Dengue Type
Puerto Rico,2020,1,234,DENV-1
Puerto Rico,2020,2,456,DENV-1
...
```

**加载代码**：
```python
from src.data_loader import DengueDataLoader

loader = DengueDataLoader()
df = loader.load_cdc_dengue(
    filepath='data/cdc_dengue.csv',
    territory='Puerto Rico'
)
```

---

### 4. 自定义数据

如果您有自己的登革热数据，可以使用自定义加载：

**数据格式要求**：
```csv
date,cases
2020-01-01,123
2020-01-02,145
...
```

**加载代码**：
```python
from src.data_loader import DengueDataLoader

loader = DengueDataLoader()
df = loader.load_custom_csv(
    filepath='data/my_dengue_data.csv',
    date_col='date',
    cases_col='cases'
)
```

---

## 数据预处理

加载数据后，建议进行以下预处理：

```python
from src.data_loader import DengueDataLoader

loader = DengueDataLoader()
df = loader.load_opendengue('data/opendengue.csv', country='Brazil')

# 预处理（归一化、平滑等）
df_processed, metadata = loader.preprocess_for_simulation(
    df, 
    population=10000000  # 巴西人口
)

print(f"总病例数: {metadata['total_cases']:,}")
print(f"峰值病例: {metadata['peak_cases']:,}")
print(f"峰值日期: {metadata['peak_date']}")
```

---

## 合成数据（用于测试）

如果没有真实数据，可以使用合成数据进行测试：

```python
from src.data_loader import create_synthetic_dengue_data

# 生成3年的合成登革热数据
df = create_synthetic_dengue_data(
    num_days=365*3,
    population=1000000,
    peak_month=3,  # 3月高峰
    seasonality=0.8
)

# 保存到本地
df.to_csv('data/synthetic_dengue.csv', index=False)
```

---

## 数据质量检查

在使用数据前，建议检查：

1. **缺失值**：
```python
print(f"缺失值数量: {df['cases'].isna().sum()}")
```

2. **异常值**：
```python
import matplotlib.pyplot as plt
plt.plot(df['date'], df['cases'])
plt.title('Dengue Cases Over Time')
plt.show()
```

3. **时间连续性**：
```python
date_diffs = df['date'].diff().dt.days
print(f"日期间隔统计:\n{date_diffs.describe()}")
```

---

## 常见问题

**Q: 数据是月度还是日度？**
A: OpenDengue和CDC数据通常是月度，Kaggle数据可能是日度。代码会自动处理转换。

**Q: 如何处理缺失数据？**
A: 建议使用线性插值或前向填充：
```python
df['cases'] = df['cases'].interpolate(method='linear')
```

**Q: 如何选择合适的人口规模？**
A: 使用数据对应地区的实际人口。可以从世界银行数据获取：https://data.worldbank.org/

---

## 数据引用

使用这些数据时，请引用原始数据源：

- **OpenDengue**: Kraemer et al. (2019). The global distribution of the arbovirus vectors Aedes aegypti and Ae. albopictus. eLife, 8, e47160.
- **CDC**: Centers for Disease Control and Prevention. Dengue Surveillance Data.
- **Kaggle**: 参见数据集页面引用说明。
