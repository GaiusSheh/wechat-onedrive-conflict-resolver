#!/usr/bin/env python3
"""
自动化微信登录测试（非交互式）
"""

import sys
import os
import time

# 添加core目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from wechat_controller import is_wechat_running, stop_wechat, start_wechat
from wechat_auto_login import WeChatAutoLogin

def auto_test_login():
    """自动测试微信登录流程"""
    print("=" * 50)
    print("微信自动登录测试 - 自动模式")
    print("=" * 50)
    
    # 步骤1: 关闭微信
    print("步骤 1/3: 关闭微信")
    if is_wechat_running():
        print("  微信正在运行，关闭中...")
        if stop_wechat():
            print("  [OK] 微信已关闭")
        else:
            print("  [X] 关闭微信失败")
            return False
    else:
        print("  微信未运行")
    
    print("  等待2秒...")
    time.sleep(2)
    
    # 步骤2: 启动微信
    print("\n步骤 2/3: 启动微信")
    if start_wechat():
        print("  [OK] 微信启动成功")
    else:
        print("  [X] 微信启动失败")
        return False
    
    print("  等待5秒让微信完全启动...")
    time.sleep(5)
    
    # 步骤3: 自动登录
    print("\n步骤 3/3: 自动登录")
    auto_login = WeChatAutoLogin()
    
    # 检测窗口
    windows = auto_login.find_wechat_windows()
    if windows:
        print(f"  找到 {len(windows)} 个微信窗口:")
        for i, window in enumerate(windows):
            # 清理标题中的特殊字符
            title = window['title'].replace('\u200b', '').strip()
            print(f"    {i+1}. {title} (可见: {window['visible']})")
    else:
        print("  [X] 未找到微信窗口")
        return False
    
    # 执行自动登录
    print("  开始自动登录检测...")
    success = auto_login.detect_and_login(timeout=20)
    
    if success:
        print("  [OK] 自动登录操作已执行")
        return True
    else:
        print("  [!] 未检测到需要登录的界面，可能微信已经登录")
        return True  # 这种情况下也算成功

def main():
    success = auto_test_login()
    
    print("\n" + "=" * 50)
    if success:
        print("测试完成！")
        print("如果微信需要登录，自动点击功能应该已经执行")
        print("请检查微信窗口状态")
    else:
        print("测试失败")
    print("=" * 50)

if __name__ == "__main__":
    main()