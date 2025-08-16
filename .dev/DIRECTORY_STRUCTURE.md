# 项目目录结构

> **版本**: v4.1 正式版 + 开机自启动  
> **最后更新**: 2025-08-15

## 📁 根目录结构（发行版）

```
Wechat-tools/
├── 📄 README.md                 # 项目说明文档（用户指南）
├── 📄 gui_app.py               # GUI应用启动器
├── 📄 start_gui.bat            # Windows启动脚本
├── 📄 requirements.txt         # Python依赖
├── 📄 version.json             # 版本配置文件 (v4.1根目录统一)
├── 📁 build/                   # 构建系统目录 (v4.0重组)
│   ├── BUILD_GUIDE.md          # 构建指南文档
│   ├── scripts/                # 构建脚本
│   │   ├── build_exe.py        # 主构建脚本
│   │   ├── generate_version_info.py # 版本信息生成器
│   │   └── build.bat           # Windows快速构建
│   ├── config/                 # 构建配置
│   │   ├── version.json        # 版本配置数据
│   │   ├── version_info.txt    # Windows版本信息文件
│   │   └── WeChatOneDriveTool.spec # PyInstaller规格
│   └── temp/                   # 临时文件和缓存
├── 📁 configs/                 # 用户配置文件目录
│   ├── configs.json            # 主配置文件 (v4.0简化)
│   └── config_examples.md      # 配置示例说明
├── 📁 core/                    # 核心功能模块
│   ├── config_manager.py       # 配置管理器
│   ├── global_cooldown.py      # 全局冷却管理
│   ├── idle_detector.py        # 空闲检测器
│   ├── logger_helper.py        # 日志助手
│   ├── onedrive_controller.py  # OneDrive控制器
│   ├── performance_debug.py    # 性能调试系统 (GUI必需模块)
│   ├── performance_monitor.py  # 性能监控器
│   ├── startup_manager.py      # 开机自启动管理器 (v4.0.3恢复)
│   ├── sync_monitor.py         # 同步监控器
│   ├── sync_workflow.py        # 同步工作流
│   ├── task_scheduler.py       # 任务调度器
│   ├── version_helper.py       # 版本管理助手
│   ├── wechat_auto_login.py    # 微信自动登录 (实现但未启用)
│   └── wechat_controller.py    # 微信控制器
├── 📁 debug_control/           # 调试控制模块 (v4.0新增)
│   ├── __init__.py             # 模块导出
│   ├── debug_config.py         # 统一调试配置 (4个开关)
│   └── debug_manager.py        # 统一调试管理器
├── 📁 gui/                     # GUI界面模块
│   ├── __init__.py
│   ├── close_dialog.py         # 关闭对话框
│   ├── config_panel.py         # 配置面板
│   ├── icon_manager.py         # 图标管理器
│   ├── main_window.py          # 主窗口
│   ├── system_tray.py          # 系统托盘
│   └── resources/              # 资源文件
│       ├── downloads/          # 下载资源
│       └── icons/              # 图标文件
├── 📁 data/                    # 运行时数据目录
│   └── global_cooldown_state.json  # 冷却状态文件
├── 📁 logs/                    # 四套日志架构 (v4.0)
│   ├── main/                   # 主日志 (用户级别)
│   ├── perf/                   # 性能调试日志 (开发级别)
│   ├── gui/                    # GUI调试日志 (开发级别)
│   └── icon/                   # 图标调试日志 (开发级别)
└── 📁 .dev/                    # 开发相关内容
    ├── CHANGELOG.md            # 开发日志
    ├── DIRECTORY_STRUCTURE.md  # 本文档
    ├── requirements.md         # 功能需求
    ├── performance_data/       # 性能测试数据
    ├── project explain/        # 项目说明文档
    ├── plans/                  # 规划文档
    │   ├── implementation_plan.md
    │   ├── implemented/        # 已实现功能
    │   ├── implementing/       # 开发中功能
    │   └── future/             # 未来规划
    ├── tools/                  # 开发工具
    │   ├── check_dependencies.py
    │   ├── quick_start.py
    │   └── README.md
    ├── tests/                  # 测试文件
    └── deprecated/             # 废弃文件归档
        ├── scripts/            # 废弃脚本
        ├── core_backup/        # 核心模块备份
        ├── gui_backup/         # GUI模块备份  
        ├── docs_backup/        # 文档备份
        └── tests_backup/       # 测试文件备份
```

## 🔧 核心模块说明

### 配置管理 (configs/)
- `configs.json` - 主配置文件，v4.0简化配置结构
- `config_examples.md` - 配置示例和说明文档

### 构建系统 (build/) - v4.0重组
- `BUILD_GUIDE.md` - 完整构建指南和故障排除文档
- `scripts/` - 构建脚本目录
  - `build_exe.py` - 主构建脚本，全自动化构建流程
  - `generate_version_info.py` - 版本信息生成器，自动生成Windows版本信息
  - `build.bat` - Windows快速构建脚本
