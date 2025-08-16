#!/usr/bin/env python3
"""
性能监控模块 - 跟踪应用程序CPU和内存使用情况
"""

import psutil
import time
import threading
from datetime import datetime

# 导入统一日志系统
from core.logger_helper import logger

class PerformanceMonitor:
    """性能监控器 - 跟踪CPU和内存使用"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.stats = {
            'cpu_percent': 0.0,
            'memory_mb': 0.0,
            'start_time': time.time(),
            'peak_cpu': 0.0,
            'peak_memory': 0.0,
            'sample_count': 0
        }
        self.last_log_time = 0
        
    def start_monitoring(self, log_callback=None):
        """开始性能监控"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.stats['start_time'] = time.time()
        
        def monitor_loop():
            while self.monitoring:
                try:
                    # 获取CPU使用率
                    cpu_percent = self.process.cpu_percent()
                    
                    # 获取内存使用情况
                    memory_info = self.process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB
                    
                    # 更新统计
                    self.stats['cpu_percent'] = cpu_percent
                    self.stats['memory_mb'] = memory_mb
                    self.stats['peak_cpu'] = max(self.stats['peak_cpu'], cpu_percent)
                    self.stats['peak_memory'] = max(self.stats['peak_memory'], memory_mb)
                    self.stats['sample_count'] += 1
                    
                    # 每30秒记录一次性能日志
                    current_time = time.time()
                    if log_callback and (current_time - self.last_log_time) >= 30:
                        avg_cpu = self.get_average_cpu()
                        log_callback(
                            f"[性能] CPU: {cpu_percent:.1f}% (峰值: {self.stats['peak_cpu']:.1f}%) "
                            f"内存: {memory_mb:.1f}MB (峰值: {self.stats['peak_memory']:.1f}MB)",
                            "DEBUG"
                        )
                        self.last_log_time = current_time
                    
                    time.sleep(5)  # 每5秒采样一次
                    
                except Exception as e:
                    if log_callback:
                        log_callback(f"性能监控出错: {e}", "ERROR")
                    time.sleep(10)
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        if log_callback:
            log_callback("性能监控已启动", "INFO")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
    
    def get_current_stats(self):
        """获取当前性能统计"""
        runtime = int(time.time() - self.stats['start_time'])
        return {
            'cpu_percent': self.stats['cpu_percent'],
            'memory_mb': self.stats['memory_mb'],
            'peak_cpu': self.stats['peak_cpu'],
            'peak_memory': self.stats['peak_memory'],
            'runtime_seconds': runtime,
            'sample_count': self.stats['sample_count']
        }
    
    def get_average_cpu(self):
        """获取平均CPU使用率（简单估算）"""
        if self.stats['sample_count'] > 0:
            return self.stats['peak_cpu'] * 0.6  # 简单估算
        return 0.0
    
    def get_performance_summary(self):
        """获取性能摘要"""
        stats = self.get_current_stats()
        runtime_min = stats['runtime_seconds'] // 60
        
        return (
            f"运行时间: {runtime_min}分钟 | "
            f"当前CPU: {stats['cpu_percent']:.1f}% | "
            f"当前内存: {stats['memory_mb']:.1f}MB | "
            f"峰值CPU: {stats['peak_cpu']:.1f}% | "
            f"峰值内存: {stats['peak_memory']:.1f}MB"
        )

# 全局性能监控实例
_performance_monitor = None

def get_performance_monitor():
    """获取全局性能监控实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def start_performance_monitoring(log_callback=None):
    """启动全局性能监控"""
    monitor = get_performance_monitor()
    monitor.start_monitoring(log_callback)
    return monitor

def get_performance_stats():
    """获取当前性能统计"""
    monitor = get_performance_monitor()
    return monitor.get_current_stats()

def get_performance_summary():
    """获取性能摘要"""
    monitor = get_performance_monitor()
    return monitor.get_performance_summary()

if __name__ == "__main__":
    # 测试性能监控
    def test_log(message, level):
        logger.debug(f"[{level}] {message}")
    
    logger.info("开始性能监控测试...")
    monitor = start_performance_monitoring(test_log)
    
    try:
        # 运行30秒测试
        for i in range(6):
            time.sleep(5)
            stats = get_performance_stats()
            logger.debug(f"第{i+1}次采样: CPU {stats['cpu_percent']:.1f}% 内存 {stats['memory_mb']:.1f}MB")
        
        logger.info("\n性能摘要:")
        logger.info(get_performance_summary())
        
    except KeyboardInterrupt:
        logger.info("\n测试结束")
    finally:
        monitor.stop_monitoring()