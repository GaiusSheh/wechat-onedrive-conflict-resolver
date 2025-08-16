# 工具脚本说明

本目录包含项目相关的辅助工具脚本。

## 脚本列表

### 开发环境工具

#### `check_dependencies.py`
**功能**: 检查项目所需的Python依赖包是否正确安装
**用法**: `python tools/check_dependencies.py`
**说明**: 
- 验证第三方依赖包（psutil、schedule等）
- 检查Python标准库模块可用性
- 提供安装建议

#### `quick_start.py`
**功能**: 项目快速启动和环境检查脚本
**用法**: `python tools/quick_start.py`
**说明**: 
- 自动检查Python版本和依赖包
- 创建默认配置文件
- 提供使用指南
- 可选择性运行测试同步流程

### 说明
**注意**: 构建和版本工具已迁移到专门的构建目录，请参考：
- **构建工具位置**: `build/scripts/` 目录
- **构建指南**: `build/BUILD_GUIDE.md`
- **快速构建**: `build/scripts/build.bat`

构建相关功能不再位于tools目录中。

## 快速使用

### 开发环境设置
```bash
# 1. 环境检查和快速启动
python .dev/tools/quick_start.py

# 2. 依赖验证
python .dev/tools/check_dependencies.py
```

### 构建发布版本
**注意**: 构建工具已迁移，请使用：
```bash
# 推荐方法: 使用专门的构建目录
build\scripts\build.bat                    # 使用默认版本
build\scripts\build.bat 4.0.3             # 指定版本号

# 详细构建
python build\scripts\build_exe.py --version 4.0.3 --clean
```

更多信息请参考 `build/BUILD_GUIDE.md`

## 文件结构

```
.dev/tools/
├── README.md                    # 本文档
├── check_dependencies.py       # 依赖检查
└── quick_start.py              # 快速启动

# 构建工具已迁移到:
build/scripts/                  # 专门的构建目录
└── BUILD_GUIDE.md              # 详细构建指南
```

## 使用建议

1. **首次使用时**: 运行 `quick_start.py` 进行环境检查和配置初始化
2. **部署时**: 使用 `check_dependencies.py` 验证环境依赖
3. **构建发布版**: 参考 `build/BUILD_GUIDE.md` 使用专门的构建系统
4. **问题排查时**: 这些工具可以帮助诊断环境配置问题

## 工具职责

本目录现专注于**开发环境工具**：
- **环境检查**: 验证Python依赖和开发环境
- **快速启动**: 项目初始化和配置检查
- **问题诊断**: 开发环境相关问题排查

**构建和版本管理**已迁移到专门的 `build/` 目录。