#!/usr/bin/env python3
"""
演示GUI性能监控日志输出
展示性能监控数据如何记录到项目统一日志系统中
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

# 导入性能调试和日志系统
from core.performance_debug import (
    enable_performance_debug, measure_time, log_user_action, 
    log_system_call, log_gui_update, perf_timer
)

def demo_performance_logging():
    """演示性能监控如何集成到日志系统"""
    
    print("=== GUI性能监控日志演示 ===\n")
    print("性能监控数据将记录到项目统一日志系统中，而不是直接打印到控制台")
    print("日志级别映射：")
    print("- PERF-DEBUG    -> logger.debug()   (< 50ms)")
    print("- PERF-INFO     -> logger.info()    (50-100ms)")  
    print("- PERF-WARNING  -> logger.warning() (100-200ms)")
    print("- PERF-CRITICAL -> logger.error()   (> 200ms)")
    print()
    
    # 确保性能调试开启
    enable_performance_debug()
    
    # 模拟不同性能级别的操作
    @measure_time("LogDemo", "快速操作")
    def fast_operation():
        log_user_action("LogDemo", "快速操作点击")
        time.sleep(0.03)  # 30ms - 应该记录为DEBUG级别
        return "fast"
    
    @measure_time("LogDemo", "正常操作") 
    def normal_operation():
        log_user_action("LogDemo", "正常操作点击")
        time.sleep(0.08)  # 80ms - 应该记录为INFO级别
        return "normal"
        
    @measure_time("LogDemo", "慢操作")
    def slow_operation():
        log_user_action("LogDemo", "慢操作点击")
        time.sleep(0.15)  # 150ms - 应该记录为WARNING级别
        log_gui_update("LogDemo", "界面更新完成")
        return "slow"
    
    @measure_time("LogDemo", "很慢操作")
    def very_slow_operation():
        log_user_action("LogDemo", "很慢操作点击")
        time.sleep(0.25)  # 250ms - 应该记录为CRITICAL级别
        log_system_call("模拟系统调用", 200.5)
        return "very_slow"
    
    print("开始执行不同耗时的操作...")
    print("(性能数据将记录到日志系统中)\n")
    
    fast_operation()
    normal_operation()
    slow_operation() 
    very_slow_operation()
    
    print("演示完成！")
    print("\n性能监控特性：")
    print("1. 用户交互记录: 每次点击、菜单选择等操作")
    print("2. 系统调用计时: 微信/OneDrive状态检查耗时")  
    print("3. GUI更新性能: 界面刷新和状态更新时间")
    print("4. 完整操作链路: 从用户触发到操作完成的总耗时")
    print("5. 自动性能分级: 根据耗时自动选择合适的日志级别")
    print("6. 统一日志管理: 集成到项目现有日志系统中")
    
    print("\n配置说明：")
    print("- 通过 configs/performance_debug_config.json 控制开关")
    print("- 可以按组件分别控制性能监控")
    print("- 支持自定义性能阈值设置")
    
    print("\n在实际GUI程序中使用时：")
    print("- 启动 python gui_app.py")
    print("- 点击各种按钮和菜单")
    print("- 性能数据会自动记录到日志文件中")
    print("- 可以通过日志文件分析GUI响应性能")

if __name__ == "__main__":
    demo_performance_logging()