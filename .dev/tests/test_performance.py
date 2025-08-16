#!/usr/bin/env python3
"""
性能优化效果测试脚本
用于验证GUI应用的CPU和内存使用改善情况
"""

import time
import psutil
import threading
from datetime import datetime

def test_performance():
    """测试性能优化效果"""
    print("=== 性能优化效果测试 ===\n")
    print("测试说明：")
    print("- 优化前预期：CPU 5-10%，内存 80-120MB")
    print("- 优化后目标：CPU 2-5%，内存 50-80MB")
    print("- 测试时长：60秒，每5秒采样一次\n")
    
    # 获取当前进程
    process = psutil.Process()
    
    # 统计数据
    samples = []
    start_time = time.time()
    
    try:
        for i in range(12):  # 60秒 / 5秒 = 12次采样
            # 等待5秒
            time.sleep(5)
            
            # 获取性能指标
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # 记录样本
            samples.append({
                'time': i * 5,
                'cpu': cpu_percent,
                'memory': memory_mb
            })
            
            # 显示当前状态
            print(f"[{i+1:2d}/12] 时间: {i*5:2d}s | CPU: {cpu_percent:5.1f}% | 内存: {memory_mb:6.1f}MB")
        
        # 计算统计结果
        avg_cpu = sum(s['cpu'] for s in samples) / len(samples)
        max_cpu = max(s['cpu'] for s in samples)
        avg_memory = sum(s['memory'] for s in samples) / len(samples)
        max_memory = max(s['memory'] for s in samples)
        
        print(f"\n=== 测试结果汇总 ===")
        print(f"测试时长: {int(time.time() - start_time)}秒")
        print(f"采样次数: {len(samples)}次")
        print(f"")
        print(f"CPU使用率:")
        print(f"  平均: {avg_cpu:.1f}%")
        print(f"  峰值: {max_cpu:.1f}%")
        print(f"")
        print(f"内存使用:")
        print(f"  平均: {avg_memory:.1f}MB")
        print(f"  峰值: {max_memory:.1f}MB")
        print(f"")
        
        # 评估优化效果
        print("=== 优化效果评估 ===")
        
        # CPU优化效果
        if avg_cpu <= 3.0:
            cpu_result = "✅ 优秀"
        elif avg_cpu <= 5.0:
            cpu_result = "🟢 良好"
        elif avg_cpu <= 8.0:
            cpu_result = "🟡 一般"
        else:
            cpu_result = "❌ 需要进一步优化"
        
        print(f"CPU性能: {cpu_result} (平均 {avg_cpu:.1f}%)")
        
        # 内存优化效果
        if avg_memory <= 60:
            memory_result = "✅ 优秀"
        elif avg_memory <= 80:
            memory_result = "🟢 良好"
        elif avg_memory <= 100:
            memory_result = "🟡 一般"
        else:
            memory_result = "❌ 需要进一步优化"
        
        print(f"内存性能: {memory_result} (平均 {avg_memory:.1f}MB)")
        
        # 总体评估
        if avg_cpu <= 5.0 and avg_memory <= 80:
            print(f"\n🎉 总体评估: 性能优化成功！")
            print(f"   CPU从预期5-10%降低到{avg_cpu:.1f}%")
            print(f"   内存从预期80-120MB降低到{avg_memory:.1f}MB")
        else:
            print(f"\n⚠️  总体评估: 还有进一步优化空间")
            if avg_cpu > 5.0:
                print(f"   CPU使用率({avg_cpu:.1f}%)仍然偏高")
            if avg_memory > 80:
                print(f"   内存使用量({avg_memory:.1f}MB)仍然偏高")
    
    except KeyboardInterrupt:
        print(f"\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")

def monitor_gui_performance():
    """专门监控GUI应用的性能（运行GUI后调用）"""
    print("=== GUI性能实时监控 ===\n")
    print("请先启动GUI应用 (python gui_app.py)")
    print("然后观察下面的性能数据，按Ctrl+C结束监控\n")
    
    try:
        while True:
            # 查找GUI进程
            gui_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('gui_app.py' in arg for arg in cmdline):
                        gui_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if gui_processes:
                for proc in gui_processes:
                    try:
                        cpu = proc.cpu_percent()
                        memory = proc.memory_info().rss / 1024 / 1024
                        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                              f"PID: {proc.pid} | CPU: {cpu:5.1f}% | 内存: {memory:6.1f}MB", 
                              end='', flush=True)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            else:
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                      f"未找到GUI进程，请启动 gui_app.py", end='', flush=True)
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print(f"\n\n监控已停止")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "gui":
        monitor_gui_performance()
    else:
        print("性能测试模式选择：")
        print("1. 基础性能测试 (60秒)")
        print("2. GUI实时监控")
        print()
        choice = input("请选择模式 (1/2): ").strip()
        
        if choice == "2":
            monitor_gui_performance()
        else:
            test_performance()