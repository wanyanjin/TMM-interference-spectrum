# AGENTS.md

本文件是 `TMM-interference-spectrum` 项目的稳定工程宪法。所有 AI Agent 在执行任务前必须先阅读本文件。

若本文件与临时聊天指令冲突，以本文件为准；若确需偏离，必须先说明偏离原因、影响范围与替代方案。

---

## 1. 项目定位与最高原则

本项目是科研型光谱建模与反演系统，不是通用 CRUD 工程。核心目标是：

- 光学模型物理一致性
- 数值优化稳定性
- 数据链路可追溯
- 结果可复现、可比较、可回滚

发生冲突时遵循：

1. 物理正确性优先于“先跑通”
2. 长期可维护优先于局部方便
3. 可验证证据优先于经验猜测

---

## 2. 四层记忆系统（强制）

### 2.1 `AGENTS.md`

- 职责：稳定规则、红线、执行纪律
- 不承载长历史、详细 SOP、结果清单

### 2.2 `CURRENT_TASK.md`

- 职责：当前活动记忆
- 仅记录当前目标、TODO、阻塞、下一步
- 不承载完整历史

### 2.3 `CHANGELOG_DIGEST.md`

- 职责：追加式压缩历史
- 只记录可证实的关键决策、能力变化、流程变化、重要问题

### 2.4 `docs/PROJECT_STATE.md`

- 职责：当前真实仓库状态快照与 SOP 入口
- 必须反映真实目录、真实脚本数据流与当前验证边界

---

## 3. Phase 与提交纪律

### 3.1 Phase 强制归属

每次任务必须归属到明确 Phase。若用户未指定，Agent 需根据上下文给出合理归属并保持一致命名。

### 3.2 提交信息格式

commit message 必须使用中文并以 `[Phase XX]` 开头，例如：

- `[Phase 08] 完善项目治理规范并准备参比比较流程`

### 3.3 多机协作提交要求（Windows/macOS）

每次任务完成并验证后，原则上必须执行：

1. `git commit`
2. `git push`

目的：保证另一台电脑可同步接续工作。若因网络/权限无法 push，必须在回报中说明原因与当前状态。

### 3.4 提交范围纪律

- 仅提交与当前任务直接相关文件
- 禁止把无关脚本、临时结果、`.DS_Store`、`__pycache__` 混入提交
- 禁止未验证即提交

---

## 4. 目录与数据红线

### 4.1 根目录红线

项目根目录禁止散落：

- 临时脚本
- CSV/图表/中间数组
- 调试日志
- 临时草稿

### 4.2 数据分层

- `data/raw/`：原始数据，只读
- `data/processed/`：标准中间数据，脚本间共享入口
- `results/figures/`：图表
- `results/logs/`：运行日志与摘要
- `results/report/`：汇报友好精选资产（当前仓库使用此目录名）

### 4.3 原始数据不可覆盖

未经用户明确授权，不得覆盖、重命名或就地清洗 raw 数据。

### 4.4 流程解耦

脚本之间必须通过落盘文件交互，不允许依赖聊天上下文或内存状态作为事实来源。

### 4.5 生成物路径治理与根目录零污染规则

项目根目录只允许放置稳定入口文件和项目级配置文件，例如 `AGENTS.md`、`README.md`、`CURRENT_TASK.md`、`CHANGELOG_DIGEST.md`、`pyproject.toml`、`uv.lock`、`.gitignore`、`src/`、`tests/`、`docs/`、`data/`、`results/`、`resources/`、`configs/`、`scripts/`、`test_data/`、`tools/`。

除上述稳定入口和配置外，任何由测试、脚本、CLI、GUI、workflow、agent、notebook 或临时调试产生的文件，都禁止直接写入项目根目录。禁止项包括但不限于：pytest 缓存、测试临时目录、运行缓存、临时 CSV/TXT/JSON/YAML、临时 PNG/SVG/PDF/HTML、调试日志、scratch 脚本、中间数组、实验运行结果、GUI 导出结果、CLI 运行结果、benchmark 输出、profiling 输出、coverage 输出、自动生成报告、模型拟合结果、临时 manifest/summary。

若新增功能会生成仓库尚未定义存放位置的新文件类型，禁止先写到根目录。必须按以下顺序处理：

1. 判断产物性质：raw data / processed data / figure / report / log / run artifact / cache / temp / fixture / calibration / export。
2. 选择已有受控目录。
3. 如果没有合适目录，创建清晰命名的新目录。
4. 在相关文档中登记该目录用途。
5. 在 `.gitignore` 中明确哪些文件应忽略、哪些索引文件或 `.gitkeep` 应保留。
6. 在回报中说明新目录和数据流。

