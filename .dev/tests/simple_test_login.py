#!/usr/bin/env python3
"""
简单的微信自动登录测试
"""

import sys
import os

# 添加core目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from wechat_controller import is_wechat_running, stop_wechat, start_wechat
from wechat_auto_login import WeChatAutoLogin

def main():
    print("简单微信自动登录测试")
    print("=" * 40)
    
    # 检查微信状态
    print("1. 检查微信状态...")
    if is_wechat_running():
        print("   微信正在运行")
        choice = input("   是否要重启微信来测试自动登录? (y/n): ")
        if choice.lower() == 'y':
            print("   停止微信...")
            stop_wechat()
            print("   等待2秒...")
            import time
            time.sleep(2)
        else:
            print("   测试结束")
            return
    
    # 启动微信
    print("2. 启动微信...")
    if not start_wechat():
        print("   启动失败")
        return
    
    print("3. 等待微信完全启动...")
    import time
    time.sleep(5)
    
    # 检测登录界面
    print("4. 检测登录界面...")
    auto_login = WeChatAutoLogin()
    
    windows = auto_login.find_wechat_windows()
    if windows:
        print(f"   找到 {len(windows)} 个微信窗口")
        for window in windows:
            print(f"   - {window['title']} (可见: {window['visible']})")
    else:
        print("   未找到微信窗口")
        return
    
    # 尝试自动登录
    print("5. 尝试自动登录...")
    success = auto_login.detect_and_login(timeout=15)
    
    if success:
        print("   [OK] 自动登录操作已执行")
    else:
        print("   [X] 未检测到登录界面或登录失败")
    
    print("\n测试完成")

if __name__ == "__main__":
    main()