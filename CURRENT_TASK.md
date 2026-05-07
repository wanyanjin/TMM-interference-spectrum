# CURRENT_TASK.md

## 当前任务

`Phase 08：参比几何验证与治理规范收敛`

目标：在现有 `pvk_x01` 审计结果基础上升级 HTML slide deck 与 technical report 的前端质量，引入本地 `reveal.js + KaTeX + Playwright QA` 工具链，用于解释反射率校准、TMM 计算链和当前实验-理论偏差；并为下一步 `nk_audit` / `nk_envelope` 做准备。

## 本轮范围

- 生成基于本地 `reveal.js` 的 Phase 08 HTML slide deck
- 生成同主题的 `technical_report.html`
- 新增本地视觉 QA 脚本与逐页截图输出
- 只读取现有 `pvk_x01` 结果集和 `600 nm` trace，不改主结果

不在本轮范围：

- 不修改 TMM / HDR / Phase 07 业务代码
- 不重算 Phase 08 主结果 CSV/JSON/MD
- 不导出 PDF / PPTX
- 不改 `src/core/reference_comparison.py` 主计算逻辑

## TODO

1. 重建 `step08_build_audit_slide_deck.py`，输出 reveal.js deck
2. 生成 `phase08_reference_audit_deck.html` 与 `technical_report.html`
3. 新增 `tools/phase08_slides_qa.mjs` 与 QA 截图
4. 为下一步 `nk_audit` 与 `nk_envelope` 保留可讲解的审计材料

## 阻塞与注意事项

- 工作区存在无关未提交改动（`docs/PROJECT_STATE.md`、`src/scripts/stepD2b_explain_feature_pipeline.py`、`results/report/...`），本轮不得纳入提交。
- `test_data/0429` 无 `.spe`，曝光时间仅来自文件名推断，必须在 trace 报告中保留该约束。
- HTML 中不得出现外部 CDN。
- deck 只讲 `pvk_x01` audited 结果集，不引入新的重算分支。
- browser-use 当前无可用 IAB backend，本轮浏览器验收改由 Playwright 截图完成。

## 立即下一步

- 运行本地 deck build 与 Playwright QA
- 核对关键页截图和 overflow 报告
- 下一步准备 `nk_audit` 与 `nk_envelope`，验证 PVK / Ag `n,k` 数据的适用性

## 最新同步

- 现阶段 Phase 08 已把 `step08_build_audit_slide_deck.py` 的图面布局改为更宽的画布与防溢出标注，避免右侧标签被裁切。
- `results/slides/phase08_reference_audit/assets/deck.js` 已加入无 `Reveal` / 无 `KaTeX` 的降级渲染路径，便于本地 QA 与离线阅读。
- `results/slides/phase08_reference_audit/assets/theme.css` 已补充 `deck-enhanced` / `deck-fallback` 样式分支，以及公式 fallback 样式。
- 当前仍保留下一步 `nk_audit` / `nk_envelope` 计划，不改变 Phase 08 的主线方向。
