#!/usr/bin/env python3
"""
性能监控脚本 - 监控主程序的CPU和内存使用
"""
import psutil
import time
import sys
import os
from datetime import datetime

def find_main_program_processes():
    """查找主程序相关的Python进程"""
    target_processes = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
        try:
            if proc.info['name'] in ['python.exe', 'python3.13.exe']:
                cmdline = proc.info['cmdline']
                if cmdline and len(cmdline) > 1:
                    script_path = cmdline[1]
                    # 检查是否是我们的主程序
                    if 'gui_app.py' in script_path or current_dir in script_path:
                        target_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return target_processes

def monitor_performance(duration_minutes=5):
    """监控程序性能"""
    print(f"开始性能监控 - 监控时长: {duration_minutes}分钟")
    print("正在查找主程序进程...")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    cpu_samples = []
    memory_samples = []
    sample_count = 0
    
    print(f"监控开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    print(f"{'时间':<8} {'PID':<8} {'CPU%':<8} {'内存MB':<10} {'累计平均CPU%':<12} {'累计平均内存MB':<15}")
    print("=" * 60)
    
    while time.time() < end_time:
        try:
            # 查找目标进程
            processes = find_main_program_processes()
            
            if not processes:
                print(f"{datetime.now().strftime('%H:%M:%S'):<8} 未找到主程序进程，等待启动...")
                time.sleep(2)
                continue
            
            total_cpu = 0
            total_memory = 0
            
            for proc in processes:
                try:
                    # 获取CPU和内存使用率
                    cpu_percent = proc.cpu_percent()
                    memory_mb = proc.memory_info().rss / 1024 / 1024  # 转换为MB
                    
                    total_cpu += cpu_percent
                    total_memory += memory_mb
                    
                    # 记录样本
                    cpu_samples.append(cpu_percent)
                    memory_samples.append(memory_mb)
                    
                    sample_count += 1
                    
                    # 计算累计平均值
                    avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
                    avg_memory = sum(memory_samples) / len(memory_samples) if memory_samples else 0
                    
                    # 实时显示
                    current_time = datetime.now().strftime('%H:%M:%S')
                    print(f"{current_time:<8} {proc.pid:<8} {cpu_percent:<8.1f} {memory_mb:<10.1f} {avg_cpu:<12.1f} {avg_memory:<15.1f}")
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            time.sleep(2)  # 每2秒采样一次
            
        except KeyboardInterrupt:
            print("\n监控被用户中断")
            break
        except Exception as e:
            print(f"监控过程中出错: {e}")
            time.sleep(2)
    
    # 生成监控报告
    print("\n" + "=" * 60)
    print("性能监控报告")
    print("=" * 60)
    
    if cpu_samples and memory_samples:
        avg_cpu = sum(cpu_samples) / len(cpu_samples)
        max_cpu = max(cpu_samples)
        min_cpu = min(cpu_samples)
        
        avg_memory = sum(memory_samples) / len(memory_samples)
        max_memory = max(memory_samples)
        min_memory = min(memory_samples)
        
        print(f"监控时长: {(time.time() - start_time)/60:.1f} 分钟")
        print(f"采样次数: {len(cpu_samples)}")
        print()
        print("CPU使用率:")
        print(f"  平均: {avg_cpu:.2f}%")
        print(f"  最高: {max_cpu:.2f}%")
        print(f"  最低: {min_cpu:.2f}%")
        print()
        print("内存使用:")
        print(f"  平均: {avg_memory:.1f} MB")
        print(f"  最高: {max_memory:.1f} MB")
        print(f"  最低: {min_memory:.1f} MB")
        print()
        
        # 性能评估
        print("性能评估:")
        if avg_cpu < 1.0:
            print(f"  ✅ CPU使用率很低 ({avg_cpu:.2f}%)")
        elif avg_cpu < 3.0:
            print(f"  ✅ CPU使用率正常 ({avg_cpu:.2f}%)")
        elif avg_cpu < 5.0:
            print(f"  ⚠️  CPU使用率稍高 ({avg_cpu:.2f}%)")
        else:
            print(f"  ❌ CPU使用率过高 ({avg_cpu:.2f}%)")
        
        if avg_memory < 50:
            print(f"  ✅ 内存使用很低 ({avg_memory:.1f} MB)")
        elif avg_memory < 100:
            print(f"  ✅ 内存使用正常 ({avg_memory:.1f} MB)")
        elif avg_memory < 200:
            print(f"  ⚠️  内存使用稍高 ({avg_memory:.1f} MB)")
        else:
            print(f"  ❌ 内存使用过高 ({avg_memory:.1f} MB)")
    else:
        print("未收集到有效的性能数据")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        try:
            duration = float(sys.argv[1])
        except ValueError:
            print("请提供有效的监控时长（分钟）")
            return
    else:
        duration = 5  # 默认5分钟
    
    print("=== 程序性能监控工具 ===")
    print(f"将监控主程序 {duration} 分钟")
    print("请在另一个终端启动主程序: python gui_app.py")
    print("按 Ctrl+C 可随时停止监控")
    print()
    
    try:
        monitor_performance(duration)
    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == "__main__":
    main()