推荐分流规则如下：

- 原始实验数据 -> `data/raw/`
- 标准中间数据 -> `data/processed/`
- 校准文件 -> `data/calibrations/` 或 `resources/calibrations/`
- 正式图表 -> `results/figures/`
- 正式日志 -> `results/logs/`
- 正式报告 -> `results/report/`
- 实验运行记录 -> `runs/<workflow_name>/<run_id>/`
- GUI 导出结果 -> `results/gui_exports/` 或 `runs/gui/<run_id>/`
- CLI 输出 -> `results/<tool_name>/` 或 `runs/<tool_name>/<run_id>/`
- 测试临时文件 -> `tmp/pytest/`
- 测试 fixture -> `tests/fixtures/`
- 测试生成但需保留的样例 -> `tests/fixtures/generated/` 并配 README
- scratch 脚本 -> `tmp/scratch/`，任务结束后清理
- benchmark / profiling -> `results/benchmarks/` 或 `tmp/benchmarks/`
- coverage / htmlcov -> `tmp/coverage/` 或 `htmlcov/`，并被 `.gitignore` 忽略
- 缓存 -> `tmp/cache/` 或工具默认 cache 目录，并被 `.gitignore` 忽略

正式产物与临时产物必须严格区分。正式产物包括可复现实验结果、正式报告、正式图表、标准中间数据、以及后续流程需要读取的 manifest / summary / calibration；这些应进入受控目录，并按需要纳入版本管理或通过 README 说明不纳入 Git 的原因。临时产物包括 debug 输出、临时图、一次性 CSV、pytest cache、scratch 文件、中间排错文件；这些必须进入 `tmp/` 或对应临时目录，并默认不进入 Git。

所有新增 CLI、GUI、workflow、脚本必须满足：不得默认 `output_dir =` 项目根目录，不得默认向 `Path.cwd()` 直接写结果，不得把当前工作目录当作结果目录，必须显式传入 `output_dir` 或默认进入受控目录，输出前必须确保 `output_dir` 存在，输出完成后必须生成 manifest 或 summary，说明文件位置。

测试代码必须使用 `pytest tmp_path / tmp_path_factory`，禁止测试向 repository root 写文件，禁止测试把缓存、图片、CSV、JSON、log 写到根目录。如果测试需要生成持久 fixture，必须放到 `tests/fixtures/generated/` 并配说明。

每次任务完成前必须执行 `git status --short`，并检查项目根目录是否新增了未授权文件或目录。若发现根目录污染，必须先判断是否临时产物，再删除或移动到合适目录，随后更新 `.gitignore` 或文档，并再次检查 `git status`；回报中必须说明处理结果。禁止把根目录污染留给用户手动清理。

---

## 5. 架构边界（含未来 GUI/CLI）

### 5.1 核心逻辑归位

- `src/core/`：TMM/Fresnel/EMA、残差、优化、材料插值、HDR 核心逻辑
- `src/scripts/`：可执行入口和流程编排，保持“薄脚本”

未来扩展建议：

- `src/analysis/`：诊断与特征分析
- `src/workflows/`：复用型流水线
- `src/storage/`：I/O 与 manifest 适配
- `src/cli/`、`src/gui/`：调用 workflow，不承载核心公式

### 5.2 GUI 红线

GUI 只能做输入、展示、状态查看、动作请求，不得直接实现：

- TMM 公式
- 拟合目标函数
- 数据清洗主逻辑
- 材料库解析
- 文件存储细节

---

## 6. 高频功能 CLI 化与 CLI 文档规范

### 6.1 CLI 化触发条件

凡是满足以下任一条件的功能，应标准化为 CLI：

- 会被重复使用
- 需要跨样品运行
- 未来可能被 GUI 调用
- 将进入正式实验或分析流程

### 6.2 CLI 的角色边界

- CLI 是稳定入口，不是临时脚本别名。
- CLI 负责参数解析、输入验证、调用 `core/workflow/storage`、输出 manifest/summary。
- CLI 不得复制核心物理公式、拟合残差主逻辑或材料模型主逻辑。

### 6.3 GUI 与 CLI 一致性要求

- GUI 后续必须复用同一套 `core/workflow/CLI` 参数模型。
- 禁止在 GUI 侧另写一套业务逻辑或参数语义。

### 6.4 CLI 文档交付红线

- 每个正式 CLI 必须有详细文档。
- CLI 文档未更新时，功能不能视为正式交付。
- CLI 变更时，必须同步更新：
  - `docs/CLI_INDEX.md`
  - `docs/cli/*.md` 对应详细文档