- `config/` - 构建配置目录
  - `version.json` - 项目版本配置数据
  - `version_info.txt` - Windows exe文件版本信息
  - `WeChatOneDriveTool.spec` - PyInstaller打包配置
- `temp/` - PyInstaller临时文件和缓存目录

### 调试控制 (debug_control/) - v4.0新增
- `debug_config.py` - 统一调试配置，包含4个开关（性能/GUI/图标/同步）
- `debug_manager.py` - 统一调试管理器，Python常量配置系统
- `__init__.py` - 模块导出和统一接口

### 核心功能 (core/)
- `config_manager.py` - 配置文件读取、验证、热重载
- `global_cooldown.py` - 全局冷却时间管理，防止频繁触发
- `idle_detector.py` - 用户空闲状态检测
- `logger_helper.py` - 统一日志系统
- `onedrive_controller.py` - OneDrive进程控制
- `performance_debug.py` - GUI性能调试系统 (GUI模块必需依赖)
- `performance_monitor.py` - 性能监控和优化
- `startup_manager.py` - 开机自启动管理器，支持注册表操作和exe路径检测
- `sync_monitor.py` - 后台监控服务，支持定时和空闲触发
- `sync_workflow.py` - 完整同步流程控制
- `task_scheduler.py` - 定时任务调度
- `version_helper.py` - 动态版本管理系统
- `wechat_auto_login.py` - 微信自动登录功能 (实现但未启用)
- `wechat_controller.py` - 微信进程管理

### GUI界面 (gui/)
- `main_window.py` - 主界面窗口，基于ttkbootstrap现代化设计
- `config_panel.py` - 配置面板，中文本地化界面
- `system_tray.py` - 系统托盘功能
- `icon_manager.py` - 图标资源管理
- `resources/icons/` - UI图标文件

### 运行时数据 (data/)
- `global_cooldown_state.json` - 冷却状态持久化文件

### 四套日志系统 (logs/) - v4.0架构革命
- `main/` - 主日志文件（用户级别），始终生成
- `perf/` - 性能调试日志（开发级别），开关控制
- `gui/` - GUI调试日志（开发级别），开关控制  
- `icon/` - 图标调试日志（开发级别），开关控制
- 支持DEBUG/INFO/WARNING/ERROR分级记录

## 📊 开发内容 (.dev/)

### 文档管理
- `CHANGELOG.md` - 完整开发历程和技术改进记录
- `plans/` - 功能规划文档，按实现状态分类
- `requirements.md` - 详细功能需求文档

### 开发工具
- `tools/` - 环境检查、依赖安装等开发辅助工具
- `tests/` - 测试文件和测试数据

### 历史归档 - v4.0.3整理
- `deprecated/` - 废弃文件按类型分类保存
  - `scripts/` - 废弃的开发脚本
  - `core_backup/` - 核心模块历史版本（startup_manager.py已恢复使用）
  - `gui_backup/` - GUI模块历史版本（v4.0.2合并）
  - `docs_backup/` - 文档历史版本
  - `tests_backup/` - 测试文件备份（v4.0.2新增）

## 🎯 目录设计原则

1. **发行版简洁** - 根目录只保留用户需要的文件
2. **开发内容分离** - 所有开发相关文件统一在 `.dev/` 中
3. **功能模块化** - 按功能划分目录，职责清晰
4. **调试控制独立** - v4.0将调试相关功能独立到 `debug_control/`
5. **日志架构分层** - v4.0实现四套独立日志系统
6. **配置管理统一** - Python常量配置与JSON用户配置分离
7. **历史可追溯** - 重要变更保留历史版本供参考
8. **文档完整** - 每个目录都有相应的说明文档

## 📝 文件生命周期

- **活跃开发** → 对应模块目录 (core/, gui/, configs/, debug_control/)
- **开发辅助** → .dev/tools/
- **规划文档** → .dev/plans/ (按状态分类)
- **功能完成** → .dev/plans/implemented/
- **废弃替换** → .dev/deprecated/ (按类型分类)

## 🚀 v4.0架构亮点

1. **调试控制模块化**: 独立的 `debug_control/` 目录管理所有调试功能
2. **Python常量配置**: 革命性配置管理，性能提升2300倍
3. **四套日志架构**: 独立的日志子目录，开关精确控制
4. **构建系统专业化**: 独立的 `build/` 目录，职责分离的构建架构
5. **清理废弃内容**: 移除 `gui/deprecated/`，整理到 `.dev/deprecated/`
6. **模块路径优化**: 统一导入路径，提升代码可维护性

这种结构确保了项目的可维护性和用户友好性，同时实现了开发配置与用户配置的完美分离，为软件架构提供了创新的解决方案。