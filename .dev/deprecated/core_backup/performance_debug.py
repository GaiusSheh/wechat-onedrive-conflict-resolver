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

# 加载配置
def load_perf_config():
    """加载性能调试配置"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'performance_debug_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            return config_data.get('performance_debug', DEFAULT_CONFIG)
    except:
        return DEFAULT_CONFIG

# 全局配置
_PERF_CONFIG = load_perf_config()
PERFORMANCE_DEBUG_ENABLED = _PERF_CONFIG.get('enabled', True)
PERFORMANCE_THRESHOLDS = _PERF_CONFIG.get('thresholds', DEFAULT_CONFIG['thresholds'])

def perf_log(message, level="INFO"):
    """性能调试日志函数"""
    if PERFORMANCE_DEBUG_ENABLED:
        # 集成到项目统一日志系统
        try:
            # 导入统一日志系统
            from core.logger_helper import logger
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            perf_message = f"[{timestamp}][PERF-{level}] {message}"
            
            # 根据级别选择对应的logger方法
            if level == "CRITICAL":
                logger.error(perf_message)  # 使用ERROR级别记录CRITICAL性能问题
            elif level == "WARNING":
                logger.warning(perf_message)
            elif level == "DEBUG":
                logger.debug(perf_message)
            else:  # INFO
                logger.info(perf_message)
                
        except ImportError:
            # 如果无法导入logger，回退到print方式
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"[{timestamp}][PERF-{level}] {message}")

def measure_time(component, operation):
    """测量操作耗时的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not PERFORMANCE_DEBUG_ENABLED:
                return func(*args, **kwargs)
            
            start_time = time.time()
            perf_log(f"{component}.{operation} 开始")
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # 根据耗时选择日志级别
                if duration_ms > PERFORMANCE_THRESHOLDS['very_slow']:
                    level = "CRITICAL"
                elif duration_ms > PERFORMANCE_THRESHOLDS['slow']:
                    level = "WARNING"
                elif duration_ms > PERFORMANCE_THRESHOLDS['normal']:
                    level = "INFO"
                else:
                    level = "DEBUG"
                
                perf_log(f"{component}.{operation} 完成 - {duration_ms:.1f}ms", level)
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                perf_log(f"{component}.{operation} 异常 - {duration_ms:.1f}ms - {str(e)}", "ERROR")
                raise
                
        return wrapper
    return decorator

def perf_timer():
    """简单的计时器上下文管理器"""
    class PerfTimer:
        def __init__(self):
            self.start_time = None
            
        def __enter__(self):
            if PERFORMANCE_DEBUG_ENABLED:
                self.start_time = time.time()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if PERFORMANCE_DEBUG_ENABLED and self.start_time:
                duration_ms = (time.time() - self.start_time) * 1000
                perf_log(f"代码块执行时间: {duration_ms:.1f}ms")
    
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
    """启用性能调试"""
    global PERFORMANCE_DEBUG_ENABLED
    PERFORMANCE_DEBUG_ENABLED = True
    perf_log("性能调试已启用")

def disable_performance_debug():
    """禁用性能调试"""
    global PERFORMANCE_DEBUG_ENABLED
    if PERFORMANCE_DEBUG_ENABLED:
        perf_log("性能调试即将禁用")
    PERFORMANCE_DEBUG_ENABLED = False

def is_performance_debug_enabled():
    """检查性能调试是否启用"""
    return PERFORMANCE_DEBUG_ENABLED

# 使用示例
if __name__ == "__main__":
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
    
    print("\n--- 禁用性能调试 ---")
    disable_performance_debug()
    
    # 再次执行（应该没有输出）
    test_function()
    log_user_action("MainWindow", "另一个操作")
    
    print("\n--- 重新启用 ---")
    enable_performance_debug()
    test_function()