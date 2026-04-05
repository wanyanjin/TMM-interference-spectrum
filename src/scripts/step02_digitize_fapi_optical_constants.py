from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_IMAGE = PROJECT_ROOT / (
    "reference/Khan 等 - 2024 - Optical constants manipulation of formamidinium "
    "lead iodide perovskites ellipsometric and spectrosc.pdf-64661b05-c239-4731-a3f7-"
    "2c0456a4df66/images/b3c499f799c0be47f32bf58a0c588af9c30db72b33cb6d3577d4c4317a76a48d.jpg"
)
OUTPUT_CSV = PROJECT_ROOT / "resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv"
OUTPUT_FIGURE = PROJECT_ROOT / "results/figures/phase02_fig2_fapi_optical_constants_digitized.png"
OUTPUT_OVERLAY = PROJECT_ROOT / "results/figures/phase02_fig2_fapi_optical_constants_overlay.png"
OUTPUT_LOG = PROJECT_ROOT / "results/logs/phase02_fig2_fapi_digitization_notes.md"


@dataclass(frozen=True)
class PanelConfig:
    panel: str
    quantity: str
    x0: int
    y0: int
    x1: int
    y1: int
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    keep_components: int
    component_min_area: int
    erase_regions: tuple[tuple[int, int, int, int], ...] = ()


PANELS = (
    PanelConfig(
        panel="a",
        quantity="n",
        x0=62,
        y0=17,
        x1=319,
        y1=222,
        x_min=450.0,
        x_max=1000.0,
        y_min=1.2,
        y_max=2.5,
        keep_components=1,
        component_min_area=200,
    ),
    PanelConfig(
        panel="b",
        quantity="kappa",
        x0=375,
        y0=15,
        x1=630,
        y1=224,
        x_min=450.0,
        x_max=1000.0,
        y_min=0.0,
        y_max=1.2,
        keep_components=10,
        component_min_area=20,
        erase_regions=((100, 0, 145, 40),),
    ),
)


