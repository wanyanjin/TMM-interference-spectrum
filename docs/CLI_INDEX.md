# CLI_INDEX.md

本文档是项目 CLI 总目录。所有正式 CLI 的新增、状态变化、参数或行为变更，都必须同步更新本索引与对应 `docs/cli/*.md` 详细文档。

---

## CLI Registry

| CLI 名称 | 类型 | 状态 | 主要用途 | 入口命令 | 详细文档路径 | 关联 Phase |
| --- | --- | --- | --- | --- | --- | --- |
| `reflectance-calibration` | calibration | planned | 统一绝对反射率标定入口（样品/参比） | `python -m src.cli.reflectance_calibration` | `docs/cli/reflectance_calibration.md` | Phase 01 / Phase 08 |
| `reference-comparison` | analysis | active | 比较 `glass/PVK` 在 `glass/Ag` 与 `Ag mirror` 双参比口径下的反射率并输出 TMM 诊断（主审查 500-750 nm） | `python src/cli/reference_comparison.py --sample-csv <...> --reference-csv <...> [--comparison-mode dual_reference --ag-mirror-csv <...> --background-csv <...>]` | `docs/cli/reference_comparison.md` | Phase 08 |
| `phase07-dual-window-inversion` | inversion | script-only | 双窗联合反演流程入口 | `python src/scripts/step07_dual_window_inversion.py` | `docs/cli/phase07_dual_window_inversion.md` | Phase 07 |
| `phase06-hdr-calibration` | calibration | script-only | HDR 绝对反射率单样本/批处理标定 | `python src/scripts/step06_single_sample_hdr_absolute_calibration.py` / `python src/scripts/step06_batch_hdr_calibration.py` | `docs/cli/phase06_hdr_calibration.md` | Phase 06 |

---

## 状态定义

- `planned`: 已纳入路线图，尚未形成正式 CLI 实现
- `active`: 已有正式 CLI 实现并有完整文档
- `deprecated`: 保留兼容但不建议新流程继续使用
- `experimental`: 试验性 CLI，接口可能变化
- `script-only`: 当前仅有脚本入口，尚未标准化为正式 CLI
