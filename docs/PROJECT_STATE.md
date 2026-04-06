# PROJECT_STATE.md

本文件用于持续同步 `TMM-interference-spectrum` 项目的当前状态，是后续 AI Agent 和架构师恢复上下文的首要入口。

## 1. Current Snapshot

- 更新时间：2026-04-06
- 当前判断 Phase：`Phase 02`
- 阶段定义：`绝对反射率标定 -> 文献数字化 -> CsFAPI 近红外外推 -> TMM 基准前向/反演闭环`
- 当前可用能力：
  - 已有 `step01_absolute_calibration.py`，可将样品与银镜原始计数转换为绝对反射率
  - 已有 `step01b_cauchy_extrapolation.py`，可基于 [LIT-0001] 的 `ITO/CsFAPI` 数字化折射率曲线生成 `750-1100 nm` 的 CsFAPI 扩展 `n-k` 中间件
  - 已有 `step02_tmm_inversion.py`，可读取目标反射率、ITO 色散和 CsFAPI 扩展 `n-k` 中间件，执行包含 50/50 BEMA 粗糙度与 ITO 标量吸收补偿的三参数 `d_bulk + d_rough + alpha_ito` 联合反演
  - 已有 `diagnostics_shape_mismatch.py`，可在独立沙盒中对 ITO 近红外吸收、厚度不均匀性和 PVK 色散斜率做形状畸变诊断
  - 已有 `step02_digitize_fapi_optical_constants.py`，可从 `LIT-0001` 的 Fig. 2 原图数字化提取 FAPI 的 `n/κ` 曲线并输出 QA 图
  - 已有 `step02_digitize_csfapi_optical_constants.py`，可从 `LIT-0001` 的 Fig. 3 原图数字化提取 CsFAPI 的 `n/κ` 曲线并输出 QA 图
  - 已产出标准中间文件 `data/processed/target_reflectance.csv` 与 `data/processed/CsFAPI_nk_extended.csv`
  - 已完成 Phase 02 形状畸变诊断，当前证据指向：ITO 近红外吸收失真是长波端托平与整体形状失配的主导因素
- 当前未完成内容：
  - 尚未建立 `src/core/` 公共物理模块
  - 尚未把历史目录完全迁移到 `AGENTS.md` 规定的新结构
  - 尚未形成规范化的 Phase 日志、资源索引和结构化结果台账

## 2. Current Directory Tree

以下目录树基于当前仓库实际状态整理，仅保留关键层级和关键文件。

```text
TMM-interference-spectrum/
├── AGENTS.md
├── docs/
│   ├── LITERATURE_MAP.md
│   └── PROJECT_STATE.md
├── src/
│   └── scripts/
│       ├── diagnostics_shape_mismatch.py
│       ├── step01_absolute_calibration.py
│       ├── step01b_cauchy_extrapolation.py
│       ├── step02_digitize_csfapi_optical_constants.py
│       ├── step02_digitize_fapi_optical_constants.py
│       └── step02_tmm_inversion.py
├── data/
│   └── processed/
│       ├── CsFAPI_nk_extended.csv
│       └── target_reflectance.csv
├── resources/
│   ├── digitized/
│   │   ├── phase02_fig2_fapi_optical_constants_digitized.csv
│   │   └── phase02_fig3_csfapi_optical_constants_digitized.csv
│   ├── GCC-1022系列xlsx.xlsx
│   ├── ITO_20 Ohm_105 nm_e1e2.mat
│   ├── CsFAPI_TL_parameters_and_formulas.md
│   └── MinerU-0.13.1-arm64.dmg
├── results/
│   ├── figures/
│   │   ├── absolute_reflectance_interference.png
│   │   ├── cauchy_extrapolation_check.png
│   │   ├── diagnostic_shape_analysis.png
│   │   ├── phase02_fig2_fapi_optical_constants_digitized.png
│   │   ├── phase02_fig2_fapi_optical_constants_overlay.png
│   │   ├── phase02_fig3_csfapi_optical_constants_digitized.png
│   │   ├── phase02_fig3a_csfapi_optical_constants_overlay.png
│   │   ├── phase02_fig3b_csfapi_optical_constants_overlay.png
│   │   └── tmm_inversion_result.png
│   └── logs/
│       ├── phase02_shape_diagnostic_report.md
│       ├── phase02_fig2_fapi_digitization_notes.md
│       └── phase02_fig3_csfapi_digitization_notes.md
├── test_data/
│   ├── sample.csv
│   ├── glass-1mm.csv
│   └── Ag-mirro.csv
└── reference/
    └── Khan.../...
```

