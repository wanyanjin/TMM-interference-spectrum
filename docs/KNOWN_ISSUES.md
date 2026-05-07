# KNOWN_ISSUES.md

1. `reflectance_qc` GUI 目前为实验态，不是完整 TMM 拟合系统。
2. 目前输入 adapter 仅覆盖 CSV/TXT，尚未实现 H5/Zarr。
3. 本机环境缺少完整科学计算依赖时，CLI/workflow 无法运行（如 `numpy` 缺失）。
4. 当前 Windows 环境存在系统临时目录 ACL 问题，`pytest tmp_path` 可能触发 `PermissionError`。
5. GUI 自动化测试依赖 `PySide6`；缺失时测试将被 `pytest.importorskip` 跳过。
