#!/usr/bin/env python3
"""
智能缓存测试脚本 - 2025-08-08
验证force_refresh参数的实时状态反馈效果

测试场景：
1. 缓存命中性能（force_refresh=False）
2. 强制刷新实时性（force_refresh=True）  
3. 用户操作后的状态同步效果
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

def test_smart_cache_invalidation():
    """测试智能缓存失效机制"""
    try:
        from core.wechat_controller import is_wechat_running, clear_wechat_status_cache
        from core.onedrive_controller import is_onedrive_running, clear_onedrive_status_cache
        from core.logger_helper import logger
        
        logger.info("开始智能缓存失效测试")
        
        # 清理缓存，确保测试准确性
        clear_wechat_status_cache()
        clear_onedrive_status_cache()
        
        logger.info("=== 测试场景1：缓存性能 ===")
        
        # 第一次调用（建立缓存）
        start_time = time.time()
        wechat_status_1 = is_wechat_running(force_refresh=False)
        duration_1 = (time.time() - start_time) * 1000
        logger.warning(f"微信状态首次查询(缓存建立): {duration_1:.1f}ms, 结果: {'运行' if wechat_status_1 else '停止'}")
        
        # 第二次调用（缓存命中）
        start_time = time.time()
        wechat_status_2 = is_wechat_running(force_refresh=False)
        duration_2 = (time.time() - start_time) * 1000
        logger.info(f"微信状态缓存命中查询: {duration_2:.1f}ms, 结果: {'运行' if wechat_status_2 else '停止'}")
        
        if duration_2 < duration_1:
            improvement = ((duration_1 - duration_2) / duration_1) * 100
            logger.error(f"缓存性能提升: {improvement:.1f}% (从{duration_1:.1f}ms到{duration_2:.1f}ms)")
        
        logger.info("=== 测试场景2：强制刷新实时性 ===")
        
        # 强制刷新测试
        start_time = time.time()
        wechat_status_force = is_wechat_running(force_refresh=True)
        duration_force = (time.time() - start_time) * 1000
        logger.warning(f"微信状态强制刷新查询: {duration_force:.1f}ms, 结果: {'运行' if wechat_status_force else '停止'}")
        
        # 验证强制刷新确实执行了实际查询（时间应该接近首次查询）
        if abs(duration_force - duration_1) < abs(duration_force - duration_2):
            logger.info("✅ 强制刷新确实执行了实际状态检查")
        else:
            logger.warning("⚠️  强制刷新可能没有正确工作")
        
        logger.info("=== 测试场景3：OneDrive智能缓存 ===")
        
        # OneDrive缓存测试
        start_time = time.time()
        od_status_1 = is_onedrive_running(force_refresh=False)
        od_duration_1 = (time.time() - start_time) * 1000
        logger.warning(f"OneDrive状态首次查询: {od_duration_1:.1f}ms, 结果: {'运行' if od_status_1 else '停止'}")
        
        start_time = time.time()
        od_status_2 = is_onedrive_running(force_refresh=False)
        od_duration_2 = (time.time() - start_time) * 1000
        logger.info(f"OneDrive状态缓存命中: {od_duration_2:.1f}ms, 结果: {'运行' if od_status_2 else '停止'}")
        
        start_time = time.time()
        od_status_force = is_onedrive_running(force_refresh=True)
        od_duration_force = (time.time() - start_time) * 1000
        logger.warning(f"OneDrive状态强制刷新: {od_duration_force:.1f}ms, 结果: {'运行' if od_status_force else '停止'}")
        
        logger.info("=== 测试场景4：用户体验模拟 ===")
        
        logger.info("模拟用户操作场景：点击按钮 → 操作完成 → 立即看到状态更新")
        
        # 模拟GUI定时状态检查（使用缓存）
        logger.info("[GUI定时检查] 使用缓存，快速响应")
        for i in range(3):
            start_time = time.time()
            wechat_cached = is_wechat_running(force_refresh=False)
            od_cached = is_onedrive_running(force_refresh=False)
            total_time = (time.time() - start_time) * 1000
            logger.info(f"  第{i+1}次定时检查: {total_time:.1f}ms (微信:{wechat_cached}, OneDrive:{od_cached})")
            time.sleep(0.5)
        
        # 模拟用户操作后的强制刷新
        logger.info("[用户操作后] 强制刷新，确保实时状态")
        start_time = time.time()
        wechat_realtime = is_wechat_running(force_refresh=True)
        od_realtime = is_onedrive_running(force_refresh=True)
        realtime_total = (time.time() - start_time) * 1000
        logger.warning(f"用户操作后强制刷新: {realtime_total:.1f}ms (微信:{wechat_realtime}, OneDrive:{od_realtime})")
        
        logger.info("=== 性能总结 ===")
        
        # 计算整体性能表现
        cached_avg = (duration_2 + od_duration_2) / 2
        realtime_avg = (duration_force + od_duration_force) / 2
        
        logger.error(f"缓存模式平均响应: {cached_avg:.1f}ms (用于GUI定时检查)")
        logger.error(f"实时模式平均响应: {realtime_avg:.1f}ms (用于用户操作后)")
        logger.error(f"智能缓存方案达到平衡：90%时间享受{cached_avg:.1f}ms极速响应")
        logger.error(f"用户操作时提供{realtime_avg:.1f}ms实时准确状态")
        
        # 与历史数据对比
        historical_time = 9391.1  # 优化前的状态检查时间
        cache_improvement = ((historical_time - cached_avg) / historical_time) * 100
        realtime_improvement = ((historical_time - realtime_avg) / historical_time) * 100
        
        logger.error(f"相比优化前性能:")
        logger.error(f"  缓存模式提升: {cache_improvement:.1f}% ({historical_time:.1f}ms → {cached_avg:.1f}ms)")
        logger.error(f"  实时模式提升: {realtime_improvement:.1f}% ({historical_time:.1f}ms → {realtime_avg:.1f}ms)")
        
        if cache_improvement > 95 and realtime_improvement > 50:
            logger.error("🎉 智能缓存方案大获成功！完美平衡性能与实时性")
        elif cache_improvement > 90:
            logger.error("✅ 智能缓存方案效果优秀！显著提升用户体验")
        else:
            logger.warning("⚠️  缓存方案有待进一步优化")
        
        logger.info("智能缓存失效测试完成")
        
    except Exception as e:
        logger.error(f"智能缓存测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_smart_cache_invalidation()