## 3. Structure Compliance Notes

当前仓库与项目级 `AGENTS.md` 规范相比，存在以下结构偏差：

- `test_data/` 仍然承担原始测量数据目录职责，后续应迁移或重命名到 `data/raw/`
- `reference/` 目前存放论文拆解结果，按新规范更适合逐步并入 `resources/references/`
- `src/core/` 尚不存在，脚本中的复用逻辑目前仍散落在 `src/scripts/`
- 项目根尚无 `README.md`

这些偏差当前不会阻断现有流程，但属于后续需要收敛的结构债务。

## 4. Script SOP

### 4.1 `step01_absolute_calibration.py`

- 文件位置：`src/scripts/step01_absolute_calibration.py`
- 主要职责：将样品和银镜测量计数转换为 `850-1100 nm` 波段的绝对反射率，并输出图表和标准中间 CSV

输入：
- `test_data/sample.csv`
  - 样品测量光谱
  - 约定曝光时间：100 ms
- `test_data/Ag-mirro.csv`
  - 银镜测量光谱
  - 约定曝光时间：25 ms
- `resources/GCC-1022系列xlsx.xlsx`
  - 厂家提供的银镜绝对反射率基准

核心处理流程：
- 自动识别 CSV 的波长列和强度列
- 截取 `850-1100 nm` 目标波段
- 对银镜信号按曝光时间做归一化
- 将厂家银镜基准插值到样品波长网格
- 计算绝对反射率：
  - `R_abs = (S_sample / S_mirror_norm) * R_mirror_ref`
- 对反射率曲线做 Savitzky-Golay 平滑

输出：
- `data/processed/target_reflectance.csv`
  - 关键列约定至少包含：
    - `Wavelength`
    - `R_smooth`
- `results/figures/absolute_reflectance_interference.png`

### 4.2 `step01b_cauchy_extrapolation.py`

- 文件位置：`src/scripts/step01b_cauchy_extrapolation.py`
- 主要职责：从 [LIT-0001] Fig. 3 的数字化 `ITO/CsFAPI` 折射率曲线中提取透明区，用 Cauchy 模型外推到 `1100 nm`，生成 step02 可直接消费的标准 `n-k` 中间件

输入：
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
  - [LIT-0001] Fig. 3 的数字化光学常数数据
  - 本步骤只使用 `series = ITO/CsFAPI` 且 `quantity = n` 的数据

当前模型假设：
- 只截取 `750-1000 nm` 的近红外透明区拟合 Cauchy 模型
- Cauchy 模型写作 `n(lambda) = A + B / (lambda_um^2)`
- 为保证数值稳定性，拟合时使用 `lambda_um = wavelength_nm / 1000`
- `750-1100 nm` 内统一强制 `k = 0`
- `1000-1100 nm` 为超出 [LIT-0001] 原始测量窗口的解析外推区

输出：
- `data/processed/CsFAPI_nk_extended.csv`
  - 列约定：
    - `Wavelength`
    - `n`
    - `k`
- `results/figures/cauchy_extrapolation_check.png`

### 4.3 `step02_tmm_inversion.py`

- 文件位置：`src/scripts/step02_tmm_inversion.py`
- 主要职责：读取 `step01` 输出的目标反射率、ITO 色散和 `step01b` 生成的 CsFAPI 扩展 `n-k` 中间件，执行包含 BEMA 表面粗糙度修正与 ITO 标量吸收补偿的三参数联合反演

输入：
- `data/processed/target_reflectance.csv`
  - 来自 `step01`
