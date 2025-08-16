#!/usr/bin/env python3
"""
自动触发功能测试脚本 - 2025-08-09
检查自动监控线程为什么没有启动
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))

def test_config_loading():
    """测试配置加载"""
    try:
        from core.config_manager import ConfigManager
        
        print("=== 配置管理器测试 ===")
        config = ConfigManager()
        
        print(f"配置文件路径: {config.config_file}")
        print(f"配置文件是否存在: {os.path.exists(config.config_file)}")
        
        print("\n=== 静置触发配置 ===")
        print(f"is_idle_trigger_enabled(): {config.is_idle_trigger_enabled()}")
        print(f"get_idle_minutes(): {config.get_idle_minutes()}")
        print(f"get_idle_cooldown_minutes(): {config.get_idle_cooldown_minutes()}")
        
        print("\n=== 原始配置数据 ===")
        idle_config = config.config.get('idle_trigger', {})
        print(f"idle_trigger配置: {idle_config}")
        
        print("\n=== 定时触发配置 ===")
        print(f"is_scheduled_trigger_enabled(): {config.is_scheduled_trigger_enabled()}")
        scheduled_config = config.config.get('scheduled_trigger', {})
        print(f"scheduled_trigger配置: {scheduled_config}")
        
        return config
        
    except Exception as e:
        print(f"配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_idle_detector():
    """测试空闲检测器"""
    try:
        from core.idle_detector import IdleDetector
        
        print("\n=== 空闲检测器测试 ===")
        detector = IdleDetector()
        
        idle_seconds = detector.get_idle_time_seconds()
        print(f"当前系统空闲时间: {idle_seconds:.1f}秒")
        
        idle_minutes = idle_seconds / 60
        print(f"当前系统空闲时间: {idle_minutes:.1f}分钟")
        
        return detector
        
    except Exception as e:
        print(f"空闲检测器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_monitoring_conditions():
    """测试监控启动条件"""
    print("\n=== 监控启动条件测试 ===")
    
    config = test_config_loading()
    detector = test_idle_detector()
    
    if config and detector:
        print("\n=== 综合条件检查 ===")
        has_method = hasattr(config, 'is_idle_trigger_enabled')
        is_enabled = config.is_idle_trigger_enabled() if has_method else False
        
        print(f"config对象有is_idle_trigger_enabled方法: {has_method}")
        print(f"静置触发启用状态: {is_enabled}")
        print(f"启动监控线程条件: {has_method and is_enabled}")
        
        if has_method and is_enabled:
            print("✅ 监控线程应该启动")
            
            idle_minutes = config.get_idle_minutes()
            cooldown_minutes = config.get_idle_cooldown_minutes()
            current_idle = detector.get_idle_time_seconds()
            idle_threshold = idle_minutes * 60
            
            print(f"\n=== 触发条件检查 ===")
            print(f"配置的空闲触发时间: {idle_minutes}分钟 ({idle_threshold}秒)")
            print(f"配置的冷却时间: {cooldown_minutes}分钟")
            print(f"当前空闲时间: {current_idle:.1f}秒")
            print(f"是否达到触发条件: {current_idle >= idle_threshold}")
            
        else:
            print("❌ 监控线程不会启动")
            if not has_method:
                print("   原因: config对象缺少is_idle_trigger_enabled方法")
            if not is_enabled:
                print("   原因: 静置触发未启用")

if __name__ == "__main__":
    test_monitoring_conditions()