#!/usr/bin/env python3
"""
缓存策略性能测试脚本
验证5秒缓存机制的性能提升效果
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

def test_cache_performance():
    """测试缓存性能"""
    try:
        from core.wechat_controller import is_wechat_running, clear_wechat_status_cache
        from core.onedrive_controller import is_onedrive_running, clear_onedrive_status_cache
        from core.logger_helper import logger
        
        logger.debug("=== 缓存策略性能测试 ===")
        logger.debug("测试场景：模拟GUI频繁状态检查")
        logger.debug("期望效果：第一次慢（实际查询），后续快（缓存）")
        
        # 清理所有缓存，确保测试的准确性
        clear_wechat_status_cache()
        clear_onedrive_status_cache()
        
        logger.debug("=== 微信状态检查测试 ===")
        
        # 第一次检查（应该慢，需要实际查询）
        start_time = time.time()
        wechat_result1 = is_wechat_running()
        duration1 = (time.time() - start_time) * 1000
        logger.info(f"微信状态检查第1次 (实际查询): {duration1:.1f}ms (结果: {'运行中' if wechat_result1 else '未运行'})")
        
        # 第二次检查（应该快，使用缓存）
        start_time = time.time()
        wechat_result2 = is_wechat_running()
        duration2 = (time.time() - start_time) * 1000
        logger.info(f"微信状态检查第2次 (缓存结果): {duration2:.1f}ms (结果: {'运行中' if wechat_result2 else '未运行'})")
        
        # 第三次检查（应该快，使用缓存）
        start_time = time.time()
        wechat_result3 = is_wechat_running()
        duration3 = (time.time() - start_time) * 1000
        logger.info(f"微信状态检查第3次 (缓存结果): {duration3:.1f}ms (结果: {'运行中' if wechat_result3 else '未运行'})")
        
        # 等待缓存过期后再测试
        logger.debug("等待6秒，让缓存过期...")
        time.sleep(6)
        
        # 缓存过期后的检查（应该又变慢）
        start_time = time.time()
        wechat_result4 = is_wechat_running()
        duration4 = (time.time() - start_time) * 1000
        logger.info(f"微信状态检查第4次 (缓存过期): {duration4:.1f}ms (结果: {'运行中' if wechat_result4 else '未运行'})")
        
        print(f"\n=== OneDrive状态检查测试 ===")
        
        # 重复OneDrive的测试
        start_time = time.time()
        od_result1 = is_onedrive_running()
        od_duration1 = (time.time() - start_time) * 1000
        print(f"第1次检查 (实际查询): {od_duration1:.1f}ms (结果: {'运行中' if od_result1 else '未运行'})")
        
        start_time = time.time()
        od_result2 = is_onedrive_running()
        od_duration2 = (time.time() - start_time) * 1000
        print(f"第2次检查 (缓存结果): {od_duration2:.1f}ms (结果: {'运行中' if od_result2 else '未运行'})")
        
        start_time = time.time()
        od_result3 = is_onedrive_running()
        od_duration3 = (time.time() - start_time) * 1000
        print(f"第3次检查 (缓存结果): {od_duration3:.1f}ms (结果: {'运行中' if od_result3 else '未运行'})")
        
        print(f"\n=== 性能分析 ===")
        
        # 缓存命中的平均性能
        wechat_cache_avg = (duration2 + duration3) / 2
        od_cache_avg = (od_duration2 + od_duration3) / 2
        total_cache_avg = wechat_cache_avg + od_cache_avg
        
        print(f"实际查询耗时:")
        print(f"  微信: {duration1:.1f}ms")
        print(f"  OneDrive: {od_duration1:.1f}ms")
        print(f"  总计: {duration1 + od_duration1:.1f}ms")
        
        print(f"\n缓存命中耗时:")
        print(f"  微信平均: {wechat_cache_avg:.1f}ms")
        print(f"  OneDrive平均: {od_cache_avg:.1f}ms")
        print(f"  总计平均: {total_cache_avg:.1f}ms")
        
        # 计算性能提升
        if total_cache_avg < (duration1 + od_duration1):
            improvement_ratio = ((duration1 + od_duration1) - total_cache_avg) / (duration1 + od_duration1) * 100
            speed_up = (duration1 + od_duration1) / total_cache_avg
            
            print(f"\n🎯 缓存优化效果:")
            print(f"  响应时间提升: {improvement_ratio:.1f}%")
            print(f"  速度提升: {speed_up:.1f}倍")
            print(f"  从 {(duration1 + od_duration1)/1000:.2f}秒 → {total_cache_avg/1000:.3f}秒")
            
            if improvement_ratio > 90:
                print("  ✅ 优化效果极佳！GUI响应接近瞬时")
            elif improvement_ratio > 70:
                print("  ✅ 优化效果很好！明显提升用户体验")
            else:
                print("  ⚠️  优化效果一般，可能需要调整缓存时间")
        
        print(f"\n=== 模拟GUI使用场景 ===")
        
        # 模拟用户快速点击多次的场景
        print("模拟用户连续点击5次状态检查按钮...")
        
        clear_wechat_status_cache()
        clear_onedrive_status_cache()
        
        total_time = 0
        for i in range(5):
            start_time = time.time()
            wechat_status = is_wechat_running()
            onedrive_status = is_onedrive_running()
            click_duration = (time.time() - start_time) * 1000
            total_time += click_duration
            
            print(f"  第{i+1}次点击: {click_duration:.1f}ms")
            
            # 短暂延迟模拟用户操作间隔
            time.sleep(0.2)
        
        avg_click_time = total_time / 5
        print(f"\n平均每次点击响应时间: {avg_click_time:.1f}ms")
        print(f"总计5次点击耗时: {total_time:.1f}ms")
        
        # 与历史数据对比
        historical_single_check = 9391.1  # 从日志获取的历史数据
        historical_5_clicks = historical_single_check * 5
        
        print(f"\n📊 与优化前对比:")
        print(f"优化前5次点击预计耗时: {historical_5_clicks/1000:.1f}秒")
        print(f"优化后5次点击实际耗时: {total_time/1000:.2f}秒")
        
        if total_time < historical_5_clicks:
            overall_improvement = (historical_5_clicks - total_time) / historical_5_clicks * 100
            print(f"整体性能提升: {overall_improvement:.1f}%")
            print(f"用户等待时间减少: {(historical_5_clicks - total_time)/1000:.1f}秒")
            
            if overall_improvement > 95:
                print("🏆 缓存策略大获成功！用户体验极大提升！")
            elif overall_improvement > 80:
                print("🎉 缓存策略效果显著！用户体验明显改善！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cache_performance()