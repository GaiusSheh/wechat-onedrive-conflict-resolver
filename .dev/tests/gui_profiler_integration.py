#!/usr/bin/env python3
"""
GUI性能分析器集成接口
提供简单的方法将性能监控集成到现有GUI中，而不修改现有代码结构

使用方法：
1. 在主GUI启动时调用 setup_gui_profiling()
2. 在需要监控的操作前后添加简单的调用
3. 定期生成性能报告

设计原则：最小侵入，最大收益
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
from functools import wraps
from typing import Callable, Any, Dict, Optional

# 导入我们的profiler
from gui_profiler import gui_profiler, profile_user_interaction, profile_gui_update

class GUIPerformanceMonitor:
    """GUI性能监控器 - 简单集成接口"""
    
    def __init__(self):
        self.profiler = gui_profiler
        self.monitoring_active = False
        self.auto_report_interval = 300  # 5分钟自动生成一次报告
        self._report_thread = None
        
    def start_monitoring(self, session_name: str = None):
        """开始性能监控"""
        self.monitoring_active = True
        session_id = self.profiler.start_session(session_name)
        print(f"🎯 GUI性能监控已启动: {session_id}")
        
        # 启动自动报告线程
        if self._report_thread is None or not self._report_thread.is_alive():
            self._report_thread = threading.Thread(target=self._auto_report_loop, daemon=True)
            self._report_thread.start()
        
        return session_id
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        report_path = self.profiler.save_report()
        print(f"📊 性能监控已停止，报告已保存: {report_path}")
        return report_path
    
    def _auto_report_loop(self):
        """自动报告循环"""
        while self.monitoring_active:
            time.sleep(self.auto_report_interval)
            if self.monitoring_active:
                try:
                    self.profiler.save_report()
                    print("📊 自动性能报告已生成")
                except Exception as e:
                    print(f"⚠️  生成自动报告失败: {e}")

# 全局监控器实例
performance_monitor = GUIPerformanceMonitor()

# 简化的性能监控装饰器
def monitor_button_click(button_name: str):
    """监控按钮点击性能"""
    return profile_user_interaction("Button", button_name)

def monitor_window_update(window_name: str):
    """监控窗口更新性能"""
    return profile_gui_update("Window", window_name)

def monitor_status_update(component: str):
    """监控状态更新性能"""
    return profile_gui_update("Status", component)

# 快速集成函数
def setup_gui_profiling(enable: bool = True, session_name: str = None):
    """设置GUI性能分析
    
    Args:
        enable: 是否启用性能监控
        session_name: 会话名称，默认使用时间戳
    """
    if enable:
        return performance_monitor.start_monitoring(session_name)
    return None

def quick_track_interaction(component: str, action: str, func: Callable, *args, **kwargs):
    """快速追踪交互性能
    
    使用方法：
    result = quick_track_interaction("MainWindow", "同步按钮", self.run_sync_workflow)
    """
    if not performance_monitor.monitoring_active:
        return func(*args, **kwargs)
    
    event_id = gui_profiler.track_user_interaction(component, action)
    try:
        result = func(*args, **kwargs)
        gui_profiler.finish_interaction(event_id, success=True)
        return result
    except Exception as e:
        gui_profiler.finish_interaction(event_id, success=False, 
                                       result_metadata={'error': str(e)})
        raise

def show_performance_summary():
    """显示性能摘要对话框"""
    try:
        report = gui_profiler.generate_performance_report()
        summary = report.get('interaction_summary', {})
        
        if not summary:
            messagebox.showinfo("性能摘要", "暂无性能数据")
            return
        
        message = f"""=== GUI性能摘要 ===

总交互次数: {summary.get('total_interactions', 0)}
平均响应时间: {summary.get('average_response_time_ms', 0):.1f}ms  
成功率: {summary.get('success_rate', 0)*100:.1f}%

