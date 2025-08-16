#!/usr/bin/env python3
"""
版本号辅助工具 - 统一版本号管理
"""

import json
import os
from pathlib import Path

class VersionHelper:
    """版本号统一管理类"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.version_file = self.root_dir / "version.json"
        self._version_cache = None
    
    def get_version_info(self):
        """获取版本信息"""
        if self._version_cache is None:
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    self._version_cache = json.load(f)
            else:
                # version.json文件不存在时的错误处理
                raise FileNotFoundError(
                    f"版本配置文件未找到: {self.version_file}\n"
                    "请确保项目根目录存在version.json文件"
                )
        return self._version_cache
    
    def get_version(self):
        """获取版本号"""
        return self.get_version_info()["version"]
    
    def get_version_name(self):
        """获取版本名称"""
        return self.get_version_info()["name"]
    
    def get_full_version_string(self):
        """获取完整版本字符串"""
        info = self.get_version_info()
        return f"v{info['version']} | {info['name']}"
    
    def get_app_title(self):
        """获取应用标题"""
        return f"微信OneDrive冲突解决工具 v{self.get_version()}"

# 全局实例
version_helper = VersionHelper()

# 便捷函数
def get_version():
    """获取当前版本号"""
    return version_helper.get_version()

def get_version_name():
    """获取版本名称"""
    return version_helper.get_version_name()

def get_app_title():
    """获取应用标题"""
    return version_helper.get_app_title()

def get_full_version_string():
    """获取完整版本字符串"""
    return version_helper.get_full_version_string()

if __name__ == "__main__":
    print(f"版本号: {get_version()}")
    print(f"版本名: {get_version_name()}")
    print(f"应用标题: {get_app_title()}")
    print(f"完整版本: {get_full_version_string()}")