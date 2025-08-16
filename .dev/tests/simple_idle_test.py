#!/usr/bin/env python3
"""
简单的空闲时间API性能测试
"""
import time
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.idle_detector import IdleDetector

def simple_performance_test():
    """简单的性能测试"""
    print("创建IdleDetector...")
    detector = IdleDetector()
    
    print("测试单次调用时间...")
    
    # 测试10次单次调用
    for i in range(10):
        start = time.perf_counter()
        idle_time = detector.get_idle_time_seconds()
        end = time.perf_counter()
        duration_ms = (end - start) * 1000
        print(f"第{i+1}次: {duration_ms:.3f}ms (空闲: {idle_time:.1f}s)")
        
        # 避免太快，让系统有时间处理
        time.sleep(0.1)
    
    print("测试完成!")

if __name__ == "__main__":
    simple_performance_test()