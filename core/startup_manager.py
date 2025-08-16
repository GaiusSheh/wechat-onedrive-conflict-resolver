"""
微信OneDrive冲突解决工具 - 开机自启动管理器

该模块负责管理Windows开机自启动功能。
v4.0版本：支持PyInstaller打包后的exe文件自启动管理。
"""

import os
import sys
import winreg
from pathlib import Path

class StartupManager:
    """开机自启动管理器"""
    
    def __init__(self):
        self.app_name = "WeChatOneDriveTool"
        self.registry_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
    def get_exe_path(self):
        """获取当前可执行文件路径"""
        if getattr(sys, 'frozen', False):
            # PyInstaller打包后的exe路径
            return sys.executable
        else:
            # 开发环境，返回脚本路径
            return os.path.abspath(__file__)
    
    def is_startup_enabled(self):
        """检查是否已设置开机自启"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key) as key:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                # 检查注册表中的路径是否存在（去除启动参数）
                exe_path = value.split(' --')[0].strip('"')
                return os.path.exists(exe_path)
        except (FileNotFoundError, OSError):
            return False
    
    def enable_startup(self, minimized=True):
        """启用开机自启动
        
        Args:
            minimized (bool): 是否最小化启动
            
        Returns:
            tuple: (成功状态, 消息)
        """
        try:
            exe_path = self.get_exe_path()
            startup_command = f'"{exe_path}"'
            
            # 如果设置为最小化启动，添加参数
            if minimized:
                startup_command += " --start-minimized"
            
            # 写入注册表
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.registry_key) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, startup_command)
            
            return True, "开机自启动已启用"
        except Exception as e:
            return False, f"启用开机自启动失败: {e}"
    
    def disable_startup(self):
        """禁用开机自启动
        
        Returns:
            tuple: (成功状态, 消息)
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, self.app_name)
            return True, "开机自启动已禁用"
        except FileNotFoundError:
            return True, "开机自启动未设置"
        except Exception as e:
            return False, f"禁用开机自启动失败: {e}"
    
    def get_startup_command(self):
        """获取当前的启动命令
        
        Returns:
            str: 启动命令，如果未设置则返回None
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key) as key:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                return value
        except (FileNotFoundError, OSError):
            return None
    
    def get_startup_status(self):
        """获取开机自启动详细状态
        
        Returns:
            dict: 包含启动状态、命令、是否最小化等信息
        """
        command = self.get_startup_command()
        if command is None:
            return {
                'enabled': False,
                'command': None,
                'minimized': False,
                'exe_exists': False
            }
        
        # 解析命令
        exe_path = command.split(' --')[0].strip('"')
        minimized = '--start-minimized' in command
        exe_exists = os.path.exists(exe_path)
        
        return {
            'enabled': True,
            'command': command,
            'exe_path': exe_path,
            'minimized': minimized,
            'exe_exists': exe_exists
        }

# 测试代码
if __name__ == '__main__':
    manager = StartupManager()
    
    print("=== 开机自启动管理器测试 ===")
    print(f"当前exe路径: {manager.get_exe_path()}")
    print(f"是否已启用: {manager.is_startup_enabled()}")
    
    status = manager.get_startup_status()
    print("详细状态:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    if status['enabled']:
        print(f"当前启动命令: {status['command']}")