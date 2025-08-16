#!/usr/bin/env python3
"""
缓存策略性能测试脚本（简化版）
使用项目统一日志系统，测试缓存优化效果
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

def test_cache_optimization():
    """测试缓存优化效果"""
    try:
        from core.wechat_controller import is_wechat_running, clear_wechat_status_cache
        from core.onedrive_controller import is_onedrive_running, clear_onedrive_status_cache
        from core.logger_helper import logger
        
        logger.info("开始缓存策略性能测试")
        
        # 清理缓存，确保第一次是实际查询
        clear_wechat_status_cache()
        clear_onedrive_status_cache()
        
        # 测试微信状态检查
        logger.debug("测试微信状态检查性能")
        
        # 第一次：实际查询（预期较慢）
        start_time = time.time()
        wechat_result1 = is_wechat_running()
        duration1 = (time.time() - start_time) * 1000
        logger.warning(f"微信状态第1次查询耗时: {duration1:.1f}ms (实际查询)")
        
        # 第二次：缓存命中（预期很快）
        start_time = time.time()
        wechat_result2 = is_wechat_running()
        duration2 = (time.time() - start_time) * 1000
        logger.info(f"微信状态第2次查询耗时: {duration2:.1f}ms (缓存命中)")
        
        # 测试OneDrive状态检查
        logger.debug("测试OneDrive状态检查性能")
        
        # 第一次：实际查询
        start_time = time.time()
        od_result1 = is_onedrive_running()
        od_duration1 = (time.time() - start_time) * 1000
        logger.warning(f"OneDrive状态第1次查询耗时: {od_duration1:.1f}ms (实际查询)")
        
        # 第二次：缓存命中
        start_time = time.time()
        od_result2 = is_onedrive_running()
        od_duration2 = (time.time() - start_time) * 1000
        logger.info(f"OneDrive状态第2次查询耗时: {od_duration2:.1f}ms (缓存命中)")
        
        # 计算性能提升
        total_first = duration1 + od_duration1
        total_cached = duration2 + od_duration2
        
        if total_cached < total_first:
            improvement = ((total_first - total_cached) / total_first) * 100
            speedup = total_first / total_cached
            logger.error(f"缓存优化性能提升: {improvement:.1f}% (提速{speedup:.1f}倍)")
            logger.error(f"响应时间: {total_first:.1f}ms → {total_cached:.1f}ms")
            
            # 与历史数据对比
            historical_total = 9391.1  # 从日志获取的历史慢查询时间
            if total_cached < historical_total:
                vs_historical = ((historical_total - total_cached) / historical_total) * 100
                logger.error(f"相比历史最慢记录提升: {vs_historical:.1f}%")
                logger.error(f"从{historical_total/1000:.1f}秒优化到{total_cached/1000:.3f}秒")
        
        logger.info("缓存策略性能测试完成")
        
    except Exception as e:
        logger.error(f"缓存测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cache_optimization()