- `data/processed/CsFAPI_nk_extended.csv`
  - 来自 `step01b`
  - 用作 PVK 层在 `850-1100 nm` 的复折射率输入
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`
  - ITO 介电函数数据库
  - 脚本兼容两类情况：
    - MATLAB 可读 MAT
    - 实际为三列表格文本

当前模型假设：
- 波段：`850-1100 nm`
- 入射角：`0` 度
- 玻璃前表面按非相干处理
- 后侧薄膜堆栈按相干 TMM 处理
- ITO 厚度固定：`105 nm`
- NiOx 厚度固定：`20 nm`
- SAM 厚度固定：`2 nm`
- PVK 块体厚度 `d_bulk` 搜索范围：`400-650 nm`
- PVK 表面粗糙层厚度 `d_rough` 搜索范围：`0-100 nm`
- ITO 吸收缩放系数 `alpha_ito` 搜索范围：`0.1-20.0`
- PVK 采用 `step01b` 生成的 CsFAPI 扩展 `n-k` 中间件，并通过线性插值映射到目标波长网格
- 粗糙层采用 `50% PVK + 50% Air` 的 Bruggeman EMA 有效介质模型
- ITO 在进入 TMM 之前，锁定实部 `n` 不变，仅对虚部 `k` 施加标量吸收缩放
- 相干层堆栈为：`Glass -> ITO -> NiOx -> SAM -> PVK_Bulk -> PVK_Roughness -> Air`

核心处理流程：
- 读取目标绝对反射率
- 读取 `step01b` 生成的 CsFAPI 扩展 `n-k` 表
- 解析 ITO 的 `e1/e2` 数据并转为 `n + ik`
- 构建 ITO 复折射率插值器
- 根据 `alpha_ito` 对 ITO 的消光系数 `k` 做标量吸收放大
- 构建 PVK 复折射率插值器
- 根据块体 PVK 复介电常数计算 50/50 BEMA 粗糙层复折射率
- 计算宏观反射率：
  - 玻璃前表面菲涅尔反射
  - 玻璃后方包含粗糙层的薄膜堆栈相干 TMM
  - 再按非相干强度级联公式合成总反射率
- 使用 `lmfit` 的 `leastsq` 做三参数联合反演
- 输出最佳拟合图

输出：
- `results/figures/tmm_inversion_result.png`
- 终端打印：
  - 拟合厚度
  - `chi-square`
  - 优化状态

### 4.4 `step02_digitize_fapi_optical_constants.py`

- 文件位置：`src/scripts/step02_digitize_fapi_optical_constants.py`
- 主要职责：从 `LIT-0001` 的 Fig. 2 原图中提取 FAPI 的折射率 `n` 与消光系数 `κ` 两个子图数据，并输出单一 CSV 与 QA 图

输出：
- `resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv`
- `results/figures/phase02_fig2_fapi_optical_constants_digitized.png`
- `results/figures/phase02_fig2_fapi_optical_constants_overlay.png`
- `results/logs/phase02_fig2_fapi_digitization_notes.md`

### 4.5 `step02_digitize_csfapi_optical_constants.py`

- 文件位置：`src/scripts/step02_digitize_csfapi_optical_constants.py`
- 主要职责：从 `LIT-0001` 的 Fig. 3 原图中提取 CsFAPI 的折射率 `n` 与消光系数 `κ` 两个子图数据，并输出单一 CSV 与 QA 图

输出：
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
- `results/figures/phase02_fig3_csfapi_optical_constants_digitized.png`
- `results/figures/phase02_fig3a_csfapi_optical_constants_overlay.png`
- `results/figures/phase02_fig3b_csfapi_optical_constants_overlay.png`
- `results/logs/phase02_fig3_csfapi_digitization_notes.md`

### 4.6 `diagnostics_shape_mismatch.py`

- 文件位置：`src/scripts/diagnostics_shape_mismatch.py`
- 主要职责：在不修改主流程的前提下，复用 `step02` 的数据读取和 BEMA 基线模型，对条纹形状畸变的物理来源做诊断

输入：
- `data/processed/target_reflectance.csv`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`

