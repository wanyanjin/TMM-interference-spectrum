# LITERATURE_MAP.md

本文件是 `TMM-interference-spectrum` 项目的文献索引地图与长期知识库入口，用于在实现任何物理模型、数学公式、数值方法和核心参数选型之前，先定位证据来源，再回源读取原文。

## Usage Rule

1. 在实现任何涉及物理模型、数学推导、色散参数、带隙、厚度先验、边界条件、拟合窗口的代码前，先阅读本文件。
2. 先看 `Index`，定位最相关的文献条目 ID，再跳转到对应 `Entries` 详细卡片。
3. 进入具体条目后，必须回源打开该条目列出的 `Source Dir` 下原始 `full.md` 或 PDF，确认公式、常数、单位和适用条件。
4. 在代码、注释或 docstring 中引用文献时，必须标注条目 ID，例如 `[LIT-0001]`。
5. 如果需要的文献不在本文件中，或者 `reference/` / `resources/references/` 下新增了文献，必须调用 `$literature-map` 技能更新本文件后再继续开发。

## Index

| ID | Title | Tags | Key Models / Parameters | Source Coverage | Status |
| --- | --- | --- | --- | --- | --- |
| `LIT-0001` | Khan et al. (2024) Optical constants manipulation of formamidinium lead iodide perovskites | `perovskite`, `Tauc-Lorentz`, `FAPI`, `CsFAPI`, `n-k`, `ellipsometry` | 三振子 Tauc-Lorentz；FAPI/CsFAPI 的 `Eg`、`eps_inf`、`A_i/E_i/C_i`；`eps_r=n^2-k^2`；`eps_i=2nk` | 2 个重复 MinerU 目录已合并 | indexed |

## Entries

### [LIT-0001] Khan et al. (2024) Optical constants manipulation of formamidinium lead iodide perovskites: ellipsometric and spectroscopic twigging

- Status: `indexed`
- DOI: `10.1039/d4ya00339j`
- Tags: `perovskite`, `FAPI`, `CsFAPI`, `spectroscopic-ellipsometry`, `three-oscillator-Tauc-Lorentz`, `dielectric-function`, `n-k`
- Source Dir: `reference/Khan 等 - 2024 - Optical constants manipulation of formamidinium lead iodide perovskites ellipsometric and spectrosc.pdf-64661b05-c239-4731-a3f7-2c0456a4df66`
- Source Dir: `reference/Khan 等 - 2024 - Optical constants manipulation of formamidinium lead iodide perovskites ellipsometric and spectrosc.pdf-d567370f-bbbb-4604-91f2-876d6e53d1e0`
- Source Note: 同一篇论文的 2 个 MinerU 解析目录，内容高度重复；当前统一映射为一个文献条目。

#### Applicability

- 适用于 FAPI 与 CsFAPI 薄膜的光学常数建模、三振子 Tauc-Lorentz 参数选型和带隙引用。
- 对本项目最直接的价值是为 PVK 层提供文献来源明确的 `eps_inf`、`Eg` 和振子参数。
- 论文的椭偏测试波段是 `450-1000 nm`。若将该参数组外推到 `1000 nm` 以上，必须在代码或文档中明确标记“超出原测量窗口外推”。

#### Key Extraction

- Optical model:
  - 采用 spectroscopic ellipsometry 测量，并使用 three-oscillator Tauc-Lorentz (T-L) 模型拟合 perovskite 层光学常数。
- Measurement window:
  - 论文原始光学常数提取基于 `450-1000 nm` 波段。
- Core dielectric relations:
  - `eps_r = n^2 - k^2`
  - `eps_i = 2 n k`
- Tauc-Lorentz rule used by the paper:
  - 当 `E <= Eg` 时，`eps_i = 0`
  - 当 `E > Eg` 时，`eps_i(E)` 由 `A, E0, C, Eg` 决定，为标准 Tauc-Lorentz 虚部表达式
  - `eps_r(E)` 由 `eps_inf` 加上解析闭式项组成，属于 Jellison-Modine 风格的 T-L 实部表达式

#### Parameter Tables

##### Table A. Bandgap `Eg`

