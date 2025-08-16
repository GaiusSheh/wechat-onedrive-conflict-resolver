#!/usr/bin/env python3
"""
测试系统空闲时间API的性能
"""
import time
import sys
import os

# 添加路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.idle_detector import IdleDetector

def test_idle_api_performance():
    """测试空闲时间API的性能"""
    print("开始测试系统空闲时间API性能...")
    
    # 创建检测器
    detector = IdleDetector()
    
    # 预热调用（第一次可能较慢）
    print("预热调用...")
    detector.get_idle_time_seconds()
    
    # 测试单次调用时间
    print("\n=== 单次调用测试 ===")
    times = []
    for i in range(10):
        start_time = time.perf_counter()
        idle_time = detector.get_idle_time_seconds()
        end_time = time.perf_counter() 
        duration = (end_time - start_time) * 1000  # 转换为毫秒
        times.append(duration)
        print(f"第{i+1}次: {duration:.3f}ms (空闲时间: {idle_time:.1f}s)")
    
    print(f"\n单次调用统计:")
    print(f"  平均时间: {sum(times)/len(times):.3f}ms")
    print(f"  最快时间: {min(times):.3f}ms")
    print(f"  最慢时间: {max(times):.3f}ms")
    
    # 测试连续快速调用
    print("\n=== 连续快速调用测试 ===")
    start_time = time.perf_counter()
    for i in range(100):
        detector.get_idle_time_seconds()
    end_time = time.perf_counter()
    total_time = (end_time - start_time) * 1000
    avg_time = total_time / 100
    
    print(f"100次连续调用:")
    print(f"  总时间: {total_time:.3f}ms")
    print(f"  平均每次: {avg_time:.3f}ms")
    print(f"  每秒可调用: {1000/avg_time:.0f}次")
    
    # 测试不同频率调用的影响
    print("\n=== 不同调用频率测试 ===")
    frequencies = [0.1, 0.5, 1.0, 2.0, 3.0]  # 秒
    
    for freq in frequencies:
        print(f"\n每{freq}秒调用一次（测试10次）:")
        times = []
        for i in range(10):
            start_time = time.perf_counter()
            idle_time = detector.get_idle_time_seconds()
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000
            times.append(duration)
            
            if i < 9:  # 最后一次不需要等待
                time.sleep(freq)
        
        avg_time = sum(times) / len(times)
        print(f"  平均调用时间: {avg_time:.3f}ms")
        print(f"  相对于调用间隔的占比: {(avg_time/1000)/freq*100:.2f}%")

if __name__ == "__main__":
    test_idle_api_performance()