核心诊断探针：
- Probe A：对 ITO 的近红外 `k` 施加长波增强缩放，测试 Drude 吸收失真假说
- Probe B：对 `d_bulk` 做高斯厚度平均，测试光斑内宏观厚度不均匀性
- Probe C：放开 PVK 的 Cauchy `B` 参数缩放，测试近红外色散斜率是否过平

输出：
- `results/figures/diagnostic_shape_analysis.png`
- `results/logs/phase02_shape_diagnostic_report.md`

## 5. Data Flow

当前项目主数据流如下：

```text
test_data/sample.csv
test_data/Ag-mirro.csv
resources/GCC-1022系列xlsx.xlsx
    -> step01_absolute_calibration.py
    -> data/processed/target_reflectance.csv

resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
    -> step01b_cauchy_extrapolation.py
    -> data/processed/CsFAPI_nk_extended.csv
    -> results/figures/cauchy_extrapolation_check.png

data/processed/target_reflectance.csv
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> step02_tmm_inversion.py (CsFAPI 扩展 n-k -> ITO 标量吸收补偿 -> BEMA 粗糙层修正 -> d_bulk + d_rough + alpha_ito 三参数反演)
    -> results/figures/tmm_inversion_result.png

data/processed/target_reflectance.csv
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> diagnostics_shape_mismatch.py
    -> results/figures/diagnostic_shape_analysis.png
    -> results/logs/phase02_shape_diagnostic_report.md

reference/Khan.../images/b3c499f799...
    -> step02_digitize_fapi_optical_constants.py
    -> resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv

reference/Khan.../images/4ad6d508...
reference/Khan.../images/885e29d3...
    -> step02_digitize_csfapi_optical_constants.py
    -> resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
```

可按 SOP 理解为：

1. `step01` 负责把原始计数校准成可用于物理建模的绝对反射率
2. `step01b` 把 [LIT-0001] 数字化 CsFAPI 曲线转换成标准近红外 `n-k` 中间件
3. `step02` 在消费标准 `n-k` 中间件后，先对 ITO 的消光系数 `k` 做标量吸收补偿，再通过 50/50 BEMA 将 PVK-Air 表面粗糙度折算为有效介质层
4. 当前脚本链已经具备“测量数据 -> 标准中间数据 + 文献外推中间数据 -> ITO 标量吸收 + BEMA 修正 TMM 三参数反演图表”的最小闭环
5. 诊断沙盒指出的 ITO 近红外吸收缺项，现已被并入主流程做解耦的标量吸收补偿

## 6. Key Physical / Numerical Assumptions

当前实现中最重要的物理和数值假设如下：

- 仅处理 `850-1100 nm` 波段
- 玻璃厚板不作为相干层直接进入 TMM 相位矩阵
- ITO 数据若波长量级大于 `2000`，则按 Angstrom 自动转为 nm
- 厂家银镜基准若数值范围大于 `1.5`，则按百分比转为 `0-1` 小数
- PVK 的近红外色散来源为 [LIT-0001] Fig. 3 的 `ITO/CsFAPI` 数字化 `n` 曲线，并通过 Cauchy 模型外推到 `1100 nm`
- `750-1100 nm` 内强制采用 `k = 0`
- `1000-1100 nm` 属于超出原始椭偏测量窗口的模型外推区
- 粗糙层采用 `50% PVK + 50% Air` 的 BEMA 有效介质
- ITO 的额外吸收以锁定实部 `n` 的标量参数 `alpha_ito` 表示
- 反演当前同时拟合 `d_bulk`、`d_rough` 与 `alpha_ito` 三个参数

这些假设是理解结果与后续扩展的关键锚点；若后续有改动，必须同步更新本文件。

## 7. Bug Ledger

当前尚未确认完全关闭的问题如下。

### 7.1 目录结构尚未收敛到规范态

- 表现：
  - 原始数据仍在 `test_data/`
  - 文献与拆解材料仍在 `reference/`
- 影响：
  - 新 Agent 容易在旧目录和新规范之间混淆
  - 不利于后续自动化脚本稳定约定路径
- 当前状态：
  - 已通过 `AGENTS.md` 明确新规范
  - 仓库实体结构尚未迁移