=== 性能分布 ==="""
        
        perf_dist = report.get('performance_distribution', {})
        for level, count in perf_dist.items():
            message += f"\n{level}: {count}次"
        
        bottlenecks = report.get('bottleneck_analysis', [])
        if bottlenecks:
            message += "\n\n=== 性能瓶颈 ==="
            for bottleneck in bottlenecks[:3]:
                message += f"\n{bottleneck['component']}: {bottleneck['avg_response_time_ms']:.1f}ms"
        
        recommendations = report.get('recommendations', [])
        if recommendations:
            message += "\n\n=== 优化建议 ==="
            for rec in recommendations[:3]:
                message += f"\n• {rec}"
        
        messagebox.showinfo("GUI性能分析", message)
        
    except Exception as e:
        messagebox.showerror("错误", f"生成性能摘要失败: {e}")

# 用于现有代码的最小侵入集成示例
class PerformanceIntegrationHelper:
    """性能集成辅助类 - 提供最简单的集成方法"""
    
    @staticmethod
    def wrap_button_command(original_command: Callable, button_name: str):
        """包装按钮命令以添加性能监控
        
        使用方法（在现有代码中）：
        # 原来的代码：
        # button = ttk.Button(parent, text="同步", command=self.run_sync)
        
        # 添加性能监控：
        # button = ttk.Button(parent, text="同步", 
        #                    command=PerformanceIntegrationHelper.wrap_button_command(
        #                        self.run_sync, "同步按钮"))
        """
        @wraps(original_command)
        def wrapped_command(*args, **kwargs):
            return quick_track_interaction("Button", button_name, original_command, *args, **kwargs)
        
        return wrapped_command
    
    @staticmethod
    def wrap_status_update(original_update: Callable, component_name: str):
        """包装状态更新方法以添加性能监控"""
        @wraps(original_update)
        def wrapped_update(*args, **kwargs):
            if not performance_monitor.monitoring_active:
                return original_update(*args, **kwargs)
            
            event_id = gui_profiler.track_gui_update("StatusUpdate", component_name)
            try:
                result = original_update(*args, **kwargs)
                gui_profiler.finish_gui_update(event_id)
                return result
            except Exception as e:
                gui_profiler.finish_gui_update(event_id)
                raise
        
        return wrapped_update
    
    @staticmethod
    def add_performance_menu(parent_menu):
        """向现有菜单添加性能分析选项
        
        使用方法：
        # 在现有的菜单创建代码中添加：
        # PerformanceIntegrationHelper.add_performance_menu(self.menubar)
        """
        if not isinstance(parent_menu, tk.Menu):
            return
        
        # 创建性能菜单
        perf_menu = tk.Menu(parent_menu, tearoff=0)
        perf_menu.add_command(label="开始性能监控", 
                             command=lambda: setup_gui_profiling(True))
        perf_menu.add_command(label="停止性能监控", 
                             command=performance_monitor.stop_monitoring)
        perf_menu.add_separator()
        perf_menu.add_command(label="显示性能摘要", 
                             command=show_performance_summary)
        perf_menu.add_command(label="生成性能报告", 
                             command=gui_profiler.save_report)
        
        parent_menu.add_cascade(label="性能分析", menu=perf_menu)

# 简化的使用示例
def demo_integration():
    """演示如何集成到现有GUI中"""
    
    print("=== GUI性能监控集成演示 ===\n")
    
    # 1. 启动性能监控
    session_id = setup_gui_profiling(True, "demo_session")
    
    # 2. 模拟现有的GUI操作方法
    def original_sync_function():
        print("执行同步操作...")
        time.sleep(0.1)  # 模拟100ms操作
        return "同步成功"
    
    def original_status_update():
        print("更新状态显示...")
        time.sleep(0.05)  # 模拟50ms更新
        return "状态已更新"
    
    # 3. 使用包装后的方法（最小侵入）
    wrapped_sync = PerformanceIntegrationHelper.wrap_button_command(
        original_sync_function, "同步按钮"
    )
    
    wrapped_status = PerformanceIntegrationHelper.wrap_status_update(
        original_status_update, "主窗口状态"
    )
    
    # 4. 执行操作（现有代码调用方式不变）
    result1 = wrapped_sync()
    result2 = wrapped_status()
    
    # 5. 快速追踪新操作
    def config_load():
        print("加载配置...")
        time.sleep(0.08)
        return "配置加载完成"
    
    result3 = quick_track_interaction("ConfigPanel", "加载配置", config_load)
    
    print(f"\n操作结果: {result1}, {result2}, {result3}")
    
    # 6. 显示性能摘要
    time.sleep(0.1)  # 让数据处理完成
    show_performance_summary()
    
    # 7. 停止监控
    report_path = performance_monitor.stop_monitoring()
    
    print(f"\n演示完成，性能报告: {report_path}")

if __name__ == "__main__":
    demo_integration()