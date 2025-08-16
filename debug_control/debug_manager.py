#!/usr/bin/env python3
"""
调试开关管理模块
统一管理四套调试系统的开关状态
使用Python常量配置，打包时固化到exe中
"""

from typing import Dict, Any
from .debug_config import (
    PERFORMANCE_DEBUG_ENABLED,
    GUI_DEBUG_ENABLED, 
    ICON_DEBUG_ENABLED,
    PERFORMANCE_THRESHOLDS,
    PERFORMANCE_COMPONENTS,
    GUI_COMPONENTS,
    ICON_SETTINGS,
    ICON_OUTPUT
)

class DebugManager:
    """调试开关管理器 - 基于Python常量"""
    
    _instance = None
    _lock = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            import threading
            if cls._lock is None:
                cls._lock = threading.Lock()
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DebugManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
    
    def is_performance_debug_enabled(self) -> bool:
        """检查性能调试是否启用"""
        return PERFORMANCE_DEBUG_ENABLED
    
    def is_gui_debug_enabled(self) -> bool:
        """检查GUI调试是否启用"""
        return GUI_DEBUG_ENABLED
    
    def is_icon_debug_enabled(self) -> bool:
        """检查图标调试是否启用"""
        return ICON_DEBUG_ENABLED
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能调试配置"""
        return {
            "enabled": PERFORMANCE_DEBUG_ENABLED,
            "thresholds": PERFORMANCE_THRESHOLDS,
            "components": PERFORMANCE_COMPONENTS
        }
    
    def get_gui_config(self) -> Dict[str, Any]:
        """获取GUI调试配置"""
        return {
            "enabled": GUI_DEBUG_ENABLED,
            "components": GUI_COMPONENTS
        }
    
    def get_icon_config(self) -> Dict[str, Any]:
        """获取图标调试配置"""
        return {
            "enabled": ICON_DEBUG_ENABLED,
            "settings": ICON_SETTINGS,
            "output": ICON_OUTPUT
        }
    
    def is_gui_component_debug_enabled(self, component: str) -> bool:
        """检查特定GUI组件调试是否启用"""
        if not self.is_gui_debug_enabled():
            return False
        return GUI_COMPONENTS.get(component, {}).get("enabled", False)
    
    def get_icon_setting(self, setting_name: str, default=None):
        """获取图标调试的特定设置"""
        if not self.is_icon_debug_enabled():
            return default
        return ICON_SETTINGS.get(setting_name, default)
    
    def get_performance_threshold(self, threshold_name: str) -> float:
        """获取性能阈值配置（毫秒）"""
        return PERFORMANCE_THRESHOLDS.get(threshold_name, 100)
    
    def get_debug_status_summary(self) -> Dict[str, bool]:
        """获取所有调试开关状态摘要"""
        return {
            "performance_debug": self.is_performance_debug_enabled(),
            "gui_debug": self.is_gui_debug_enabled(),
            "icon_debug": self.is_icon_debug_enabled()
        }

# 全局实例
debug_manager = DebugManager()

# 便捷函数
def is_performance_debug_enabled() -> bool:
    """检查性能调试是否启用"""
    return debug_manager.is_performance_debug_enabled()

def is_gui_debug_enabled() -> bool:
    """检查GUI调试是否启用"""
    return debug_manager.is_gui_debug_enabled()

def is_icon_debug_enabled() -> bool:
    """检查图标调试是否启用"""
    return debug_manager.is_icon_debug_enabled()

def is_gui_component_debug_enabled(component: str) -> bool:
    """检查特定GUI组件调试是否启用"""
    return debug_manager.is_gui_component_debug_enabled(component)

def get_icon_debug_setting(setting_name: str, default=None):
    """获取图标调试设置"""
    return debug_manager.get_icon_setting(setting_name, default)

def get_performance_threshold(threshold_name: str) -> float:
    """获取性能阈值（毫秒）"""
    return debug_manager.get_performance_threshold(threshold_name)

if __name__ == "__main__":
    # 测试调试管理器
    print("=== 调试开关状态测试 ===")
    
    status = debug_manager.get_debug_status_summary()
    for debug_type, enabled in status.items():
        print(f"{debug_type}: {'启用' if enabled else '禁用'}")
    
    print(f"\n性能阈值配置:")
    for threshold in ['fast', 'normal', 'slow', 'very_slow']:
        value = get_performance_threshold(threshold)
        print(f"  {threshold}: {value}ms")
    
    if is_gui_debug_enabled():
        print(f"\nGUI组件调试状态:")
        components = ['layout', 'buttons', 'status_updates', 'window_events']
        for comp in components:
            enabled = is_gui_component_debug_enabled(comp)
            print(f"  {comp}: {'启用' if enabled else '禁用'}")