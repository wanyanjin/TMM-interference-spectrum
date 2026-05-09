# CLI: refractiveindex-material-fetch

状态：`active`

## 1. 功能定位

从 `refractiveindex.info` 抓取指定材料页的结构化来源文件，并生成项目统一的标准化 `n/k` CSV 与索引 manifest。

## 2. 适用场景

- 为后续 TMM、材料替换、叠层扩展准备可追溯 `Si` / `SiO2` 光学常数来源
- 将网站来源固化到仓库，避免后续重复手工查找
- 为未来 `aligned/overlay nk` 组装流程提供稳定材料入口

## 3. 入口命令

默认抓取 `Si` 与 `SiO2`：

```bash
python src/scripts/step09e_fetch_refractiveindex_materials.py
```

仅抓取 `Si`：

```bash
python src/scripts/step09e_fetch_refractiveindex_materials.py --materials Si
```

Dry-run：

```bash
python src/scripts/step09e_fetch_refractiveindex_materials.py --dry-run
```

## 4. 参数说明

- `--materials`: 目标材料列表；当前仅支持 `Si`、`SiO2`
- `--output-root`: 输出根目录，默认 `resources/refractiveindex_info`
- `--timeout-seconds`: 单次网络请求超时，默认 `30`
- `--dry-run`: 仅检查配置与计划下载项，不写文件

## 5. 输入与来源固定值

- `Si` 页面：`https://refractiveindex.info/?shelf=main&book=Si&page=Schinke`
- `SiO2` 页面：`https://refractiveindex.info/?shelf=main&book=SiO2&page=Malitson`

每个材料页固定保存两类 raw 文件：

- 网站 `CSV` 导出
- `Full database record`（YAML）

说明：

- 网站 `CSV` 不保证包含完整 `k` 列；标准化 `n/k` 结果以 YAML 解析为准

## 6. 输出文件

输出根目录：

- `resources/refractiveindex_info/raw/Si/`
- `resources/refractiveindex_info/raw/SiO2/`
- `resources/refractiveindex_info/normalized/`
- `resources/refractiveindex_info/refractiveindex_info_index.json`

当前标准化结果：

- `normalized/si_schinke_2015_nk.csv`
- `normalized/sio2_malitson_1965_nk_400_1100nm.csv`

## 7. 执行原理

- `Si`：解析 `Schinke` 页 YAML 中的 `tabulated nk`
- `SiO2`：解析 `Malitson` 页 YAML 中的 `formula 1`
- `SiO2` 标准化规则：
  - 在 `400-1100 nm`、`1 nm` 步长上评价公式
  - 显式写入 `k = 0`
  - 在 manifest 标记为 bulk fused silica / formula-derived 口径

## 8. 调用接口

- 入口脚本：`src/scripts/step09e_fetch_refractiveindex_materials.py`
- 当前为 script-style CLI，不依赖额外第三方 YAML 解析库

## 9. 数据流

`refractiveindex.info page -> raw CSV + raw YAML -> normalized nk CSV -> refractiveindex_info_index.json`

## 10. 错误行为

- 页面下载失败：报错退出
- YAML 中缺少 `tabulated nk` 或 `formula 1`：报错退出
- 标准化 CSV 出现 `NaN/Inf`、负 `k` 或波长非递增：报错退出
- `SiO2` 公式覆盖不足 `400-1100 nm`：报错退出

## 11. GUI 调用建议

- GUI 不直接联网抓材料
- 若后续 GUI 需要材料选择，应调用该 CLI 或其后续 workflow 封装

## 12. 维护记录

- `v1`（Phase 09E）：引入 `Si/SiO2` 的 `refractiveindex.info` 原始来源、标准化 CSV 与索引 manifest
