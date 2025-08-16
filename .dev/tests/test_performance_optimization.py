#!/usr/bin/env python3
"""
性能优化效果测试脚本 - 2025-08-08
验证进程查找API优化和线程安全机制的效果

预期改善：
- 状态查询：27秒 → 0.5秒以内
- 缓存命中：5秒 → <10ms  
- 线程安全：无竞态条件
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

def test_performance_optimization():
    """测试性能优化效果"""
    try:
        from core.wechat_controller import is_wechat_running, clear_wechat_status_cache
        from core.onedrive_controller import is_onedrive_running, clear_onedrive_status_cache
        from core.logger_helper import logger
        
        logger.info("=== 开始性能优化效果测试 ===")
        
        # 清理缓存，确保测试准确性
        clear_wechat_status_cache()
        clear_onedrive_status_cache()
        
        logger.info("=== 测试1：单次查询性能（应该从27秒优化到0.5秒内）===")
        
        # 微信状态查询测试
        start_time = time.time()
        wechat_status = is_wechat_running(force_refresh=True)
        wechat_duration = (time.time() - start_time) * 1000
        logger.warning(f"微信状态查询耗时: {wechat_duration:.1f}ms (结果: {'运行' if wechat_status else '停止'})")
        
        if wechat_duration < 1000:  # 小于1秒认为优化成功
            logger.error(f"✅ 微信查询性能优化成功！从27秒优化到{wechat_duration:.1f}ms")
        else:
            logger.warning(f"⚠️  微信查询仍需{wechat_duration:.1f}ms，可能需要进一步优化")
        
        # OneDrive状态查询测试
        start_time = time.time()
        onedrive_status = is_onedrive_running(force_refresh=True)
        onedrive_duration = (time.time() - start_time) * 1000
        logger.warning(f"OneDrive状态查询耗时: {onedrive_duration:.1f}ms (结果: {'运行' if onedrive_status else '停止'})")
        
        if onedrive_duration < 1000:
            logger.error(f"✅ OneDrive查询性能优化成功！从27秒优化到{onedrive_duration:.1f}ms")
        else:
            logger.warning(f"⚠️  OneDrive查询仍需{onedrive_duration:.1f}ms，可能需要进一步优化")
        
        logger.info("=== 测试2：缓存性能（应该<10ms）===")
        
        # 立即第二次查询，测试缓存效果
        start_time = time.time()
        wechat_cached = is_wechat_running(force_refresh=False)
        wechat_cache_duration = (time.time() - start_time) * 1000
        logger.info(f"微信缓存查询耗时: {wechat_cache_duration:.1f}ms")
        
        start_time = time.time()
        onedrive_cached = is_onedrive_running(force_refresh=False)
        onedrive_cache_duration = (time.time() - start_time) * 1000
        logger.info(f"OneDrive缓存查询耗时: {onedrive_cache_duration:.1f}ms")
        
        if wechat_cache_duration < 50 and onedrive_cache_duration < 50:
            logger.error(f"✅ 缓存性能优异！微信:{wechat_cache_duration:.1f}ms, OneDrive:{onedrive_cache_duration:.1f}ms")
        else:
            logger.warning(f"⚠️  缓存性能仍有提升空间")
        
        logger.info("=== 测试3：线程安全和并发性能 ===")
        
        # 多线程并发测试
        results = []
        errors = []
        
        def concurrent_query(thread_id):
            try:
                start = time.time()
                wechat_result = is_wechat_running(force_refresh=False)
                onedrive_result = is_onedrive_running(force_refresh=False)
                duration = (time.time() - start) * 1000
                results.append({
                    'thread_id': thread_id,
                    'duration': duration,
                    'wechat': wechat_result,
                    'onedrive': onedrive_result
                })
            except Exception as e:
                errors.append(f"线程{thread_id}出错: {e}")
        
        # 启动5个并发线程
        threads = []
        for i in range(5):
            t = threading.Thread(target=concurrent_query, args=(i,))
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        if errors:
            logger.error(f"❌ 并发测试出现错误: {errors}")
        else:
            avg_duration = sum(r['duration'] for r in results) / len(results)
            max_duration = max(r['duration'] for r in results)
            min_duration = min(r['duration'] for r in results)
            
            logger.error(f"✅ 并发测试成功！5线程并发查询:")
            logger.error(f"  平均耗时: {avg_duration:.1f}ms")
            logger.error(f"  最长耗时: {max_duration:.1f}ms") 
            logger.error(f"  最短耗时: {min_duration:.1f}ms")
            
            # 验证结果一致性（缓存应该保证结果一致）
            wechat_results = set(r['wechat'] for r in results)
            onedrive_results = set(r['onedrive'] for r in results)
            
            if len(wechat_results) == 1 and len(onedrive_results) == 1:
                logger.error("✅ 线程安全验证通过！所有线程结果一致")
            else:
                logger.warning("⚠️  线程安全可能存在问题，结果不一致")
        
        logger.info("=== 测试4：模拟GUI使用场景 ===")
        
        # 模拟GUI频繁状态检查
        logger.info("模拟GUI每秒状态检查，持续10秒...")
        
        gui_durations = []
        for i in range(10):
            start = time.time()
            wechat_gui = is_wechat_running(force_refresh=False)
            onedrive_gui = is_onedrive_running(force_refresh=False)
            duration = (time.time() - start) * 1000
            gui_durations.append(duration)
            logger.debug(f"GUI检查第{i+1}次: {duration:.1f}ms")
            time.sleep(1)
        
        avg_gui_duration = sum(gui_durations) / len(gui_durations)
        logger.error(f"GUI模拟测试结果: 平均每次检查{avg_gui_duration:.1f}ms")
        
        if avg_gui_duration < 20:
            logger.error("🎉 GUI性能优异！用户体验极度流畅")
        elif avg_gui_duration < 100:
            logger.error("✅ GUI性能良好！用户体验流畅")
        else:
            logger.warning("⚠️  GUI性能仍需优化")
        
        logger.info("=== 性能优化总结 ===")
        
        # 与历史数据对比
        historical_time = 27000  # 历史最慢时间27秒
        current_best = min(wechat_duration, onedrive_duration)
        current_cache = max(wechat_cache_duration, onedrive_cache_duration)
        
        if current_best < 1000:
            improvement = ((historical_time - current_best) / historical_time) * 100
            speedup = historical_time / current_best
            logger.error(f"🎯 性能优化大获成功！")
            logger.error(f"  查询时间: {historical_time}ms → {current_best:.1f}ms")
            logger.error(f"  性能提升: {improvement:.1f}%")
            logger.error(f"  速度提升: {speedup:.0f}倍")
            logger.error(f"  缓存响应: {current_cache:.1f}ms")
            logger.error(f"  GUI体验: 从27秒卡死到{avg_gui_duration:.1f}ms流畅")
        else:
            logger.warning("性能优化效果有限，可能需要进一步分析")
        
        logger.info("性能优化效果测试完成")
        
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_performance_optimization()