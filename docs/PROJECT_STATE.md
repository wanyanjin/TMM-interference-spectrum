# PROJECT_STATE.md

本文件用于持续同步 `TMM-interference-spectrum` 项目的当前状态，是后续 AI Agent 和架构师恢复上下文的首要入口。

## 1. Current Snapshot

- 更新时间：2026-04-05
- 当前判断 Phase：`Phase 02`
- 阶段定义：`绝对反射率标定 -> TMM 基准前向/反演闭环`
- 当前可用能力：
  - 已有 `step01_absolute_calibration.py`，可将样品与银镜原始计数转换为绝对反射率
  - 已有 `step02_tmm_inversion.py`，可基于 TMM + LM 对 PVK 厚度进行单参数反演
  - 已有 `step02_digitize_fapi_optical_constants.py`，可从 `LIT-0001` 的 Fig. 2 原图数字化提取 FAPI 的 `n/κ` 曲线并输出 QA 图
  - 已产出基础图表结果与标准中间文件 `data/processed/target_reflectance.csv`
  - 已加入 `step02_tmm_inversion.py` 的 PVK 常数折射率 smoke test 分支，用于验证振幅是否受 PVK 近红外折射率锚定支配
- 当前未完成内容：
  - 尚未建立 `src/core/` 公共物理模块
  - 尚未把历史目录完全迁移到 `AGENTS.md` 规定的新结构
  - 尚未形成规范化的 Phase 日志、资源索引和问题台账

## 2. Current Directory Tree

以下目录树基于当前仓库实际状态整理，仅保留关键层级和关键文件。

```text
TMM-interference-spectrum/
├── AGENTS.md
├── docs/
│   └── PROJECT_STATE.md
├── src/
│   └── scripts/
│       ├── step01_absolute_calibration.py
│       ├── step02_digitize_fapi_optical_constants.py
│       └── step02_tmm_inversion.py
├── data/
│   └── processed/
│       └── target_reflectance.csv
├── resources/
│   ├── digitized/
│   │   └── phase02_fig2_fapi_optical_constants_digitized.csv
│   ├── GCC-1022系列xlsx.xlsx
│   ├── ITO_20 Ohm_105 nm_e1e2.mat
│   ├── CsFAPI_TL_parameters_and_formulas.md
│   └── MinerU-0.13.1-arm64.dmg
├── results/
│   ├── figures/
│   │   ├── absolute_reflectance_interference.png
│   │   ├── phase02_fig2_fapi_optical_constants_digitized.png
│   │   ├── phase02_fig2_fapi_optical_constants_overlay.png
│   │   └── tmm_inversion_result.png
│   └── logs/
│       └── phase02_fig2_fapi_digitization_notes.md
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
- `reference/` 目前存放论文拆解结果，按新规范更适合逐步并入 `resources/` 或 `docs/`
- `src/core/` 尚不存在，脚本中的复用逻辑目前仍散落在 `src/scripts/`
- `results/logs/` 尚未建立
- 项目根尚无 `README.md`

这些偏差当前不会阻断现有流程，但属于后续需要收敛的结构债务。

## 4. Script SOP

### 4.1 `step01_absolute_calibration.py`

- 文件位置：`src/scripts/step01_absolute_calibration.py`
- 主要职责：将样品和银镜测量计数转换为 850-1100 nm 波段的绝对反射率，并输出图表和标准中间 CSV

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
- 截取 850-1100 nm 目标波段
- 对银镜信号按曝光时间做归一化
- 将厂家银镜基准插值到样品波长网格
- 计算绝对反射率：
  - `R_abs = (S_sample / S_mirror_norm) * R_mirror_ref`
- 对反射率曲线做 Savitzky-Golay 平滑

输出：
- `data/processed/target_reflectance.csv`
  - 当前是 `step02` 的标准输入
  - 关键列约定至少包含：
    - `Wavelength`
    - `R_smooth`
- `results/figures/absolute_reflectance_interference.png`

### 4.2 `step02_tmm_inversion.py`

- 文件位置：`src/scripts/step02_tmm_inversion.py`
- 主要职责：读取 `step01` 输出的目标反射率，结合 ITO 色散和 PVK 近红外折射率模型，执行单参数厚度反演

输入：
- `data/processed/target_reflectance.csv`
  - 来自 `step01`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`
  - ITO 介电函数数据库
  - 脚本兼容两类情况：
    - MATLAB 可读 MAT
    - 实际为三列表格文本

