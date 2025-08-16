#!/usr/bin/env python3
"""
调试控制模块
包含所有调试相关的配置和管理器
"""

from .debug_config import *
from .debug_manager import debug_manager

__all__ = [
    'PERFORMANCE_DEBUG_ENABLED',
    'GUI_DEBUG_ENABLED', 
    'ICON_DEBUG_ENABLED',
    'SYNC_DEBUG_ENABLED',
    'PERFORMANCE_THRESHOLDS',
    'GUI_COMPONENTS',
    'ICON_SETTINGS',
    'debug_manager'
]