#!/usr/bin/env python3
"""
状态检查性能测试脚本
测试优化前后的性能差异
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

def test_status_check_performance():
    """测试状态检查性能"""
    print("=== 状态检查性能测试 ===\n")
    
    try:
        from core.wechat_controller import is_wechat_running, find_wechat_processes
        from core.onedrive_controller import is_onedrive_running, find_onedrive_processes
        
        print("测试微信状态检查性能...")
        
        # 测试微信状态检查（多次测试取平均值）
        wechat_times = []
        for i in range(3):
            start_time = time.time()
            result = is_wechat_running()
            duration = (time.time() - start_time) * 1000
            wechat_times.append(duration)
            print(f"  第{i+1}次微信状态检查: {duration:.1f}ms (结果: {'运行中' if result else '未运行'})")
        
        avg_wechat_time = sum(wechat_times) / len(wechat_times)
        print(f"  微信状态检查平均耗时: {avg_wechat_time:.1f}ms")
        
        print("\n测试OneDrive状态检查性能...")
        
        # 测试OneDrive状态检查（多次测试取平均值）
        onedrive_times = []
        for i in range(3):
            start_time = time.time()
            result = is_onedrive_running()
            duration = (time.time() - start_time) * 1000
            onedrive_times.append(duration)
            print(f"  第{i+1}次OneDrive状态检查: {duration:.1f}ms (结果: {'运行中' if result else '未运行'})")
        
        avg_onedrive_time = sum(onedrive_times) / len(onedrive_times)
        print(f"  OneDrive状态检查平均耗时: {avg_onedrive_time:.1f}ms")
        
        print("\n=== 性能分析 ===")
        total_avg_time = avg_wechat_time + avg_onedrive_time
        print(f"总平均耗时: {total_avg_time:.1f}ms")
        
        # 与日志中的历史数据对比
        historical_wechat = 4783.5  # 从日志中获取的历史数据
        historical_onedrive = 4607.6
        historical_total = historical_wechat + historical_onedrive
        
        print(f"\n=== 优化效果对比 ===")
        print(f"优化前 (历史数据):")
        print(f"  微信状态检查: {historical_wechat}ms")
        print(f"  OneDrive状态检查: {historical_onedrive}ms")  
        print(f"  总耗时: {historical_total}ms")
        
        print(f"\n优化后 (当前测试):")
        print(f"  微信状态检查: {avg_wechat_time:.1f}ms")
        print(f"  OneDrive状态检查: {avg_onedrive_time:.1f}ms")
        print(f"  总耗时: {total_avg_time:.1f}ms")
        
        # 计算性能提升
        if total_avg_time < historical_total:
            improvement_ratio = (historical_total - total_avg_time) / historical_total * 100
            speed_up = historical_total / total_avg_time
            print(f"\n性能提升效果:")
            print(f"  耗时减少: {improvement_ratio:.1f}%")
            print(f"  速度提升: {speed_up:.1f}倍")
            print(f"  响应时间从 {historical_total/1000:.1f}秒 优化到 {total_avg_time/1000:.2f}秒")
            
            if improvement_ratio > 80:
                print("  结果: 优化效果显著! 用户体验大幅提升")
            elif improvement_ratio > 50:
                print("  结果: 优化效果良好! 明显改善响应速度")
            else:
                print("  结果: 优化效果一般，仍有进一步优化空间")
        else:
            print(f"\n注意: 当前测试耗时 ({total_avg_time:.1f}ms) 与历史数据差异较大")
            print("可能原因: 系统状态不同、进程数量变化等")
        
        print(f"\n=== 进程查找详情 ===")
        
        # 测试进程查找详细信息
        start_time = time.time()
        wechat_procs = find_wechat_processes()
        wechat_find_time = (time.time() - start_time) * 1000
        
        start_time = time.time()  
        onedrive_procs = find_onedrive_processes()
        onedrive_find_time = (time.time() - start_time) * 1000
        
        print(f"微信进程查找: {wechat_find_time:.1f}ms (找到 {len(wechat_procs)} 个进程)")
        print(f"OneDrive进程查找: {onedrive_find_time:.1f}ms (找到 {len(onedrive_procs)} 个进程)")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_status_check_performance()