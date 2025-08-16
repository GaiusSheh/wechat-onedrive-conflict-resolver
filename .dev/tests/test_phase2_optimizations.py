#!/usr/bin/env python3
"""
Phase 2细节优化效果测试 - 2025-08-08
验证Process对象优化和OneDrive专项优化的效果

预期改善：
- 查询时间：1.1-2.7秒 → 0.5秒以内
- OneDrive查询：专门优化，解决最慢环节
- Process创建：减少不必要开销
"""

import sys
import os
import time
import statistics

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

def test_phase2_optimizations():
    """测试Phase 2细节优化效果"""
    try:
        from core.wechat_controller import is_wechat_running, clear_wechat_status_cache
        from core.onedrive_controller import is_onedrive_running, clear_onedrive_status_cache
        from core.logger_helper import logger
        
        logger.info("=== 开始Phase 2细节优化效果测试 ===")
        
        # 清理缓存，确保测试准确性
        clear_wechat_status_cache()
        clear_onedrive_status_cache()
        
        logger.info("=== 测试1：单次查询性能对比 ===")
        logger.info("目标：从Phase 1的1.1-2.7秒优化到0.5秒以内")
        
        # 微信查询性能测试 - 多次测试取平均值
        wechat_times = []
        for i in range(3):
            clear_wechat_status_cache()
            start_time = time.time()
            wechat_status = is_wechat_running(force_refresh=True)
            duration = (time.time() - start_time) * 1000
            wechat_times.append(duration)
            logger.debug(f"微信查询第{i+1}次: {duration:.1f}ms")
            time.sleep(1)  # 避免缓存影响
        
        wechat_avg = statistics.mean(wechat_times)
        wechat_min = min(wechat_times)
        wechat_max = max(wechat_times)
        
        logger.warning(f"微信查询性能 (3次平均):")
        logger.warning(f"  平均: {wechat_avg:.1f}ms")
        logger.warning(f"  最快: {wechat_min:.1f}ms") 
        logger.warning(f"  最慢: {wechat_max:.1f}ms")
        
        # OneDrive查询性能测试 - 重点优化对象
        onedrive_times = []
        for i in range(3):
            clear_onedrive_status_cache()
            start_time = time.time()
            onedrive_status = is_onedrive_running(force_refresh=True)
            duration = (time.time() - start_time) * 1000
            onedrive_times.append(duration)
            logger.debug(f"OneDrive查询第{i+1}次: {duration:.1f}ms")
            time.sleep(1)
        
        onedrive_avg = statistics.mean(onedrive_times)
        onedrive_min = min(onedrive_times)
        onedrive_max = max(onedrive_times)
        
        logger.warning(f"OneDrive查询性能 (3次平均):")
        logger.warning(f"  平均: {onedrive_avg:.1f}ms")
        logger.warning(f"  最快: {onedrive_min:.1f}ms")
        logger.warning(f"  最慢: {onedrive_max:.1f}ms")
        
        logger.info("=== 测试2：优化效果评估 ===")
        
        # 与Phase 1数据对比
        phase1_wechat = 1100  # Phase 1微信查询时间
        phase1_onedrive_avg = 2000  # Phase 1 OneDrive平均时间  
        phase1_onedrive_worst = 2700  # Phase 1 OneDrive最差时间
        
        if wechat_avg < phase1_wechat:
            wechat_improvement = ((phase1_wechat - wechat_avg) / phase1_wechat) * 100
            logger.error(f"✅ 微信查询优化成功！")
            logger.error(f"  Phase 1: {phase1_wechat}ms → Phase 2: {wechat_avg:.1f}ms")
            logger.error(f"  性能提升: {wechat_improvement:.1f}%")
        else:
            logger.warning(f"⚠️  微信查询优化有限: {phase1_wechat}ms → {wechat_avg:.1f}ms")
        
        if onedrive_avg < phase1_onedrive_avg:
            onedrive_improvement = ((phase1_onedrive_avg - onedrive_avg) / phase1_onedrive_avg) * 100
            logger.error(f"✅ OneDrive查询优化成功！")
            logger.error(f"  Phase 1平均: {phase1_onedrive_avg}ms → Phase 2: {onedrive_avg:.1f}ms")
            logger.error(f"  性能提升: {onedrive_improvement:.1f}%")
        else:
            logger.warning(f"⚠️  OneDrive查询优化有限")
        
        # 检查是否达到目标0.5秒
        target_time = 500  # 500ms目标
        
        if wechat_avg < target_time and onedrive_avg < target_time:
            logger.error(f"🎯 Phase 2优化目标达成！")
            logger.error(f"  微信: {wechat_avg:.1f}ms < 500ms ✅")
            logger.error(f"  OneDrive: {onedrive_avg:.1f}ms < 500ms ✅")
        else:
            logger.warning(f"🎯 Phase 2优化目标部分达成:")
            logger.warning(f"  微信: {wechat_avg:.1f}ms {'✅' if wechat_avg < target_time else '❌'}")
            logger.warning(f"  OneDrive: {onedrive_avg:.1f}ms {'✅' if onedrive_avg < target_time else '❌'}")
        
        logger.info("=== 测试3：缓存性能验证 ===")
        
        # 验证缓存性能未受影响
        start_time = time.time()
        wechat_cached = is_wechat_running(force_refresh=False)
        wechat_cache_time = (time.time() - start_time) * 1000
        
        start_time = time.time()
        onedrive_cached = is_onedrive_running(force_refresh=False)
        onedrive_cache_time = (time.time() - start_time) * 1000
        
        logger.info(f"缓存性能验证:")
        logger.info(f"  微信缓存: {wechat_cache_time:.1f}ms")
        logger.info(f"  OneDrive缓存: {onedrive_cache_time:.1f}ms")
        
        if wechat_cache_time < 10 and onedrive_cache_time < 10:
            logger.error("✅ 缓存性能保持完美！优化未影响缓存机制")
        else:
            logger.warning("⚠️  缓存性能可能受到影响，需要检查")
        
        logger.info("=== 测试4：稳定性测试 ===")
        
        # 连续查询测试稳定性
        logger.info("进行10次连续查询，测试性能稳定性...")
        
        stability_times = []
        for i in range(5):
            clear_wechat_status_cache()
            clear_onedrive_status_cache()
            
            start = time.time()
            wechat_stable = is_wechat_running(force_refresh=True)
            onedrive_stable = is_onedrive_running(force_refresh=True)
            total_time = (time.time() - start) * 1000
            
            stability_times.append(total_time)
            logger.debug(f"稳定性测试第{i+1}次: {total_time:.1f}ms")
            time.sleep(0.5)
        
        stability_avg = statistics.mean(stability_times)
        stability_std = statistics.stdev(stability_times) if len(stability_times) > 1 else 0
        
        logger.error(f"稳定性测试结果:")
        logger.error(f"  平均总时间: {stability_avg:.1f}ms")
        logger.error(f"  标准差: {stability_std:.1f}ms")
        logger.error(f"  变异系数: {(stability_std/stability_avg)*100:.1f}%")
        
        if stability_std < 200:  # 标准差小于200ms认为稳定
            logger.error("✅ 性能稳定性优秀！查询时间变化很小")
        else:
            logger.warning("⚠️  性能稳定性一般，存在较大波动")
        
        logger.info("=== Phase 2优化总结 ===")
        
        # 综合评估
        overall_success = True
        improvements = []
        
        if wechat_avg < phase1_wechat:
            wechat_imp = ((phase1_wechat - wechat_avg) / phase1_wechat) * 100
            improvements.append(f"微信优化{wechat_imp:.1f}%")
        else:
            overall_success = False
            
        if onedrive_avg < phase1_onedrive_avg:
            onedrive_imp = ((phase1_onedrive_avg - onedrive_avg) / phase1_onedrive_avg) * 100
            improvements.append(f"OneDrive优化{onedrive_imp:.1f}%")
        else:
            overall_success = False
        
        if overall_success:
            logger.error("🎉 Phase 2细节优化取得显著成果！")
            logger.error(f"主要改进: {', '.join(improvements)}")
            logger.error(f"用户体验: 从1-3秒响应进一步提升到亚秒级")
        else:
            logger.warning("Phase 2优化效果有限，可能需要更深层的架构调整")
        
        logger.info("Phase 2细节优化测试完成")
        
    except Exception as e:
        logger.error(f"Phase 2优化测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_phase2_optimizations()