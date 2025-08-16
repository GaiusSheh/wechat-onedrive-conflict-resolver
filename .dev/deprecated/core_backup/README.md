# 已废弃的核心模块

此目录包含已废弃或不再使用的核心模块文件。

## 📁 文件说明

| 文件 | 废弃时间 | 废弃原因 |
|------|----------|----------|
| `wechat_controller_phase1_optimized.py` | 2025-08-09 | 第一阶段优化版本，已被新版本替代 |
| `performance_debug.py` | 2025-08-09 | 性能调试模块，功能已集成到新的性能监控系统 |
| `convert_prints_to_logger.py` | 2025-08-09 | print语句转换脚本，已完成转换任务 |

## ⚠️ 注意事项

- 这些文件仅作为历史记录保存
- 不建议在生产环境中使用这些废弃的文件
- 如需参考历史实现，请确保理解其局限性

## 🔄 替代方案

- `wechat_controller_phase1_optimized.py` → 使用 `core/wechat_controller.py`
- `performance_debug.py` → 使用 `core/performance_monitor.py`
- `convert_prints_to_logger.py` → 任务已完成，无需替代