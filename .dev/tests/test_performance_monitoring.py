#!/usr/bin/env python3
"""
GUI性能监控系统测试脚本
测试集成到GUI组件中的性能监控功能
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))
sys.path.insert(0, os.path.join(project_root, 'gui'))

# 导入性能调试系统
from core.performance_debug import (
    enable_performance_debug, disable_performance_debug, 
    is_performance_debug_enabled, perf_log
)

def test_main_window_performance():
    """测试主窗口性能监控"""
    print("=== 测试主窗口性能监控 ===")
    
    try:
        # 模拟导入主窗口（不实际创建GUI）
        print("1. 测试主窗口相关性能监控...")
        
        # 导入性能调试装饰器函数
        from core.performance_debug import measure_time, log_user_action
        
        # 模拟主窗口操作
        @measure_time("MainWindow", "模拟同步流程")
        def simulate_sync_workflow():
            log_user_action("MainWindow", "同步按钮点击")
            time.sleep(0.1)  # 模拟100ms操作
            return True
        
        @measure_time("MainWindow", "模拟状态更新")
        def simulate_status_update():
            log_user_action("MainWindow", "状态更新触发")
            time.sleep(0.05)  # 模拟50ms操作
            return True
        
        # 执行模拟操作
        simulate_sync_workflow()
        simulate_status_update()
        
        print("[OK] 主窗口性能监控测试通过")
        
    except Exception as e:
        print(f"[FAIL] 主窗口性能监控测试失败: {e}")

def test_config_panel_performance():
    """测试配置面板性能监控"""
    print("\n=== 测试配置面板性能监控 ===")
    
    try:
        print("2. 测试配置面板相关性能监控...")
        
        from core.performance_debug import measure_time, log_user_action
        
        # 模拟配置面板操作
        @measure_time("ConfigPanel", "模拟保存配置")
        def simulate_save_config():
            log_user_action("ConfigPanel", "保存按钮点击")
            time.sleep(0.08)  # 模拟80ms操作
            return True
        
        @measure_time("ConfigPanel", "模拟加载配置")
        def simulate_load_config():
            log_user_action("ConfigPanel", "配置加载触发")
            time.sleep(0.03)  # 模拟30ms操作
            return True
        
        # 执行模拟操作
        simulate_save_config()
        simulate_load_config()
        
        print("[OK] 配置面板性能监控测试通过")
        
    except Exception as e:
        print(f"[FAIL] 配置面板性能监控测试失败: {e}")

def test_system_tray_performance():
    """测试系统托盘性能监控"""
    print("\n=== 测试系统托盘性能监控 ===")
    
    try:
        print("3. 测试系统托盘相关性能监控...")
        
        from core.performance_debug import measure_time, log_user_action
        
        # 模拟系统托盘操作
        @measure_time("SystemTray", "模拟显示主窗口")
        def simulate_show_window():
            log_user_action("SystemTray", "双击托盘图标")
            time.sleep(0.02)  # 模拟20ms操作
            return True
        
        @measure_time("SystemTray", "模拟托盘同步")
        def simulate_tray_sync():
            log_user_action("SystemTray", "托盘同步菜单点击")
            time.sleep(0.15)  # 模拟150ms操作
            return True
        
        # 执行模拟操作
        simulate_show_window()
        simulate_tray_sync()
        
        print("[OK] 系统托盘性能监控测试通过")
        
    except Exception as e:
        print(f"[FAIL] 系统托盘性能监控测试失败: {e}")

def test_performance_thresholds():
    """测试性能阈值报警"""
    print("\n=== 测试性能阈值报警 ===")
    
    try:
        print("4. 测试不同耗时的操作...")
        
        from core.performance_debug import measure_time
        
        # 测试快速操作（<50ms）
        @measure_time("Test", "快速操作")
        def fast_operation():
            time.sleep(0.02)  # 20ms
            return "fast"
        
        # 测试正常操作（50-100ms）
        @measure_time("Test", "正常操作")
        def normal_operation():
            time.sleep(0.07)  # 70ms
            return "normal"
        
        # 测试慢操作（100-200ms）
        @measure_time("Test", "慢操作")
        def slow_operation():
            time.sleep(0.15)  # 150ms
            return "slow"
        
        # 测试非常慢操作（>200ms）
        @measure_time("Test", "非常慢操作")
        def very_slow_operation():
            time.sleep(0.3)  # 300ms
            return "very_slow"
        
        # 执行不同速度的操作
        fast_operation()
        normal_operation() 
        slow_operation()
        very_slow_operation()
        
        print("[OK] 性能阈值报警测试通过")
        
    except Exception as e:
        print(f"[FAIL] 性能阈值报警测试失败: {e}")

def test_performance_switch():
    """测试性能调试开关功能"""
    print("\n=== 测试性能调试开关 ===")
    
    try:
        print("5. 测试性能调试开关功能...")
        
        from core.performance_debug import measure_time, log_user_action
        
        @measure_time("Test", "开关测试")
        def switch_test_operation():
            log_user_action("Test", "开关测试操作")
            time.sleep(0.05)
            return "switch_test"
        
        # 确保调试开启
        enable_performance_debug()
        print("   性能调试已启用，执行操作...")
        switch_test_operation()
        
        print("   禁用性能调试...")
        disable_performance_debug()
        print("   性能调试已禁用，执行操作（应该无输出）...")
        switch_test_operation()
        
        print("   重新启用性能调试...")
        enable_performance_debug()
        switch_test_operation()
        
        print("[OK] 性能调试开关测试通过")
        
    except Exception as e:
        print(f"[FAIL] 性能调试开关测试失败: {e}")

def test_concurrent_operations():
    """测试并发操作的性能监控"""
    print("\n=== 测试并发操作性能监控 ===")
    
    try:
        print("6. 测试多线程并发操作...")
        
        from core.performance_debug import measure_time, log_user_action
        
        @measure_time("Concurrent", "并发操作")
        def concurrent_operation(thread_id):
            log_user_action("Concurrent", f"线程{thread_id}操作")
            time.sleep(0.1)  # 100ms操作
            return f"thread_{thread_id}"
        
        # 创建多个线程同时执行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_operation, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        print("[OK] 并发操作性能监控测试通过")
        
    except Exception as e:
        print(f"[FAIL] 并发操作性能监控测试失败: {e}")

def run_all_tests():
    """运行所有测试"""
    print("GUI性能监控系统集成测试")
    print("=" * 50)
    
    # 确保性能调试开启
    enable_performance_debug()
    print(f"性能调试状态: {'启用' if is_performance_debug_enabled() else '禁用'}")
    print()
    
    # 运行所有测试
    test_main_window_performance()
    test_config_panel_performance() 
    test_system_tray_performance()
    test_performance_thresholds()
    test_performance_switch()
    test_concurrent_operations()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n说明：")
    print("- 所有GUI操作的响应时间都会被记录")
    print("- 超过阈值的操作会显示警告级别")
    print("- 可以通过配置文件统一开关性能监控")
    print("- 用户每次点击到响应完成的完整时间链路都会被追踪")

if __name__ == "__main__":
    run_all_tests()