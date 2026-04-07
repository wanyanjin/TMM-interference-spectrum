from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_IMAGES = {
    "a": PROJECT_ROOT
    / (
        "reference/Khan 等 - 2024 - Optical constants manipulation of formamidinium "
        "lead iodide perovskites ellipsometric and spectrosc.pdf-64661b05-c239-4731-a3f7-"
        "2c0456a4df66/images/4ad6d50871967bd68ad9d2d4b0a12bb3fe5adf116e9eec0d34d4752f2f7dac43.jpg"
    ),
    "b": PROJECT_ROOT
    / (
        "reference/Khan 等 - 2024 - Optical constants manipulation of formamidinium "
        "lead iodide perovskites ellipsometric and spectrosc.pdf-64661b05-c239-4731-a3f7-"
        "2c0456a4df66/images/885e29d3301c8a26446578a1fe59d2783c89f227369fe031c7e24c763be6dc1c.jpg"
    ),
}
OUTPUT_CSV = PROJECT_ROOT / "resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv"
OUTPUT_FIGURE = PROJECT_ROOT / "results/figures/phase02_fig3_csfapi_optical_constants_digitized.png"
OUTPUT_OVERLAY_A = PROJECT_ROOT / "results/figures/phase02_fig3a_csfapi_optical_constants_overlay.png"
OUTPUT_OVERLAY_B = PROJECT_ROOT / "results/figures/phase02_fig3b_csfapi_optical_constants_overlay.png"
OUTPUT_LOG = PROJECT_ROOT / "results/logs/phase02_fig3_csfapi_digitization_notes.md"


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
    keep_components_red: int
    component_min_area_red: int
    keep_components_blue: int
    component_min_area_blue: int
    erase_regions: tuple[tuple[int, int, int, int], ...] = ()


PANELS = (
    PanelConfig(
        panel="a",
        quantity="n",
        x0=54,
        y0=12,
        x1=314,
        y1=222,
        x_min=450.0,
        x_max=1000.0,
        y_min=1.5,
        y_max=3.0,
        keep_components_red=2,
        component_min_area_red=100,
        keep_components_blue=1,
        component_min_area_blue=100,
        erase_regions=((170, 170, 230, 210),),
    ),
    PanelConfig(
        panel="b",
        quantity="kappa",
        x0=50,
        y0=15,
        x1=309,
        y1=223,
        x_min=450.0,
        x_max=1000.0,
        y_min=0.0,
        y_max=1.2,
        keep_components_red=1,
        component_min_area_red=100,
        keep_components_blue=1,
        component_min_area_blue=100,
        erase_regions=((155, 0, 225, 50),),
    ),
)


