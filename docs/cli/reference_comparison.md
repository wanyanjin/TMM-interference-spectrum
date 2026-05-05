# CLI: reference-comparison

状态：`planned`

## 1. 功能定位

为 Phase 08 参比几何验证提供统一 CLI 入口，对 `glass/PVK` 与 `glass/Ag`、`Ag mirror` 两类参比口径进行可追溯比较。

## 2. 适用场景

- 同一样品在不同参比模型下的反射率重建对比
- 参比选择对残差结构和拟合稳定性的影响评估
- 进入正式实验/分析流程前的参比口径审计

## 3. 入口命令

规划入口（待实现）：

```bash
python -m src.cli.reference_comparison
```

## 4. 参数说明

规划参数（待实现）：

- 样品输入路径（`glass/PVK`）
- 参比输入路径（`glass/Ag`）
- 参比输入路径（`Ag mirror`）
- 材料光学常数输入（Ag/PVK `n-k`）
- 输出目录
- 波长窗口与单位声明

## 5. 输入文件要求

- `glass/PVK` 样品数据
- `glass/Ag` 参比数据
- `Ag mirror` 参比数据
- Ag/PVK 光学常数表（`n-k`）

所有输入需通过统一参数校验，不允许隐式单位假设。

## 6. 输出文件

规划输出（待实现）：

- 两类参比标定得到的实验反射率结果表
- 对应 TMM 理论反射率结果表
- 指标汇总：`residual / RMSE / MAE / bias / shape correlation`
- QA 图（至少含叠图与残差图）
- summary 与 manifest-like 记录

## 7. 执行原理

同一目标样品在两种参比口径下分别标定，再与理论反射率对齐并计算对比指标，输出可审计差异。

## 8. 调用的核心接口

规划：复用 `src/core/` 与后续 `src/workflows/` 的统一接口，不在 CLI 内复制物理公式。

## 9. 数据流方向

`raw/processed input -> CLI 解析与校验 -> core/workflow -> data/processed -> results/figures + results/logs/report -> summary`

## 10. 校验与错误行为

- 参比类型必须显式声明
- 波长范围、单位、列名、反射率单位不一致时应报错并中止
- 输入缺失时应给出可定位错误信息

## 11. GUI 调用建议

GUI 后续应调用同一参数模型与同一 workflow，不得另写参比比较业务逻辑。

## 12. 示例

待 CLI 实现后补充可执行示例。

## 13. 版本与维护记录

- `v0`（planned）：文档草案建立，用于 Phase 08 下一步实现准备。

## 关键约束

`glass/Ag` 与 `Ag mirror` 参比模型不能混用，必须在输入、计算与输出摘要中显式区分。

