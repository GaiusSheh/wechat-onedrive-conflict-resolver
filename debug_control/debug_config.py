#!/usr/bin/env python3
"""
开发者调试开关配置
这些值在打包时会被固化到exe中，用户无法看到或修改
修改这些常量后需要重启程序生效
"""

# ===== 四套调试系统开关 =====
# 开发时可以修改这些布尔值来控制调试功能
# 发行版时建议全部设为False

# 性能调试：记录函数执行时间，分析性能瓶颈
PERFORMANCE_DEBUG_ENABLED = False

# GUI调试：记录界面事件、布局变化等
GUI_DEBUG_ENABLED = False

# 图标调试：记录系统托盘图标相关操作
ICON_DEBUG_ENABLED = False

# 同步流程调试：短路同步流程，3秒返回（便于GUI测试）
SYNC_DEBUG_ENABLED = False


# ===== 性能调试配置 =====
# 性能阈值设置（毫秒）
PERFORMANCE_THRESHOLDS = {
    "fast": 50,        # 快速：50ms以下
    "normal": 100,     # 正常：100ms以下
    "slow": 200,       # 较慢：200ms以下
    "very_slow": 500   # 很慢：500ms以上
}

# 性能调试组件配置（预留扩展）
PERFORMANCE_COMPONENTS = {}


# ===== GUI调试配置 =====
# GUI组件调试详细配置
GUI_COMPONENTS = {
    "layout": {
        "enabled": True,
        "log_frequency_seconds": 1  # 布局信息记录频率
    },
    "buttons": {
        "enabled": True,
        "log_clicks": True  # 是否记录按钮点击
    },
    "status_updates": {
        "enabled": True,
        "log_frequency_seconds": 5  # 状态更新记录频率
    },
    "window_events": {
        "enabled": True,
        "log_resize": True,   # 记录窗口大小变化
        "log_focus": False    # 记录窗口焦点变化
    }
}


# ===== 图标调试配置 =====
# 图标调试详细设置
ICON_SETTINGS = {
    "log_file_operations": True,      # 记录图标文件操作
    "log_image_processing": True,     # 记录图像处理过程
    "log_dpi_scaling": True,          # 记录DPI缩放过程
    "log_format_conversion": True,    # 记录格式转换过程
    "log_system_info": True,          # 记录系统信息
    "max_retry_attempts": 5           # 最大重试次数
}

# 图标调试输出配置
ICON_OUTPUT = {
    "include_timestamps": True,       # 包含时间戳
    "include_system_info": True,      # 包含系统信息
    "verbose_errors": True            # 详细错误信息
}


# ===== 生产环境配置建议 =====
"""
发行版建议配置（复制粘贴使用）：

PERFORMANCE_DEBUG_ENABLED = False
GUI_DEBUG_ENABLED = False  
ICON_DEBUG_ENABLED = False
SYNC_DEBUG_ENABLED = False
"""