### 6.5 CLI 文档最低字段

CLI 详细文档必须至少包含：

- 功能定位
- 适用场景
- 命令示例
- 参数表
- 输入输出
- 执行原理
- 调用接口
- 数据流
- 错误行为
- GUI 调用建议
- 维护记录

---

## 7. 结构化输入验证墙

所有结构化输入在进入核心计算前必须校验。高风险输入包括：

- 波长范围与单位
- 厚度单位与范围
- 层顺序
- 材料 `n/k` 列完整性与单位
- 参比类型（`glass/Ag`、`Ag mirror` 等）
- 曝光时间
- 反射率单位（百分比或 0-1）
- 拟合参数边界
- 是否允许外推
- 入射角/NA
- HDR/平滑开关
- 参数固定/释放配置

短期可使用显式校验与 dataclass；长期建议引入统一 schema（如 Pydantic）。

禁止静默纠错改变物理含义。

---

## 8. 物理建模与数值红线

### 7.1 可追溯性

涉及以下内容必须有公式依据或文档说明：

- TMM/Fresnel/EMA
- 粗糙层
- 非相干玻璃级联
- 偏振/角度/厚度平均
- HDR 标定
- 参比换算
- 残差定义

### 7.2 单位显式

禁止隐式混用：

- `nm` 与 `um`
- `degree` 与 `radian`
- 百分比反射率与 `0-1` 反射率

### 7.3 禁止行为

- 为了“拟合好看”随意加自由参数
- 静默改变层顺序
- 无说明外推 `n/k`
- 将不同参比模型当作同一类型
- 将数值收敛等同于物理可信
- 用 `try/except` 吞错、无依据压 `NaN/Inf`

### 7.4 拟合输出最低披露

拟合结果必须说明：

- 使用波段
- 固定/释放参数
- 参数是否贴边
- 残差结构
- 材料来源

---

## 9. 文献优先（Literature-First）

### 9.1 执行顺序

1. 先查 `docs/LITERATURE_MAP.md`
2. 再回源文献原文（当前仓库主要在 `reference/`，目标迁移到 `resources/references/`）
3. 再实现代码

### 9.2 引用标注

复杂物理实现必须在注释或 docstring 标注文献 ID，例如 `[LIT-0001]`。

### 9.3 缺失处理

若依据缺失或冲突，必须先记录并补索引，不得凭空编造公式、参数或结论。

### 9.4 材料复折射率来源优先级

当任务目标是“获取材料复折射率 `n/k` 数据”而不是实现复杂物理模型时，优先级规则如下：

1. 先查 `refractiveindex.info`
2. 若该站无目标材料、波长覆盖不足、或材料口径与任务明显不匹配，再转向其他来源
3. 使用 `refractiveindex.info` 时，必须记录：
   - 具体页面 URL
   - 页面标签/文献标签
   - 本地 raw 文件路径
   - 标准化 CSV 或后续派生文件路径

此规则仅适用于“材料 `n/k` 查询工作流”，不替代本节上方的文献优先要求；凡涉及复杂物理实现、模型公式、拟合策略或参数选型，仍必须先回到 `docs/LITERATURE_MAP.md` 与原始文献。

---

## 10. 跨平台开发要求（Windows/macOS）

### 9.1 路径与 I/O

- 优先使用 `pathlib` 与相对项目根路径
- 避免硬编码 macOS/Windows 私有绝对路径
- 明确处理中文路径、OneDrive/百度网盘同步路径差异

### 9.2 文本与编码

- 统一 UTF-8 编码
- 注意换行差异（LF/CRLF）
- 注意文件系统大小写敏感差异

### 9.3 可复现运行

- 新脚本必须写清输入、输出、依赖
- 新机器应可按文档恢复运行

---

## 11. 测试与验证底线

至少建立并维护以下验证墙：

- 关键公式单元测试
- 数据 I/O 与列名识别测试
- HDR 标定最小合成测试
- TMM forward 基准回归测试
- 拟合流程 smoke test
- 重大 bug 修复后的 regression test

仅靠 GUI 点击或肉眼看图不构成充分验证。

---

## 12. 文档维护触发条件

出现以下任一情况必须同步文档：

- 新 Phase 启动或完成
- 核心目录变化
- 数据流变化
- 参数定义/单位约定变化
- 新资源依赖引入
- 主流程重大 bug 修复

最少应更新对应文档：

