#!/usr/bin/env python3
"""
性能调试集成示例
展示如何在现有GUI代码中添加性能调试，遵循项目规则：
1. 优先注释而非删除
2. 最小侵入性修改
3. 统一开关控制
"""

import time
import sys
import os

# 导入性能调试系统
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from performance_debug import (
    measure_time, perf_log, log_user_action, log_gui_update, 
    log_system_call, perf_timer, PERFORMANCE_DEBUG_ENABLED
)

class MainWindowExample:
    """主窗口示例，展示如何集成性能调试"""
    
    def __init__(self):
        perf_log("MainWindow 初始化开始")
        
        # 原有的初始化代码保持不变
        self.setup_gui()
        self.setup_monitoring()
        
        perf_log("MainWindow 初始化完成")
    
    def setup_gui(self):
        """设置GUI - 原有代码保持不变，只添加性能日志"""
        perf_log("GUI组件创建开始")
        
        # 模拟GUI创建过程
        time.sleep(0.1)  # 模拟耗时操作
        
        perf_log("GUI组件创建完成")
    
    def setup_monitoring(self):
        """设置监控 - 原有代码保持不变"""
        perf_log("监控系统初始化")
        time.sleep(0.05)
        perf_log("监控系统初始化完成")
    
    # 方法1: 使用装饰器（推荐用于重要操作）
    @measure_time("MainWindow", "同步流程")
    def on_sync_button_click(self):
        """同步按钮点击处理"""
        # DEPRECATED: 原始代码（保留注释）
        # def on_sync_button_click(self):
        #     self.run_sync_workflow()
        
        # 记录用户操作
        log_user_action("MainWindow", "同步按钮点击")
        
        # 执行原有逻辑
        self.run_sync_workflow()
    
    def run_sync_workflow(self):
        """执行同步流程 - 原有逻辑不变"""
        # 模拟同步过程
        time.sleep(0.2)  # 模拟200ms同步操作
        return "同步完成"
    
    # 方法2: 手动添加计时（适用于复杂操作）
    def update_status(self):
        """更新状态显示"""
        # OLD VERSION: 原始代码
        # def update_status(self):
        #     self.update_wechat_status()
        #     self.update_onedrive_status()
        #     self.update_cooldown_display()
        
        # PERFORMANCE DEBUG: 添加性能监控
        perf_log("状态更新开始")
        
        with perf_timer():
            # 原有的状态更新逻辑
            self.update_wechat_status()
            self.update_onedrive_status() 
            self.update_cooldown_display()
        
        log_gui_update("StatusPanel", "状态更新完成")
    
    def update_wechat_status(self):
        """更新微信状态"""
        start_time = time.time()
        
        # 模拟状态检查
        time.sleep(0.08)  # 模拟80ms API调用
        
        # 记录系统调用耗时
        duration_ms = (time.time() - start_time) * 1000
        log_system_call("微信状态检查", duration_ms)
    
    def update_onedrive_status(self):
        """更新OneDrive状态"""
        start_time = time.time()
        
        # 模拟状态检查
        time.sleep(0.12)  # 模拟120ms API调用
        
        duration_ms = (time.time() - start_time) * 1000
        log_system_call("OneDrive状态检查", duration_ms)
    
    def update_cooldown_display(self):
        """更新冷却时间显示"""
        # 快速的GUI更新操作，只在启用调试时记录
        if PERFORMANCE_DEBUG_ENABLED:
            log_gui_update("CooldownDisplay", "冷却时间更新")
        
        time.sleep(0.01)  # 模拟10ms GUI更新
    
    # 方法3: 条件性能日志（适用于频繁操作）
    def on_timer_update(self):
        """定时器更新 - 频繁操作，只记录慢操作"""
        start_time = time.time()
        
        # 执行定时更新
        time.sleep(0.03)  # 模拟30ms更新
        
        # 只有操作超过阈值时才记录
        duration_ms = (time.time() - start_time) * 1000
        if duration_ms > 50:  # 只记录超过50ms的操作
            perf_log(f"定时更新耗时较长: {duration_ms:.1f}ms", "WARNING")

# 使用示例
def demo_performance_integration():
    """演示性能调试集成"""
    print("=== 性能调试集成演示 ===")
    
    # 创建主窗口实例
    window = MainWindowExample()
    
    print("\n--- 执行各种操作 ---")
    
    # 模拟用户操作
    window.on_sync_button_click()      # 使用装饰器的方法
    window.update_status()             # 使用手动计时的方法
    window.on_timer_update()           # 条件性能日志
    
    print("\n--- 禁用性能调试后 ---")
    from performance_debug import disable_performance_debug
    disable_performance_debug()
    
    # 再次执行（应该没有性能日志输出）
    window.on_sync_button_click()
    window.update_status()
    
    print("（应该看不到性能日志了）")

if __name__ == "__main__":
    demo_performance_integration()