当前模型假设：
- 波段：850-1100 nm
- 入射角：0 度
- 玻璃前表面按非相干处理
- 后侧薄膜堆栈按相干 TMM 处理
- ITO 厚度固定：105 nm
- NiOx 厚度固定：20 nm
- SAM 厚度固定：2 nm
- PVK 为唯一反演参数
- PVK 厚度搜索范围：400-650 nm
- 当前临时 smoke test 分支中，`get_pvk_nk()` 直接将 PVK 视为 `n=2.45, k=0` 的常数无吸收层

核心处理流程：
- 读取目标绝对反射率
- 解析 ITO 的 `e1/e2` 数据并转为 `n + ik`
- 构建 ITO 复折射率插值器
- 构造 PVK 近红外常数折射率 smoke test 模型
- 计算宏观反射率：
  - 玻璃前表面菲涅尔反射
  - 玻璃后方薄膜堆栈相干 TMM
  - 再按非相干强度级联公式合成总反射率
- 使用 `lmfit` 的 `leastsq` 做单参数厚度反演
- 输出最佳拟合图

输出：
- `results/figures/tmm_inversion_result.png`
- 终端打印：
  - 拟合厚度
  - `chi-square`
  - 优化状态

### 4.3 `step02_digitize_fapi_optical_constants.py`

- 文件位置：`src/scripts/step02_digitize_fapi_optical_constants.py`
- 主要职责：从 `LIT-0001` 的 Fig. 2 原图中提取 FAPI 的折射率 `n` 与消光系数 `κ` 两个子图数据，并输出单一 CSV 与 QA 图

输入：
- `reference/Khan.../images/b3c499f799c0be47f32bf58a0c588af9c30db72b33cb6d3577d4c4317a76a48d.jpg`
  - `LIT-0001` 的 Fig. 2 原图

核心处理流程：
- 基于原图而不是截图做数字化
- 对 Panel (a)/(b) 分别做图框坐标标定
- 通过红/蓝曲线颜色分割提取 `Glass/FAPI` 与 `ITO/FAPI`
- 对提取结果生成重绘图和原图叠加图进行 QA
- 输出数字化说明日志，明确“图像数字化数据”而非作者原始数值表

输出：
- `resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv`
- `results/figures/phase02_fig2_fapi_optical_constants_digitized.png`
- `results/figures/phase02_fig2_fapi_optical_constants_overlay.png`
- `results/logs/phase02_fig2_fapi_digitization_notes.md`

## 5. Data Flow

当前项目主数据流如下：

```text
test_data/sample.csv
test_data/Ag-mirro.csv
resources/GCC-1022系列xlsx.xlsx
    -> step01_absolute_calibration.py
    -> data/processed/target_reflectance.csv
    -> step02_tmm_inversion.py + resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> results/figures/tmm_inversion_result.png

reference/Khan.../images/b3c499f799...
    -> step02_digitize_fapi_optical_constants.py
    -> resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv
    -> results/figures/phase02_fig2_fapi_optical_constants_digitized.png
    -> results/figures/phase02_fig2_fapi_optical_constants_overlay.png
```

可按 SOP 理解为：

1. `step01` 负责把原始计数校准成可用于物理建模的绝对反射率
2. `step02` 只消费标准中间文件，不再复制前置标定逻辑
3. 当前脚本链已经具备“测量数据 -> 标准中间数据 -> TMM 反演图表”的最小闭环

## 6. Key Physical / Numerical Assumptions

当前实现中最重要的物理和数值假设如下：

