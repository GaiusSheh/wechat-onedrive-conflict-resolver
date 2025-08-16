# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个微信Windows端自动化工具，用于解决OneDrive同步冲突问题。该工具通过自动化执行关闭微信、重启OneDrive同步的流程来解决文件锁定冲突。

**当前版本**: v3.0 - 日志系统统一版
**核心特性**: 现代化GUI界面、精简配置面板、完善关闭行为、系统托盘集成、统一日志系统

## 项目架构

### 核心模块 (`core/`)
- **`wechat_controller.py`** - 微信进程控制（启动/停止/状态检查）
- **`onedrive_controller.py`** - OneDrive进程和同步控制
- **`sync_workflow.py`** - 完整同步流程的主入口
- **`sync_monitor.py`** - 后台监控服务，支持定时和空闲触发
- **`idle_detector.py`** - Windows API系统空闲时间检测
- **`task_scheduler.py`** - 灵活的定时任务调度器
- **`config_manager.py`** - JSON配置文件管理和验证
- **`performance_monitor.py`** - 系统性能监控和资源使用统计
- **`logger_helper.py`** - 统一日志系统（文件+控制台，支持GUI回调）
- **`performance_debug.py`** - 性能调试日志控制（生产环境可禁用）

### GUI模块 (`gui/`)
- **`main_window.py`** - 现代化主窗口界面（ttkbootstrap样式）
- **`icon_manager.py`** - 图标资源管理和生成
- **`system_tray.py`** - 系统托盘功能
- **`close_dialog.py`** - 关闭行为选择对话框

### 配置系统
- **`configs/sync_config.json`** - 主配置文件，包含触发条件、同步设置、日志配置
- 支持两种触发模式：定时触发（固定时间）和空闲触发（系统静置后）
- **全局冷却机制**: 所有触发类型共享冷却时间，避免过频繁同步
- 可配置的重试机制和等待时间
- **日志管理**: 自动文件日志记录和轮转清理

## 常用开发命令

### 依赖管理
```bash
# 安装依赖
pip install -r requirements.txt

# 主要依赖：
# - psutil (进程管理)
# - schedule (任务调度) 
# - ttkbootstrap (现代化GUI主题)
# - pystray (系统托盘)
# - pillow (图像处理)
```

### 核心功能测试
```bash
# 手动执行完整同步流程
python core/sync_workflow.py run

# 检查当前状态
python core/sync_workflow.py status

# 单独控制微信
python core/wechat_controller.py start|stop|status

# 单独控制OneDrive
python core/onedrive_controller.py start|stop|pause|resume|status|wait-sync
```

### 配置管理
```bash
# 创建默认配置文件
python core/config_manager.py create

# 显示当前配置
python core/config_manager.py show

# 验证配置文件
python core/config_manager.py validate
```

### 自动化监控
```bash
# 启动监控服务（包含静置和定时触发）
python core/sync_monitor.py start

# 查看服务状态
python core/sync_monitor.py status

# 测试功能
python core/idle_detector.py test
python core/task_scheduler.py test
python core/sync_monitor.py test-sync
```

### GUI界面运行
```bash
# 启动现代化图形界面（推荐）
python gui_app.py

# 或使用批处理脚本
start_gui.bat

# GUI功能特点：
# - ttkbootstrap现代化主题
# - 实时状态监控和控制
# - 全局冷却时间显示和重置
# - 彩色日志显示和自动文件记录
# - 系统托盘支持
```

## 关键技术细节

### 进程管理
- 使用 `psutil` 库进行Windows进程检测和控制
- 微信进程名：`Weixin.exe`，OneDrive进程名：`OneDrive.exe`
- 支持多进程实例检测和批量操作

### 同步流程
1. 停止所有微信进程
2. 停止OneDrive进程（暂停同步）
3. 重启OneDrive（自动恢复同步）
4. 等待同步完成（可配置超时时间）
5. 重启微信

### 超时处理
- `sync_workflow.py` 中的 `run_command()` 函数支持可配置超时
- OneDrive同步等待默认超时400秒
- 使用 `sys.executable` 确保子进程使用正确的Python解释器（支持虚拟环境）

### 配置文件结构
- `idle_trigger`: 空闲触发设置（启用状态、空闲分钟数、全局冷却时间）
- `scheduled_trigger`: 定时触发设置（启用状态、执行时间、执行日期）
- `sync_settings`: 同步行为控制（等待时间、重试次数）
- `logging`: 日志配置（启用状态、级别、文件保留数）
- `gui`: GUI界面配置（关闭行为、记住选择）
- `startup`: 启动设置（自动启动、最小化到托盘）

## 开发注意事项

### Windows特定功能
- 需要管理员权限来终止某些进程
- 使用Windows Registry API查找OneDrive安装路径
- 集成Windows API进行系统空闲检测

### 错误处理
- 所有进程操作都有适当的异常处理
- 支持进程访问权限检查
- 配置文件格式验证和错误报告

### 虚拟环境支持
- 使用 `sys.executable` 而不是硬编码的 `python` 命令
- 确保子进程调用使用正确的Python解释器和依赖