| Sample | `Eg (eV)` |
| --- | --- |
| Glass/FAPI | `1.49` |
| Glass/ITO/FAPI | `1.50` |
| Glass/CsFAPI | `1.59` |
| Glass/ITO/CsFAPI | `1.58` |

##### Table B. Three-oscillator Tauc-Lorentz parameters

| Sample | `eps_inf` | `A1` | `E1` | `C1` | `A2` | `E2` | `C2` | `A3` | `E3` | `C3` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Glass/FAPI | `1.25` | `3.43` | `1.55` | `0.19` | `44.45` | `2.18` | `4.35` | `0.83` | `2.70` | `0.41` |
| ITO/FAPI | `1.24` | `30.55` | `1.45` | `0.44` | `52.101` | `2.18` | `3.70` | `1.00` | `2.45` | `0.49` |
| Glass/CsFAPI | `1.10` | `24.53` | `1.57` | `0.13` | `7.60` | `2.46` | `0.49` | `6.50` | `3.31` | `3.89` |
| ITO/CsFAPI | `1.01` | `6.16` | `1.58` | `0.13` | `6.52` | `2.45` | `0.54` | `8.26` | `3.18` | `0.61` |

#### Formula Notes

- 论文给出了 Tauc-Lorentz 虚部 `eps_i(E)` 的分段公式：
  - `E > Eg` 时使用标准有理式
  - `E <= Eg` 时强制为 `0`
- 论文也给出了实部 `eps_r(E)` 的解析闭式表达式，其中包含：
  - `eps_inf`
  - 对数项
  - 反正切项
  - 与 `A, E0, C, Eg` 相关的辅助量
- MinerU 解析对公式排版存在噪声；如果要重新实现闭式 `eps_r`，应以 PDF 再核对一次符号细节和辅助变量定义。

#### Implementation Notes

- 当前项目的 `src/scripts/step02_tmm_inversion.py` 已使用如下参数：
  - `PVK_EPS_INF = 1.10`
  - `PVK_OSCILLATORS = [(24.53, 1.57, 0.13), (7.60, 2.46, 0.49), (6.50, 3.31, 3.89)]`
- 这组参数与本条目的 `Glass/CsFAPI` 三振子参数一一对应，可视为当前代码的直接文献来源，应在后续代码中标注为 `[LIT-0001]`。
- 当前项目代码中 `PVK_EG_EV = 1.556`，与本论文表格中的 `Glass/CsFAPI = 1.59 eV` 和 `Glass/ITO/CsFAPI = 1.58 eV` 不完全一致。
- 因此，后续若继续沿用 `PVK_EG_EV = 1.556`，必须在代码或文档中说明：
  - 该值不是本条目表格的直接照抄
  - 它来自其他资源、二次校正或拟合策略，而不是来自 Khan 2024 的 Table S2

#### Coding Guidance

- 若建模对象更接近“玻璃上制备的 CsFAPI 薄膜”，优先从 `Glass/CsFAPI` 参数组起步。
- 若建模对象更接近“ITO 基底上的 CsFAPI 薄膜”，应认真比较是否改用 `ITO/CsFAPI` 参数组更合理，而不是默认沿用玻璃基底参数。
- 当代码需要显式实现 `eps_i(E)` 时，可以依据本条目直接采用：
  - `E <= Eg -> eps_i = 0`
  - `E > Eg -> standard Tauc-Lorentz numerator / denominator form`
- 当代码需要从介电函数恢复 `n, k` 时，可以依据本条目中的：
  - `eps_r = n^2 - k^2`
  - `eps_i = 2nk`

#### Risks / Open Questions

- 本论文的参数提取波段是 `450-1000 nm`，而当前项目反演窗口是 `850-1100 nm`，其中 `1000-1100 nm` 属于外推区。
- 当前仓库中的 MinerU 目录是重复的；后续若迁移到 `resources/references/`，应保留一个规范化主目录，并同步更新本地图。
- 若后续要把 `eps_r(E)` 闭式作为高精度基线实现，建议优先回看原始 PDF，而不是完全依赖 Markdown 公式排版。

#### Code Links

- `src/scripts/step02_tmm_inversion.py`
