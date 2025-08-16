#!/usr/bin/env python3
"""
调试配置读取问题
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config_manager import ConfigManager

def debug_config():
    """调试配置读取"""
    print("=== 配置调试 ===")
    
    try:
        config = ConfigManager()
        print(f"配置文件路径: {config.config_file}")
        
        # 检查原始配置数据
        print("\n原始配置数据:")
        import json
        with open(config.config_file, 'r', encoding='utf-8') as f:
            raw_config = json.load(f)
        print(json.dumps(raw_config, ensure_ascii=False, indent=2))
        
        # 检查配置管理器的读取结果
        print(f"\n配置管理器读取结果:")
        print(f"idle_trigger.enabled: {config.get('idle_trigger.enabled')}")
        print(f"is_idle_trigger_enabled(): {config.is_idle_trigger_enabled()}")
        print(f"get_idle_minutes(): {config.get_idle_minutes()}")
        print(f"get_idle_cooldown_minutes(): {config.get_idle_cooldown_minutes()}")
        
    except Exception as e:
        print(f"调试配置时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_config()