### 日志和调试
- **多级别日志系统**: DEBUG、INFO、WARNING、ERROR四个级别
- **自动文件日志**: 每日独立日志文件，自动轮转清理
- **实时GUI日志**: 彩色标签显示，自动滚动
- **性能监控**: CPU和内存使用统计
- **详细状态报告**: 进程状态、同步进度、错误诊断
- **测试模式**: 支持各个组件的独立验证

### 全局冷却机制
- **统一冷却时间**: 手动、定时、空闲触发共享冷却期
- **冷却状态显示**: 实时倒计时和剩余时间
- **冷却重置功能**: 支持手动重置冷却时间
- **智能防护**: 避免过于频繁的同步操作

### GUI性能优化
- **批量更新机制**: 100ms延迟批处理GUI更新
- **智能状态缓存**: 只有真正变化时才更新界面
- **线程管理优化**: 合理的更新频率和资源分配
- **内存管理**: 限制日志缓存大小，自动清理

## 2025-08-08 更新日志

### 配置面板完善与版本统一 (v2.3)
**功能优化**: 将5个标签页精简为4个更合理的分组
- **触发设置**: 合并静置触发和定时触发设置
- **同步等待时间**: OneDrive同步等待、全局冷却时间、重试设置
- **日志行为**: 日志记录开关、级别、文件保留数量
- **界面行为**: 窗口关闭行为、开发功能开关

**UI改进**:
- 去除顶部"配置面板"标题，界面更简洁
- 调整默认大小为800x800固定尺寸
- 按钮文字简化（"导入配置"→"导入"，"导出配置"→"导出"）

### 关闭行为系统重构
**核心修复**:
- 修复配置面板保存后主窗口不重新读取配置的问题
- 在ConfigManager中添加reload()方法支持配置热重载
- 在on_closing()方法中调用config.reload()确保使用最新配置

**对话框处理优化**:
- 修复对话框结果处理逻辑，正确区分dialog.result和dialog.close_method
- 添加详细的DEBUG日志记录对话框交互过程
- 优化系统托盘状态检查，确保最小化功能正常工作

**字体显示修复**:
- 将关闭对话框所有文字字体从Arial改为Microsoft YaHei UI
- 解决中文字符显示不规整的问题
- 保持与主程序字体风格统一

**版本号统一**:
- 将所有项目文件中的版本号统一为v2.3
- 主窗口标题、类文档、版本标签均更新至v2.3
- 统一版本描述为"配置面板优化版"

**版本号自动化管理系统**:
- 创建`version.json`统一版本配置文件
- 实现`scripts/update_version.py`自动更新脚本
- 添加`core/version_helper.py`动态版本读取模块
- 提供`update_version.bat`便捷批处理工具
- 实现单点配置、自动更新、动态读取的完整版本管理方案

### 系统托盘功能完善
**启动时序优化**:
- 将系统托盘初始化移至日志系统之后，确保启动状态能被正确记录
- 添加托盘启动成功/失败的详细日志记录
- 优化托盘不可用时的降级处理逻辑

**交互改进**:
- 完善从托盘恢复主窗口的功能（restore_from_tray方法）
- 统一托盘相关方法命名（stop_tray vs stop等）
- 增强错误处理和异常恢复机制

## 2025-08-10 更新日志

### 日志系统完全统一 (v3.0)
**核心问题解决**:
- **日志级别过滤失效问题**: 修复了GUI中设置日志级别为info后仍显示DEBUG信息的bug
- **根本原因**: GUI的`log_message()`方法缺少日志级别过滤功能
- **解决方案**: 实现了`_should_log_level()`方法，支持DEBUG、INFO、WARNING、ERROR、CRITICAL级别过滤

**日志系统架构优化**:
- **双重日志系统协作**: GUI使用`self.log_message()`(界面显示+文件记录)，Core模块使用unified logger(文件记录)
- **避免递归调用**: 禁用GUI回调以避免logger和GUI之间的循环调用
- **配置驱动**: 日志级别由`configs/sync_config.json`中的`logging.level`统一控制
- **实时生效**: 配置面板保存后立即应用新的日志级别设置

**性能调试日志管理**:
- **生产环境优化**: 创建`configs/performance_debug_config.json`配置文件
- **性能日志禁用**: 设置`enabled: false`禁用app_*.log性能调试日志输出
- **可配置阈值**: 支持不同性能等级的阈值设置(fast/normal/slow/very_slow)

**Core模块日志使用状况分析**:
- **全面审计**: 分析12个core模块的日志系统使用情况
- **识别问题**: 发现4个模块部分使用统一logger，8个模块未使用
- **改进建议**: 识别100+个需要转换的print语句，为后续优化提供指导

**技术改进**:
- **级别优先级系统**: 实现数字优先级映射(DEBUG:10, INFO:20, WARNING:30, ERROR:40, CRITICAL:50)
- **异常处理**: 配置获取失败时默认使用INFO级别过滤
- **向前兼容**: SUCCESS级别映射到INFO级别，保持现有代码兼容