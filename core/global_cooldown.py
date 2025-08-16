#!/usr/bin/env python3
"""
全局冷却时间管理器
统一管理所有触发类型（手动、静置、定时）的冷却时间
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Optional

class GlobalCooldownManager:
    """全局冷却时间管理器"""
    
    def __init__(self):
        # 获取exe文件所在目录（而非临时解压目录）
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller打包后的exe运行时
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境运行时
            base_dir = os.path.dirname(os.path.dirname(__file__))
        
        self.state_file = os.path.join(base_dir, 'data', 'global_cooldown_state.json')
        self.last_trigger_time: Optional[datetime] = None
        self.load_state()
    
    def load_state(self):
        """从文件加载上次触发时间"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    timestamp_str = data.get('last_trigger_time')
                    if timestamp_str:
                        self.last_trigger_time = datetime.fromisoformat(timestamp_str)
        except Exception as e:
            # logger.warning(f"加载全局冷却状态失败: {e}")
            self.last_trigger_time = None
    
    def save_state(self):
        """保存当前状态到文件"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            data = {
                'last_trigger_time': self.last_trigger_time.isoformat() if self.last_trigger_time else None,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # logger.warning(f"保存全局冷却状态失败: {e}")
            pass
    
    def is_in_cooldown(self, cooldown_minutes: float) -> bool:
        """检查当前是否在冷却期内"""
        if self.last_trigger_time is None:
            return False
        
        current_time = datetime.now()
        time_since_last = (current_time - self.last_trigger_time).total_seconds()
        cooldown_seconds = cooldown_minutes * 60
        
        return time_since_last < cooldown_seconds
    
    def get_remaining_cooldown_minutes(self, cooldown_minutes: float) -> float:
        """获取剩余冷却时间（分钟）"""
        if self.last_trigger_time is None:
            return 0.0
        
        current_time = datetime.now()
        time_since_last = (current_time - self.last_trigger_time).total_seconds()
        cooldown_seconds = cooldown_minutes * 60
        remaining_seconds = max(0, cooldown_seconds - time_since_last)
        
        return remaining_seconds / 60
    
    def update_last_trigger_time(self, trigger_type: str = "unknown"):
        """更新最后触发时间"""
        self.last_trigger_time = datetime.now()
        self.save_state()
        # logger.info(f"全局冷却时间已更新: {trigger_type} 触发于 {self.last_trigger_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def reset_cooldown(self):
        """重置冷却时间（手动重置功能）"""
        self.last_trigger_time = None
        self.save_state()
        # logger.info("全局冷却时间已手动重置")
    
    def check_and_update_if_allowed(self, cooldown_minutes: float, trigger_type: str = "unknown") -> bool:
        """
        检查是否允许触发，如果允许则更新冷却时间
        返回: True=允许触发, False=还在冷却期
        """
        if self.is_in_cooldown(cooldown_minutes):
            remaining = self.get_remaining_cooldown_minutes(cooldown_minutes)
            # logger.info(f"全局冷却期内，剩余 {remaining:.1f} 分钟，拒绝 {trigger_type} 触发")
            return False
        
        self.update_last_trigger_time(trigger_type)
        return True

# 全局单例实例
_global_cooldown_manager = None

def get_global_cooldown_manager() -> GlobalCooldownManager:
    """获取全局冷却管理器单例"""
    global _global_cooldown_manager
    if _global_cooldown_manager is None:
        _global_cooldown_manager = GlobalCooldownManager()
    return _global_cooldown_manager

# 便捷函数
def is_in_global_cooldown(cooldown_minutes: float) -> bool:
    """检查是否在全局冷却期内"""
    return get_global_cooldown_manager().is_in_cooldown(cooldown_minutes)

def get_remaining_global_cooldown(cooldown_minutes: float) -> float:
    """获取剩余全局冷却时间（分钟）"""
    return get_global_cooldown_manager().get_remaining_cooldown_minutes(cooldown_minutes)

def update_global_cooldown(trigger_type: str = "unknown"):
    """更新全局冷却时间"""
    get_global_cooldown_manager().update_last_trigger_time(trigger_type)

def reset_global_cooldown():
    """重置全局冷却时间"""
    get_global_cooldown_manager().reset_cooldown()

def check_and_trigger_if_allowed(cooldown_minutes: float, trigger_type: str = "unknown") -> bool:
    """检查并在允许时更新触发时间"""
    return get_global_cooldown_manager().check_and_update_if_allowed(cooldown_minutes, trigger_type)