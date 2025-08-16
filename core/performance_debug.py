#!/usr/bin/env python3
"""
性能调试开关系统
提供统一的性能调试日志控制，可以一键开关所有性能相关的日志输出
"""

import time
from functools import wraps
from datetime import datetime

# 导入配置管理
import json
import os

# 导入统一日志系统和调试管理器
try:
    from core.logger_helper import logger as main_logger
    from debug_control.debug_manager import debug_manager
except ImportError:
    main_logger = None
    debug_manager = None

# 默认配置
DEFAULT_CONFIG = {
    'enabled': True,
    'thresholds': {
        'fast': 50,
        'normal': 100,
        'slow': 200,
        'very_slow': 500
    },
    'components': {}
}

# 现在使用统一的debug_manager
def is_performance_debug_enabled():
    """检查性能调试是否启用"""
    if debug_manager:
        return debug_manager.is_performance_debug_enabled()
    return False

def get_performance_threshold(threshold_name):
    """获取性能阈值（毫秒）"""
    if debug_manager:
        return debug_manager.get_performance_threshold(threshold_name)
    return DEFAULT_CONFIG['thresholds'].get(threshold_name, 100)

# 为了向后兼容，保留全局变量
# 注意：这些值在程序运行时会动态更新
try:
    PERFORMANCE_DEBUG_ENABLED = is_performance_debug_enabled()
    PERFORMANCE_THRESHOLDS = {
        'fast': get_performance_threshold('fast'),
        'normal': get_performance_threshold('normal'),
        'slow': get_performance_threshold('slow'),
        'very_slow': get_performance_threshold('very_slow')
    }
except:
    # 如果debug_manager未初始化，使用默认值
    PERFORMANCE_DEBUG_ENABLED = False
    PERFORMANCE_THRESHOLDS = DEFAULT_CONFIG['thresholds']

def perf_log(message, level="INFO"):
    """性能调试日志函数 - 现在使用统一的perf_debug系统"""
    if is_performance_debug_enabled():
        try:
            from core.logger_helper import logger
            # 使用新的perf_debug方法，根据level选择duration
            duration_ms = 0  # 默认值，在measure_time中会被覆盖
            
            if level == "CRITICAL":
                duration_ms = get_performance_threshold('very_slow') + 100
            elif level == "WARNING":
                duration_ms = get_performance_threshold('slow') + 50
            elif level == "INFO":
                duration_ms = get_performance_threshold('normal') + 10
            else:  # DEBUG
                duration_ms = get_performance_threshold('fast') - 10
                
            logger.perf_debug(message, duration_ms / 1000.0)  # 转换为秒
                
        except ImportError:
            # 如果无法导入logger，回退到print方式
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"[{timestamp}][PERF-{level}] {message}")

def measure_time(component, operation):
    """测量操作耗时的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_performance_debug_enabled():
                return func(*args, **kwargs)
            
            start_time = time.time()
            
            try:
                from core.logger_helper import logger
                logger.perf_debug(f"{component}.{operation} 开始", 0.0)
                
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.perf_debug(f"{component}.{operation} 完成", duration)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                try:
                    from core.logger_helper import logger
                    logger.perf_debug(f"{component}.{operation} 异常 - {str(e)}", duration)
                except ImportError:
                    pass
                raise
                
        return wrapper
    return decorator

def perf_timer():
    """简单的计时器上下文管理器"""
    class PerfTimer:
        def __init__(self):
            self.start_time = None
            
        def __enter__(self):
            if is_performance_debug_enabled():
                self.start_time = time.time()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if is_performance_debug_enabled() and self.start_time:
                duration = time.time() - self.start_time
                try:
                    from core.logger_helper import logger
                    logger.perf_debug("代码块执行时间", duration)
                except ImportError:
                    pass
    
    return PerfTimer()

def log_user_action(component, action):
    """记录用户操作"""
    perf_log(f"用户操作: {component} - {action}", "INFO")

def log_gui_update(component, update_type):
    """记录GUI更新"""
    perf_log(f"GUI更新: {component} - {update_type}", "DEBUG")

def log_system_call(operation, duration_ms=None):
    """记录系统调用"""
    if duration_ms:
        level = "WARNING" if duration_ms > 200 else "INFO"
        perf_log(f"系统调用: {operation} - {duration_ms:.1f}ms", level)
    else:
        perf_log(f"系统调用: {operation}", "INFO")

def enable_performance_debug():
    """启用性能调试 - 警告：现在需要通过修改配置文件启用"""
    print("警告: enable_performance_debug()已废弃")
    print("请通过修改 configs/performance_debug_config.json 中的 enabled 字段来控制性能调试")
    perf_log("性能调试状态检查")

def disable_performance_debug():
    """禁用性能调试 - 警告：现在需要通过修改配置文件禁用"""
    print("警告: disable_performance_debug()已废弃")
    print("请通过修改 configs/performance_debug_config.json 中的 enabled 字段来控制性能调试")
    perf_log("性能调试状态检查")

# 使用示例
if __name__ == "__main__":
    if main_logger:
        main_logger.info("=== 性能调试系统测试 ===")
    else:
        print("=== 性能调试系统测试 ===")
    
    # 测试装饰器
    @measure_time("TestComponent", "测试操作")
    def test_function():
        time.sleep(0.1)  # 模拟100ms操作
        return "完成"
    
    # 测试计时器
    def test_timer():
        with perf_timer():
            time.sleep(0.05)  # 模拟50ms操作
    
    # 执行测试
    log_user_action("MainWindow", "按钮点击")
    test_function()
    test_timer()
    log_gui_update("StatusPanel", "状态刷新")
    log_system_call("微信状态检查", 150.5)
    
    if main_logger:
        main_logger.info("\n--- 禁用性能调试 ---")
    else:
        print("\n--- 禁用性能调试 ---")
    disable_performance_debug()
    
    # 再次执行（应该没有输出）
    test_function()
    log_user_action("MainWindow", "另一个操作")
    
    if main_logger:
        main_logger.info("\n--- 重新启用 ---")
    else:
        print("\n--- 重新启用 ---")
    enable_performance_debug()
    test_function()