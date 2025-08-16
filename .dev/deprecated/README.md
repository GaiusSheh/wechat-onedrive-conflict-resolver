# 废弃文件存档

本目录包含项目开发过程中废弃的文件和组件，按类型分类存储。

## 📁 目录结构

```
deprecated/
├── README.md                    # 本文档
├── core_backup/                 # 废弃的核心模块备份
│   ├── performance_debug.py     # 旧版性能调试模块
│   ├── cleanup_print_statements.py
│   └── ...
├── gui_backup/                  # 废弃的GUI组件备份  
│   ├── main_window_backup.py    # 各版本主窗口备份
│   ├── icon_manager_old.py      # 旧版图标管理器
│   └── ...
├── docs_backup/                 # 废弃的文档备份
│   ├── performance_analysis_report.md
│   └── ...
├── tests_backup/                # 废弃的测试文件
│   ├── simple_sync_test.py      # 简单同步测试
│   ├── test_onedrive_sync.py    # OneDrive同步测试
│   └── ...
└── scripts/                     # 废弃的工具脚本
    └── update_version.py        # 版本更新脚本
```

## 🗂️ 文件分类

### Core组件备份
- **performance_debug.py**: v3.0之前的性能调试实现
- **wechat_controller_phase1_optimized.py**: 微信控制器优化版本1

### GUI组件备份  
- **main_window_backup*.py**: 主窗口的各个开发版本
- **icon_manager_old.py**: 旧版图标管理实现

### 测试文件备份
- **test_onedrive_*.py**: OneDrive相关测试
- **simple_sync_test.py**: 简化的同步测试

### 文档备份
- **performance_*.md**: 性能分析报告
- **PROJECT_SUMMARY.md**: 项目总结文档

### 工具脚本备份
- **update_version.py**: 硬编码版本管理脚本（已被动态版本系统替代）

## 🗃️ 保留意义

- **技术参考**: 记录不同实现方案的技术细节
- **回滚需要**: 如果新实现出现问题，可参考历史版本
- **开发历程**: 展示项目从简单到复杂的完整发展过程
- **学习价值**: 为类似项目提供实现思路和经验教训

## ⚠️ 注意事项

1. **不建议使用**: 这些文件已被更新的实现替代
2. **仅供参考**: 保留用于参考历史实现和设计思路  
3. **不影响构建**: 这些文件不参与项目构建和打包
4. **定期清理**: 建议每个大版本发布后清理过旧的备份

## 📝 版本历史

- **v4.0.2**: 整理deprecated目录结构，合并gui_backup，创建tests_backup
- **v4.0.1**: 移动核心调试文件到debug_control目录
- **v3.0**: 创建deprecated目录，开始系统化存档

## 📝 文件生命周期

当代码或文档被新版本替代时，按以下流程处理：
1. **依赖检查** - 使用 grep 检查是否有其他文件引用
2. **评估价值** - 确定是否有保留价值
3. **分类存档** - 按类型放入对应子目录  
4. **添加说明** - 记录废弃原因和替代方案
5. **更新索引** - 在本README中记录新增内容
6. **功能验证** - 确认主程序仍能正常启动

## ⚠️ 使用注意

- 这里的文件可能包含过时的API调用或逻辑缺陷
- **移动文件前必须检查依赖关系**，避免破坏主程序功能
- 仅供参考，不建议直接在生产环境使用
- 如需复用某些实现，请先进行充分测试

## 🐛 历史Bug记录

### 2025-08-10: performance_debug.py 误移动事件
- **问题**: 将活跃使用的 `core/performance_debug.py` 误移到此目录
- **影响**: GUI无法启动，导入错误 `ModuleNotFoundError`  
- **修复**: 恢复文件到 `core/` 目录
- **教训**: 任何 core/ 目录文件移动前必须进行依赖分析

---

*最后更新: 2025-08-15 - v4.0.2*