- 仅处理 850-1100 nm 波段
- 玻璃厚板不作为相干层直接进入 TMM 相位矩阵
- ITO 数据若波长量级大于 2000，则按 Angstrom 自动转为 nm
- 厂家银镜基准若数值范围大于 1.5，则按百分比转为 0-1 小数
- PVK 的正式文献色散来源仍是 `LIT-0001` 对应的三振子 Tauc-Lorentz 参数，但当前脚本已临时切换为用户指定的 `n=2.45, k=0` 常数锚定分支
- 反演当前仅对 `d_pvk` 一个参数进行拟合

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
  - 目前仅反演 PVK 厚度 `d_pvk`
  - ITO/NiOx/SAM 厚度与材料参数均固定
- 影响：
  - 单参数收敛不等于结构解释唯一
  - 对模型误差与参数耦合的吸收能力有限
- 当前状态：
  - 适合作为基准闭环
  - 不适合作为最终物理解译结论

### 7.4 图像数字化结果不是原始实验表

- 表现：
  - `phase02_fig2_fapi_optical_constants_digitized.csv` 来自论文图像数字化
  - 不是作者公开补充材料中的原始数值表
- 影响：
  - 可用于复核趋势、建立先验或做近似对照
  - 不应表述为“绝对无误差的原始测量数据”
- 当前状态：
  - 已优先使用论文原图而非截图
  - 已输出重绘图与叠加图作为 QA 留痕

## 8. Architecture Risks

### 8.1 复用逻辑仍未模块化

- 当前 `src/scripts/` 内部包含了大量可复用函数
- 若继续扩展更多步骤脚本，重复代码风险会快速上升
- 建议后续将以下逻辑下沉到 `src/core/`：
  - 列名识别与 CSV 读取
  - 波段裁剪与插值域校验
  - ITO 数据解析
  - Tauc-Lorentz 色散计算
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

- 当前 Fig. 2 数字化脚本依赖固定图框坐标和坐标轴范围
- 若后续换成新版 MinerU 图、原 PDF 裁图或其他论文图片，不能直接假定这套标定仍成立
- 建议后续把坐标框识别和图例剔除规则继续模块化，必要时加入人工校核步骤

### 8.5 PVK 常数折射率锚定仍属临时验证假设

- 当前 `step02_tmm_inversion.py` 已按用户要求将 `get_pvk_nk()` 切换为常数 `n=2.45, k=0`
- 该值用于 smoke test，目的是验证振幅偏低是否主要来自 PVK 与邻层阻抗匹配失真
- 若该分支显著改善拟合振幅，下一步仍需回到可追溯的文献或实验数据，建立正式近红外 `n-k` 基准

### 8.6 结果文件命名尚未 Phase 化

- 当前图像文件名尚未显式带上 `phaseXX`
- 后续结果积累后，可能不利于多轮实验比较和回滚定位

## 9. Recent Update Summary

- 更新时间：`2026-04-05`
- 当前 Phase：`Phase 02`
- 本次新增/修改：
  - 新增 `step02_digitize_fapi_optical_constants.py`
  - 新增 `resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv`
  - 新增 Fig. 2 数字化 QA 图与日志
- 已验证结论：
  - 已成功从论文原图重建 FAPI 的 `n/κ` 曲线
  - 重绘结果与原图叠加后整体贴合，无明显跑偏
- 仍待验证：
  - 若后续需要高精度建模，仍应优先寻找作者原始数值表或补充材料，而不是长期依赖图像数字化值

## 10. Recommended Next Actions

建议后续优先处理以下事项：

1. 建立 `data/raw/`，并把 `test_data/` 中实际原始测量 CSV 迁移到规范目录
2. 创建 `results/logs/` 和结构化反演结果输出文件
3. 将 `step01`/`step02` 中可复用逻辑下沉到 `src/core/`
4. 建立 `docs/RESOURCE_INDEX.md`，说明 ITO、银镜基准、论文资料的来源和格式
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