SERIES_CONFIG = {
    "Glass/CsFAPI": {
        "mask_fn": lambda hsv: cv2.inRange(hsv, (0, 70, 80), (10, 255, 255))
        | cv2.inRange(hsv, (170, 70, 80), (180, 255, 255)),
        "plot_color": "#d62728",
    },
    "ITO/CsFAPI": {
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


def build_overlay(
    panel: PanelConfig,
    base_bgr: np.ndarray,
    extracted: dict[str, tuple[np.ndarray, np.ndarray]],
) -> np.ndarray:
    overlay = base_bgr.copy()
    for series_name, config in SERIES_CONFIG.items():
        x_values, y_values = extracted[series_name]
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
        "# Phase 02 Fig. 3 CsFAPI 光学常数图数字化说明",
        "",
        "- 来源文献：`[LIT-0001] Khan et al. (2024)`",
        f"- 源图路径 (a)：`{SOURCE_IMAGES['a'].relative_to(PROJECT_ROOT)}`",
        f"- 源图路径 (b)：`{SOURCE_IMAGES['b'].relative_to(PROJECT_ROOT)}`",
        "- 提取对象：Fig. 3 中 (a) 折射率 `n` 与 (b) 消光系数 `κ` 两个子图",
        "- 提取方法：基于论文原始 MinerU 导出的图像做颜色分割与像素坐标标定，不使用截图二次压缩图。",
        "- 样品命名按论文原图保留为 `Glass/CsFAPI` 与 `ITO/CsFAPI`。",
        "- 精度边界：该 CSV 是“图像数字化数据”，不是论文作者公开的原始数值表；其准确度受原始图像分辨率和线宽限制。",
        "",
        "## 轴标定",
        "",
        "- Panel (a): `x = 450-1000 nm`, `y = 1.5-3.0`",
        "- Panel (b): `x = 450-1000 nm`, `y = 0.0-1.2`",
        "- 标定依据：Panel (a) 结合图框边界、刻度排布和正文给出的 `530 nm -> n≈2.81`、`800 nm -> n≈2.59` 做反校；Panel (b) 与 Fig. 2(b) 刻度体系一致。",
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
    ensure_parent(OUTPUT_OVERLAY_A)
    ensure_parent(OUTPUT_OVERLAY_B)
    ensure_parent(OUTPUT_LOG)

    rows: list[dict[str, object]] = []
    overlays: dict[str, np.ndarray] = {}

    for panel in PANELS:
        source_bgr = cv2.imread(str(SOURCE_IMAGES[panel.panel]))
        if source_bgr is None:
            raise FileNotFoundError(f"Failed to read source image for panel {panel.panel}: {SOURCE_IMAGES[panel.panel]}")
        source_hsv = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2HSV)
        panel_hsv = source_hsv[panel.y0 : panel.y1 + 1, panel.x0 : panel.x1 + 1]

        extracted_pixels: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for series_name, config in SERIES_CONFIG.items():
            raw_mask = config["mask_fn"](panel_hsv)
            raw_mask = erase_regions(raw_mask, panel.erase_regions)
            if series_name == "Glass/CsFAPI":
                filtered_mask = select_components(raw_mask, panel.keep_components_red, panel.component_min_area_red)
            else:
                filtered_mask = select_components(raw_mask, panel.keep_components_blue, panel.component_min_area_blue)
            x_pixels, y_pixels = extract_centerline(filtered_mask)
            wavelength_nm, values = pixel_to_data(panel, x_pixels, y_pixels)
            extracted_pixels[series_name] = (x_pixels, y_pixels)

            for wavelength_nm_i, value_i in zip(wavelength_nm, values, strict=True):
                rows.append(
                    {
                        "lit_id": "LIT-0001",
                        "figure": "Fig. 3",
                        "panel": panel.panel,
                        "quantity": panel.quantity,
                        "series": series_name,
                        "wavelength_nm": round(float(wavelength_nm_i), 6),
                        "value": round(float(value_i), 6),
                        "source_image": str(SOURCE_IMAGES[panel.panel].relative_to(PROJECT_ROOT)),
                        "digitization_basis": "paper_raster_curve",
                    }
                )

        overlays[panel.panel] = build_overlay(panel, source_bgr, extracted_pixels)

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
        ax.set_title(f"Fig. 3({panel.panel}) digitized {panel.quantity}")
        ax.grid(alpha=0.25, linewidth=0.5)
        ax.legend(frameon=False)
    figure.savefig(OUTPUT_FIGURE, dpi=220)
    plt.close(figure)

    cv2.imwrite(str(OUTPUT_OVERLAY_A), overlays["a"])
    cv2.imwrite(str(OUTPUT_OVERLAY_B), overlays["b"])
    write_log(OUTPUT_LOG, dataframe)

    print(f"Saved CSV: {OUTPUT_CSV}")
    print(f"Saved figure: {OUTPUT_FIGURE}")
    print(f"Saved overlay A: {OUTPUT_OVERLAY_A}")
    print(f"Saved overlay B: {OUTPUT_OVERLAY_B}")
    print(f"Saved log: {OUTPUT_LOG}")


if __name__ == "__main__":
    main()