SERIES_CONFIG = {
    "Glass/FAPI": {
        "mask_fn": lambda hsv: cv2.inRange(hsv, (0, 70, 80), (10, 255, 255))
        | cv2.inRange(hsv, (170, 70, 80), (180, 255, 255)),
        "plot_color": "#d62728",
    },
    "ITO/FAPI": {
        "mask_fn": lambda hsv: cv2.inRange(hsv, (90, 70, 50), (140, 255, 255)),
        "plot_color": "#1f3fff",
    },
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def select_components(mask: np.ndarray, keep_components: int, component_min_area: int) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    components: list[tuple[int, int]] = []
    for component_id in range(1, count):
        area = int(stats[component_id, cv2.CC_STAT_AREA])
        if area >= component_min_area:
            components.append((area, component_id))

    components.sort(reverse=True)
    filtered = np.zeros_like(mask)
    for _, component_id in components[:keep_components]:
        filtered[labels == component_id] = 255
    return filtered


def erase_regions(mask: np.ndarray, regions: tuple[tuple[int, int, int, int], ...]) -> np.ndarray:
    cleaned = mask.copy()
    for x0, y0, x1, y1 in regions:
        cleaned[y0:y1, x0:x1] = 0
    return cleaned


def extract_centerline(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    xs: list[int] = []
    ys: list[float] = []
    for x in range(mask.shape[1]):
        y_idx = np.where(mask[:, x] > 0)[0]
        if y_idx.size:
            xs.append(x)
            ys.append(float(np.median(y_idx)))

    if not xs:
        raise RuntimeError("No curve pixels detected in panel.")

    x_array = np.asarray(xs, dtype=float)
    y_array = np.asarray(ys, dtype=float)

    full_x = np.arange(int(x_array.min()), int(x_array.max()) + 1, dtype=float)
    full_y = np.interp(full_x, x_array, y_array)
    return full_x, full_y


def pixel_to_data(panel: PanelConfig, x_pixels: np.ndarray, y_pixels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    wavelength_nm = panel.x_min + (x_pixels / (panel.x1 - panel.x0)) * (panel.x_max - panel.x_min)
    values = panel.y_max - (y_pixels / (panel.y1 - panel.y0)) * (panel.y_max - panel.y_min)
    return wavelength_nm, values


def build_overlay(base_bgr: np.ndarray, extracted: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
    overlay = base_bgr.copy()
    for panel in PANELS:
        for series_name, config in SERIES_CONFIG.items():
            x_values, y_values = extracted[(panel.panel, series_name)]
            color_hex = config["plot_color"].lstrip("#")
            rgb = tuple(int(color_hex[i : i + 2], 16) for i in (0, 2, 4))
            bgr = (rgb[2], rgb[1], rgb[0])
            points = np.column_stack(
                [
                    np.round(x_values + panel.x0).astype(int),
                    np.round(y_values + panel.y0).astype(int),
                ]
            )
            for x, y in points:
                cv2.circle(overlay, (int(x), int(y)), 1, bgr, thickness=-1)
    return overlay


def write_log(output: Path, dataframe: pd.DataFrame) -> None:
    checks = (
        dataframe.groupby(["panel", "series"])
        .agg(
            wavelength_min_nm=("wavelength_nm", "min"),
            wavelength_max_nm=("wavelength_nm", "max"),
            value_min=("value", "min"),
            value_max=("value", "max"),
        )
        .reset_index()
    )
    check_lines = [
        "| panel | series | wavelength_min_nm | wavelength_max_nm | value_min | value_max |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in checks.itertuples(index=False):
        check_lines.append(
            "| "
            f"{row.panel} | {row.series} | {row.wavelength_min_nm:.3f} | {row.wavelength_max_nm:.3f} | "
            f"{row.value_min:.6f} | {row.value_max:.6f} |"
        )
    lines = [
        "# Phase 02 Fig. 2 FAPI 光学常数图数字化说明",
        "",
        "- 来源文献：`[LIT-0001] Khan et al. (2024)`",
        f"- 源图路径：`{SOURCE_IMAGE.relative_to(PROJECT_ROOT)}`",
        "- 提取对象：Fig. 2 中 (a) 折射率 `n` 与 (b) 消光系数 `κ` 两个子图",
        "- 提取方法：基于论文原始 MinerU 导出的图像做颜色分割与像素坐标标定，不使用截图二次压缩图。",
        "- 采样策略：保留曲线在原图像素列上的原生采样，不向 1 nm 网格做额外插值。",
        "- 精度边界：该 CSV 是“图像数字化数据”，不是论文作者公开的原始数值表；其准确度受原始图像分辨率和线宽限制。",
        "",
        "## 轴标定",
        "",
        "- Panel (a): `x = 450-1000 nm`, `y = 1.2-2.5`",
        "- Panel (b): `x = 450-1000 nm`, `y = 0.0-1.2`",
        "- 标定依据：图框边界、刻度位置和正文描述相互校对；其中 Panel (a) 顶部边界高于 `2.4` 刻度半个主刻度，对应 `2.5`。",
        "",
        "## 数据范围检查",
        "",
        *check_lines,
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_parent(OUTPUT_CSV)
    ensure_parent(OUTPUT_FIGURE)
    ensure_parent(OUTPUT_OVERLAY)
    ensure_parent(OUTPUT_LOG)

    source_bgr = cv2.imread(str(SOURCE_IMAGE))
    if source_bgr is None:
        raise FileNotFoundError(f"Failed to read source image: {SOURCE_IMAGE}")
    source_hsv = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2HSV)

    rows: list[dict[str, object]] = []
    extracted_pixels: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]] = {}

    for panel in PANELS:
        panel_hsv = source_hsv[panel.y0 : panel.y1 + 1, panel.x0 : panel.x1 + 1]
        for series_name, config in SERIES_CONFIG.items():
            raw_mask = config["mask_fn"](panel_hsv)
            raw_mask = erase_regions(raw_mask, panel.erase_regions)
            filtered_mask = select_components(
                raw_mask,
                keep_components=panel.keep_components,
                component_min_area=panel.component_min_area,
            )
            x_pixels, y_pixels = extract_centerline(filtered_mask)
            wavelength_nm, values = pixel_to_data(panel, x_pixels, y_pixels)
            extracted_pixels[(panel.panel, series_name)] = (x_pixels, y_pixels)

            for wavelength_nm_i, value_i in zip(wavelength_nm, values, strict=True):
                rows.append(
                    {
                        "lit_id": "LIT-0001",
                        "figure": "Fig. 2",
                        "panel": panel.panel,
                        "quantity": panel.quantity,
                        "series": series_name,
                        "wavelength_nm": round(float(wavelength_nm_i), 6),
                        "value": round(float(value_i), 6),
                        "source_image": str(SOURCE_IMAGE.relative_to(PROJECT_ROOT)),
                        "digitization_basis": "paper_raster_curve",
                    }
                )

    dataframe = pd.DataFrame(rows)
    dataframe.to_csv(OUTPUT_CSV, index=False)

    plt.rcParams["font.family"] = "DejaVu Sans"
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    for ax, panel in zip(axes, PANELS, strict=True):
        panel_df = dataframe[dataframe["panel"] == panel.panel]
        for series_name, config in SERIES_CONFIG.items():
            series_df = panel_df[panel_df["series"] == series_name]
            ax.plot(
                series_df["wavelength_nm"],
                series_df["value"],
                color=config["plot_color"],
                linewidth=2.0,
                label=series_name,
            )
        ax.set_xlim(panel.x_min, panel.x_max)
        ax.set_ylim(panel.y_min, panel.y_max)
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("n" if panel.quantity == "n" else "κ")
        ax.set_title(f"Fig. 2({panel.panel}) digitized {panel.quantity}")
        ax.grid(alpha=0.25, linewidth=0.5)
        ax.legend(frameon=False)
    figure.savefig(OUTPUT_FIGURE, dpi=220)
    plt.close(figure)

    overlay_bgr = build_overlay(source_bgr, extracted_pixels)
    cv2.imwrite(str(OUTPUT_OVERLAY), overlay_bgr)

    write_log(OUTPUT_LOG, dataframe)

    print(f"Saved CSV: {OUTPUT_CSV}")
    print(f"Saved figure: {OUTPUT_FIGURE}")
    print(f"Saved overlay: {OUTPUT_OVERLAY}")
    print(f"Saved log: {OUTPUT_LOG}")


if __name__ == "__main__":
    main()
