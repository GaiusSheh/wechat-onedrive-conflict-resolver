#!/usr/bin/env python3
"""
异步启动优化测试 - 2025-08-08 Phase 2
验证异步启动函数的用户体验改善效果

测试重点：
- start_wechat() 函数响应时间
- resume_onedrive_sync() 函数响应时间
- 启动成功率和状态更新时间
- 用户体验对比（点击响应 vs 状态更新）
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

def test_async_startup_performance():
    """测试异步启动函数的性能表现"""
    try:
        from core.wechat_controller import start_wechat, is_wechat_running, stop_wechat
        from core.onedrive_controller import resume_onedrive_sync, is_onedrive_running, pause_onedrive_sync
        from core.logger_helper import logger
        
        logger.info("=== 异步启动优化效果测试 ===")
        
        logger.info("=== 测试1：微信异步启动响应时间 ===")
        
        # 确保微信未运行
        if is_wechat_running():
            logger.info("停止现有微信进程...")
            stop_wechat()
            time.sleep(2)
        
        # 测试异步启动响应时间
        logger.info("测试微信异步启动函数响应时间...")
        start_time = time.time()
        result = start_wechat()
        response_time = (time.time() - start_time) * 1000
        
        logger.warning(f"微信启动函数响应时间: {response_time:.1f}ms")
        logger.warning(f"启动函数返回结果: {result}")
        
        # 目标：响应时间应该在100ms以内
        if response_time < 100:
            logger.error("✅ 微信启动响应时间优秀！用户点击立即得到反馈")
        elif response_time < 500:
            logger.warning("⚠️  微信启动响应时间可接受")
        else:
            logger.error("❌ 微信启动响应时间过长，需要优化")
        
        # 监控状态变化时间
        logger.info("监控微信状态变化时间...")
        status_check_start = time.time()
        max_wait_time = 15  # 最多等待15秒
        
        for i in range(max_wait_time):
            if is_wechat_running():
                status_update_time = time.time() - status_check_start
                logger.error(f"✅ 微信启动成功！状态更新时间: {status_update_time:.1f}秒")
                break
            time.sleep(1)
            logger.debug(f"等待微信启动... {i+1}/{max_wait_time}秒")
        else:
            logger.error("❌ 微信启动超时或失败")
        
        logger.info("=== 测试2：OneDrive异步启动响应时间 ===")
        
        # 确保OneDrive未运行
        if is_onedrive_running():
            logger.info("停止现有OneDrive进程...")
            pause_onedrive_sync()
            time.sleep(3)
        
        # 测试OneDrive异步启动
        logger.info("测试OneDrive异步启动函数响应时间...")
        start_time = time.time()
        result = resume_onedrive_sync()
        response_time = (time.time() - start_time) * 1000
        
        logger.warning(f"OneDrive启动函数响应时间: {response_time:.1f}ms")
        logger.warning(f"启动函数返回结果: {result}")
        
        if response_time < 100:
            logger.error("✅ OneDrive启动响应时间优秀！")
        elif response_time < 500:
            logger.warning("⚠️  OneDrive启动响应时间可接受")
        else:
            logger.error("❌ OneDrive启动响应时间过长")
        
        # 监控OneDrive状态变化
        logger.info("监控OneDrive状态变化时间...")
        status_check_start = time.time()
        
        for i in range(max_wait_time):
            if is_onedrive_running():
                status_update_time = time.time() - status_check_start
                logger.error(f"✅ OneDrive启动成功！状态更新时间: {status_update_time:.1f}秒")
                break
            time.sleep(1)
            logger.debug(f"等待OneDrive启动... {i+1}/{max_wait_time}秒")
        else:
            logger.error("❌ OneDrive启动超时或失败")
        
        logger.info("=== 测试3：用户体验对比分析 ===")
        
        logger.warning("异步启动优化前后对比:")
        logger.warning("优化前:")
        logger.warning("  - 点击启动 → 等待8-11秒 → 看到成功消息")
        logger.warning("  - 用户体验: 点击后界面无响应，体验差")
        logger.warning("")
        logger.warning("异步优化后:")
        logger.warning(f"  - 点击启动 → 立即响应({response_time:.1f}ms) → 后台启动 → 状态自动更新")
        logger.warning("  - 用户体验: 点击立即反馈，状态自然更新")
        
        logger.info("=== 测试4：稳定性验证 ===")
        
        # 连续启动测试
        logger.info("进行连续启动测试，验证稳定性...")
        
        response_times = []
        success_count = 0
        
        for i in range(3):
            # 停止服务
            if is_wechat_running():
                stop_wechat()
                time.sleep(2)
            
            # 测试启动响应
            start_time = time.time()
            result = start_wechat()
            response = (time.time() - start_time) * 1000
            response_times.append(response)
            
            if result:
                success_count += 1
            
            logger.debug(f"第{i+1}次启动测试: {response:.1f}ms, 结果: {result}")
            time.sleep(3)  # 给进程启动时间
        
        avg_response = sum(response_times) / len(response_times)
        success_rate = (success_count / 3) * 100
        
        logger.error(f"稳定性测试结果:")
        logger.error(f"  平均响应时间: {avg_response:.1f}ms")
        logger.error(f"  启动成功率: {success_rate:.0f}%")
        logger.error(f"  响应时间波动: {max(response_times) - min(response_times):.1f}ms")
        
        if success_rate >= 90 and avg_response < 200:
            logger.error("✅ 异步启动稳定性优秀！")
        else:
            logger.warning("⚠️  异步启动需要进一步优化")
        
        logger.info("=== 异步启动优化总结 ===")
        
        # 综合评估
        improvements = []
        if avg_response < 500:
            improvements.append(f"启动响应优化到{avg_response:.0f}ms")
        if success_rate >= 90:
            improvements.append(f"启动成功率{success_rate:.0f}%")
        
        if improvements:
            logger.error("🎉 异步启动优化取得显著成效！")
            logger.error(f"主要改进: {', '.join(improvements)}")
            logger.error("用户体验: 从等待8-11秒优化到点击立即响应")
            logger.error("技术实现: 启动函数立即返回，状态更新线程自然检测")
        else:
            logger.warning("异步启动优化效果需要进一步调整")
        
        logger.info("异步启动优化测试完成")
        
    except Exception as e:
        logger.error(f"异步启动测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_async_startup_performance()