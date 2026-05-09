# CURRENT_TASK.md

## 当前任务
`Phase 09E：refractiveindex.info 材料来源接入`

## 本轮目标
- 将 `Si` 与 `SiO2` 从 `refractiveindex.info` 收入仓库
- 保存 raw `CSV` 与 `Full database record`
- 生成标准化 `n/k` CSV 与索引 manifest
- 将材料来源优先级规则写入项目规范

## 完成状态
- 已新增正式抓取脚本：`src/scripts/step09e_fetch_refractiveindex_materials.py`
- 目标材料：
  - `Si -> Schinke 2015`
  - `SiO2 -> Malitson 1965`
- 输出目录：
  - `resources/refractiveindex_info/raw/`
  - `resources/refractiveindex_info/normalized/`
- 已生成：
  - raw `CSV` 与 `Full database record`
  - 标准化 `n/k` CSV
  - `refractiveindex_info_index.json`
- 已补：
  - 单元测试
  - CLI 文档
  - 材料来源优先级规则

## 待办
1. 清理并提交 Phase 09E 相关文件。