### 7.2 `step02` 尚未输出结构化反演结果文件

- 表现：
  - 目前只输出图像和终端打印
  - 尚未输出标准 CSV/JSON 记录最佳参数和拟合质量
- 影响：
  - 后续批量比较、回归测试和结果追踪不方便
- 当前状态：
  - 功能可用，但结果留痕不够完整

### 7.3 当前反演模型参数自由度较低

- 表现：
  - 当前仅反演 `d_bulk` 与 `d_rough`
  - ITO/NiOx/SAM 厚度与材料参数均固定
- 影响：
  - 双参数收敛仍不等于结构解释唯一
  - 对模型误差与参数耦合的吸收能力有限
- 当前状态：
  - 已比单参数模型更能吸收表面粗糙度导致的振幅偏差
  - 不适合作为最终物理解译结论

### 7.4 图像数字化结果不是原始实验表

- 表现：
  - `phase02_fig2_fapi_optical_constants_digitized.csv` 与 `phase02_fig3_csfapi_optical_constants_digitized.csv` 来自论文图像数字化
  - 不是作者公开补充材料中的原始数值表
- 影响：
  - 可用于复核趋势、建立先验或做近似对照
  - 不应表述为“绝对无误差的原始测量数据”
- 当前状态：
  - 已优先使用论文原图而非截图
  - 已输出重绘图与叠加图作为 QA 留痕

### 7.5 PVK 常数折射率临时分支已关闭

- 表现：
  - 先前用于 smoke test 的 `n=2.45, k=0` 常数锚定分支已从 `step02` 删除
- 影响：
  - 当前主流程已改为消费基于真实 CsFAPI 数字化数据外推得到的标准 `n-k` 中间件
  - “临时常数折射率”不再是主流程隐含假设
- 当前状态：
  - 已解决

### 7.6 BEMA 粗糙层升级直接用于压低理论振幅

- 表现：
  - 在相位已经基本对齐的前提下，平滑界面模型的理论振幅高于实测振幅
- 影响：
  - 引入 `PVK_Roughness` 有效介质层后，模型可通过顶部减反效应压低理论峰值，更接近实测约 `30%` 的振幅水平
- 当前状态：
  - 已纳入 `step02_tmm_inversion.py` 主流程
  - 后续仍需结合拟合结果持续验证振幅改进是否稳定

### 7.7 条纹形状畸变的主导根因已被定位，但尚未修入主流程

- 表现：
  - 在 BEMA 粗糙层已修复振幅后，主流程仍存在长波端托平和条纹跨度失配
- 影响：
  - `diagnostics_shape_mismatch.py` 的 Probe A 显示，ITO 近红外吸收增强可将形状误差显著压低
  - 这说明当前主流程的 ITO 吸收建模仍不足，是下一轮主流程升级的优先方向
- 当前状态：
  - 已通过 ITO 标量吸收补偿并入 `step02_tmm_inversion.py`
  - 当前主流程可直接检验“长波端畸变是否完全由底层吸收缺失主导”

## 8. Architecture Risks

### 8.1 复用逻辑仍未模块化

- 当前 `src/scripts/` 内部包含了大量可复用函数
- 若继续扩展更多步骤脚本，重复代码风险会快速上升
- 建议后续将以下逻辑下沉到 `src/core/`：
  - 列名识别与 CSV 读取
  - 波段裁剪与插值域校验
  - ITO 数据解析
  - Cauchy 外推
  - TMM 反射率计算

### 8.2 资源文件格式存在隐式脆弱性

- `ITO_20 Ohm_105 nm_e1e2.mat` 的扩展名与实际可解析内容不完全一致
- 当前代码已做 MAT/文本双分支兼容
- 但长期看应补资源索引文档，明确每个资源文件的真实格式与来源

### 8.3 缺少回归验证与数值基准

- 当前已有图像结果，但缺少：
  - 基准厚度的预期区间
  - 标准输入下的预期 `chi-square`
  - 自动化回归测试
- 这会导致后续重构时较难判断“模型真的没变”