- 规则变动：`AGENTS.md`
- 当前任务：`CURRENT_TASK.md`
- 历史摘要：`CHANGELOG_DIGEST.md`
- 现状与 SOP：`docs/PROJECT_STATE.md`
- 数据链路：`docs/DATA_FLOW.md`
- 风险与债务：`docs/KNOWN_ISSUES.md`
- CLI 索引：`docs/CLI_INDEX.md`
- CLI 详细文档：`docs/cli/*.md`

---

## 13. 异常处理与审计要求

异常发生后必须先完整阅读 Traceback，并判断属于：

- 物理/数值问题
- 代码逻辑问题

修复记录需包含：

- 触发条件
- 影响范围
- 根因判断
- 修复策略
- 验证结果

禁止通过“掩盖报错”制造表面成功。

---

## 14. 报告与可视化交付规范

- 所有正式 Markdown 报告中的数学公式必须使用 LaTeX，不得用普通 text code block 代替公式表达。
- 所有正式图表必须遵守 `docs/REPORTING_AND_FIGURE_STYLE.md`。
- 面向组会、论文或对外展示的图默认使用 `3:2` 比例；同一类图必须固定坐标轴范围和视觉语义。
- CLI 或脚本生成正式结果时，必须同步输出可追溯的 Markdown 报告、机器可读 JSON/CSV，以及符合项目风格的图片资产。
- 若某类图或报告因特殊用途需要偏离规范，必须在脚本或报告中明确说明原因与影响。

---

## 15. 正式工具单元开发规范

### 15.1 正式工具分层

- 新正式工具优先使用 `domain -> core -> storage -> workflows -> cli/gui -> results` 的标准结构。
- 建议正式工具把统一数据模型放到 `src/domain/`，通用基础设施放到 `src/common/`，可复用绘图放到 `src/visualization/`。
- `src/scripts/` 可以保留历史脚本、实验脚本和薄入口脚本，但新正式工具不得直接堆到 `src/scripts/`。
- 高频、可复用、未来可能 GUI 化的能力必须走正式工具结构。
- 旧脚本不在每轮任务中默认迁移，除非用户明确要求。

### 15.2 工具交付要求

- 每个正式工具必须登记到 `docs/tools/TOOL_REGISTRY.md`。
- 每个正式工具必须具备对应文档，至少覆盖工具定位、输入输出、接口与限制。
- 每个正式工具必须输出 `manifest.json` 或 `summary.json`，保证可追溯性。
- `experimental -> active` 的升级条件至少包括：测试、文档、CLI、可追溯输出齐全。

---

## 16. Core 沙箱与输入适配器规则

### 16.1 Core 沙箱

- `src/core/` 新代码不得依赖 `pandas`、`h5py`、`zarr`、`PySide6`、`pyqtgraph`、`matplotlib`、`argparse`、`json`、`yaml`。
- `core` 不得读取文件、写文件、画图、弹窗、解析命令行、判断文件格式。
- `core` 不得根据 `.csv`、`.h5`、`.txt` 等文件后缀分支。
- `core` 只接收 domain model 或 `ndarray`。
- `core` 只返回 domain result 或 `ndarray`。
- 若已有历史 `src/core/*.py` 暂未完全满足此规则，不在本轮强制重构；新代码必须遵守，旧代码逐步迁移。

### 16.2 输入适配器

- 新文件格式只能通过 `src/storage/readers/` adapter 接入。
- `workflow` 不得散落基于文件后缀的 `if/else`。
- 文件格式识别、列名归一、元数据提取与外部文件到 domain model 的转换，都应放在 `storage/readers`。
- `core` 必须完全不知道数据来自 CSV、TXT、H5、Zarr、SPE、LightField 还是 GUI。

---

## 17. GUI 技术栈规则

### 17.1 默认技术路线

- 新 GUI 默认技术路线为 `PySide6 + pyqtgraph`。
- `PySide6` 负责窗口、控件、布局、菜单、文件选择和状态栏。
- `pyqtgraph` 负责光谱曲线、多曲线叠加、缩放、拖拽和快速刷新。

### 17.2 GUI 边界

- GUI 只负责输入、展示、状态查看和动作触发。
- GUI 不得实现核心计算、TMM/Fresnel/EMA、拟合目标函数、复杂导出。
- GUI 必须调用 `workflow`，不得直接复制核心业务逻辑。
- GUI view model 只负责把 domain result 转成界面状态。

### 17.3 依赖边界

- `PySide6` 与 `pyqtgraph` 只允许出现在 `src/gui/` 或 GUI 专用 adapter 中。
- 不得把 `PySide6`、`pyqtgraph` 引入 `src/core/`、`src/domain/` 或 `src/workflows/`。
