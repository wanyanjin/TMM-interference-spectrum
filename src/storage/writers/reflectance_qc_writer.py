from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from domain.reflectance import ReflectanceQCResult
from domain.run_manifest import ToolRunManifest


def write_processed_reflectance_csv(result: ReflectanceQCResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(
        {
            "wavelength_nm": result.wavelength_nm,
            "reference_intensity_raw": result.reference_intensity_raw,
            "sample_intensity_raw": result.sample_intensity_raw,
            "reference_intensity_processed": result.reference_intensity_processed,
            "sample_intensity_processed": result.sample_intensity_processed,
            "reference_reflectance": result.reference_reflectance,
            "sample_reference_ratio": result.sample_reference_ratio,
            "calculated_reflectance": result.calculated_reflectance,
            "valid_mask": result.valid_mask,
            "mask_reason": result.mask_reason,
        }
    )
    frame.to_csv(output_path, index=False)
    return output_path


def write_qc_summary_json(
    result: ReflectanceQCResult,
    output_path: Path,
    manifest: ToolRunManifest | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "overall_status": result.qc_summary.overall_status,
        "metrics": result.qc_summary.metrics,
        "flags": [asdict(flag) for flag in result.qc_summary.flags],
        "metadata": result.qc_summary.metadata,
    }
    if manifest is not None:
        payload["manifest"] = asdict(manifest)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def write_qc_report_md(
    result: ReflectanceQCResult,
    output_path: Path,
    manifest: ToolRunManifest | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_lines = "\n".join(
        f"- `{name}`: {value}"
        for name, value in result.qc_summary.metrics.items()
    )
    flag_lines = "\n".join(
        f"- `{flag.severity.upper()}` `{flag.name}`: {flag.message}"
        for flag in result.qc_summary.flags
    ) or "- 无附加 flags。"

    manifest_lines = "- 未提供 manifest。"
    if manifest is not None:
        manifest_lines = "\n".join(
            [
                f"- tool_name: `{manifest.tool_name}`",
                f"- run_id: `{manifest.run_id}`",
                f"- inputs: `{manifest.inputs}`",
                f"- outputs: `{manifest.outputs}`",
            ]
        )

    metadata = result.qc_summary.metadata
    report = f"""# Reflectance QC Report

## 计算公式

$$
R_\\mathrm{{sample}}(\\lambda)
=
\\frac{{I_\\mathrm{{sample}}(\\lambda)}}{{I_\\mathrm{{reference}}(\\lambda)}}
R_\\mathrm{{reference}}(\\lambda)
$$

## 输入文件

{manifest_lines}

## 参数

- 波长范围: `{metadata.get("wavelength_min_nm")}` - `{metadata.get("wavelength_max_nm")}` nm
- 是否插值: `{metadata.get("interpolation_used")}`
- 是否曝光归一化: `{metadata.get("exposure_normalization_enabled")}`
- reference_type: `{metadata.get("reference_type")}`

## QC 结果

- overall_status: `{result.qc_summary.overall_status}`

## QC Metrics

{metrics_lines}

## 主要风险解释

{flag_lines}

## 输出文件路径

- processed_reflectance.csv
- qc_summary.json
- qc_report.md

## 说明

- 本轮只提供最小 CLI + workflow 闭环，不输出 GUI 图像。
- PNG/交互式图查看留给后续 visualization / GUI 阶段。
"""
    output_path.write_text(report, encoding="utf-8")
    return output_path