### 8.4 图像数字化链路仍带有手工标定假设

- 当前 Fig. 2 / Fig. 3 数字化脚本依赖固定图框坐标和坐标轴范围
- 若后续换成新版 MinerU 图、原 PDF 裁图或其他论文图片，不能直接假定这套标定仍成立
- 建议后续把坐标框识别和图例剔除规则继续模块化，必要时加入人工校核步骤

### 8.5 PVK 色散已改为真实光谱外推，但外推边界仍需审慎

- “PVK 常数折射率锚定仍属临时验证假设”这一风险已关闭
- 当前主流程已基于 [LIT-0001] Fig. 3 的 `ITO/CsFAPI` 数字化数据，在 `750-1000 nm` 透明区进行 Cauchy 拟合并外推到 `1100 nm`
- 当前新增的主要风险是：
  - `1000-1100 nm` 属于超出原文测量窗口的外推区
  - 当前将 `k` 在近红外全部强制为 `0`
  - 数字化误差会直接传递到 Cauchy 参数 `A, B`

### 8.6 BEMA 双参数反演存在参数相关性风险

- `d_bulk` 与 `d_rough` 都会影响干涉振幅与相位，二者可能存在相关性
- 因此双参数数值收敛不自动等价于唯一物理解
- 当前升级可直接改善振幅匹配，但后续若用于定量结论，仍需通过更多先验或更多观测量约束参数空间

### 8.7 ITO 吸收修正已被诊断为关键缺项

- 独立诊断表明，ITO 近红外吸收增强比厚度不均匀性和 PVK 色散斜率修正更能同时修复长波托平与整体形状
- 这也是当前主流程优先引入 ITO 标量吸收补偿，而未先固化厚度高斯平均或 PVK Cauchy `B` 缩放的原因
- 后续仍需关注 `alpha_ito` 是否与 `d_bulk` / `d_rough` 存在新的参数相关性

### 8.8 结果文件命名尚未 Phase 化

- 当前图像文件名尚未显式带上 `phaseXX`
- 后续结果积累后，可能不利于多轮实验比较和回滚定位

## 9. Recent Update Summary

- 更新时间：`2026-04-06`
- 当前 Phase：`Phase 02`
- 本次新增/修改：
  - 在 `step02_tmm_inversion.py` 中以 `alpha_ito` 新增 ITO 标量吸收补偿
  - 将主流程从 BEMA 双参数反演升级为 `d_bulk + d_rough + alpha_ito` 三参数联合反演
  - 更新 `PROJECT_STATE.md` 以反映标量吸收补偿并入主流程
- 已验证结论：
  - ITO 近红外吸收增强是当前形状畸变的主导修复机制
  - 主流程现已具备基于 `alpha_ito` 的底层基底吸收修正闭环
- 仍待验证：
  - `1000-1100 nm` 外推段的物理可信度仍需后续用原始数据或独立测量交叉验证
  - `d_bulk`、`d_rough` 与 `alpha_ito` 的相关性是否会影响最终物理解读，还需后续继续评估

## 10. Recommended Next Actions

建议后续优先处理以下事项：

1. 建立 `data/raw/`，并把 `test_data/` 中实际原始测量 CSV 迁移到规范目录
2. 创建结构化反演结果输出文件，记录 `d_bulk`、`d_rough`、`alpha_ito`、`chi-square` 与外推参数 `A/B`
3. 将 `step01`/`step01b`/`step02` 中可复用逻辑下沉到 `src/core/`
4. 建立 `docs/RESOURCE_INDEX.md`，说明 ITO、银镜基准、论文资料与数字化资源的来源和格式
5. 建立 `README.md`，补齐项目运行入口、依赖安装和 Phase 概览

## 11. Update Rule

后续出现以下情况时，必须更新本文件：

- 新增或完成一个 Phase
- 调整目录结构
- 新增/删除关键脚本
- 改变中间文件格式
- 修改核心物理假设
- 新增重要未解决问题或关闭既有问题

更新时优先保证：
- 目录树准确
- 数据流准确
- 风险和问题列表准确
- 不堆砌无关历史对话内容
