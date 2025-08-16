#!/usr/bin/env python3
# 临时测试脚本：测试OneDrive启动策略

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.onedrive_controller import resume_onedrive_sync

def test_onedrive_startup():
    """测试OneDrive启动策略"""
    print("测试OneDrive简单启动...")
    try:
        if resume_onedrive_sync():
            print("[成功] OneDrive启动测试成功！")
        else:
            print("[失败] OneDrive启动测试失败")
    except Exception as e:
        print(f"[错误] 测试过程中发生错误：{e}")

if __name__ == "__main__":
    test_onedrive_startup()