#!/usr/bin/env python3
"""
专门测试微信自动登录功能
"""

import sys
import os
import time

# 添加core目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from wechat_controller import is_wechat_running, stop_wechat, start_wechat
from wechat_auto_login import WeChatAutoLogin

def test_login_process():
    """测试完整的关闭-启动-自动登录流程"""
    print("=" * 50)
    print("微信自动登录测试")
    print("=" * 50)
    
    # 步骤1: 检查并关闭微信
    print("步骤 1: 关闭微信")
    if is_wechat_running():
        print("  微信正在运行，关闭中...")
        if stop_wechat():
            print("  [OK] 微信已关闭")
        else:
            print("  [X] 关闭微信失败")
            return False
    else:
        print("  微信未运行")
    
    # 等待2秒
    print("  等待2秒...")
    time.sleep(2)
    
    # 步骤2: 启动微信
    print("\n步骤 2: 启动微信")
    if start_wechat():
        print("  [OK] 微信启动成功")
    else:
        print("  [X] 微信启动失败")
        return False
    
    # 等待微信完全启动
    print("  等待5秒让微信完全启动...")
    time.sleep(5)
    
    # 步骤3: 自动登录
    print("\n步骤 3: 尝试自动登录")
    auto_login = WeChatAutoLogin()
    
    # 检测微信窗口
    print("  检测微信窗口...")
    windows = auto_login.find_wechat_windows()
    if not windows:
        print("  [X] 未找到微信窗口")
        return False
    
    print(f"  找到 {len(windows)} 个微信窗口")
    for window in windows:
        print(f"    - {window['title']} (可见: {window['visible']})")
    
    # 执行自动登录
    print("  执行自动登录...")
    success = auto_login.detect_and_login(timeout=30)
    
    if success:
        print("  [OK] 自动登录操作已执行")
        
        # 等待登录完成
        print("  等待登录完成...")
        if auto_login.wait_for_login_completion():
            print("  [OK] 登录完成")
        else:
            print("  [!] 登录完成检测超时")
        
        return True
    else:
        print("  [X] 自动登录失败")
        return False

def main():
    print("这个测试将：")
    print("1. 关闭当前运行的微信")
    print("2. 重新启动微信") 
    print("3. 自动检测并点击登录按钮")
    print()
    
    choice = input("确认开始测试? (y/n): ")
    if choice.lower() != 'y':
        print("测试取消")
        return
    
    success = test_login_process()
    
    print("\n" + "=" * 50)
    if success:
        print("测试完成！请检查微信是否已成功登录")
    else:
        print("测试失败，请检查错误信息")
    print("=" * 50)

if __name__ == "__main__":
    main()