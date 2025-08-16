#!/usr/bin/env python3
"""
测试微信自动登录功能
"""

import sys
import os
import time

# 添加core目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from wechat_auto_login import WeChatAutoLogin
from wechat_controller import is_wechat_running, start_wechat, stop_wechat

def test_window_detection():
    """测试窗口检测功能"""
    print("=== 测试微信窗口检测 ===")
    
    auto_login = WeChatAutoLogin()
    
    if not is_wechat_running():
        print("微信未运行，正在启动...")
        if not start_wechat():
            print("启动微信失败")
            return False
        time.sleep(3)
    
    windows = auto_login.find_wechat_windows()
    
    if windows:
        print(f"找到 {len(windows)} 个微信窗口:")
        for i, window in enumerate(windows):
            print(f"  {i+1}. 标题: '{window['title']}'")
            print(f"      类名: {window['class']}")
            print(f"      可见: {window['visible']}")
            print(f"      PID: {window['pid']}")
            
            if window['visible']:
                buttons = auto_login.find_login_button(window['hwnd'])
                if buttons:
                    print(f"      发现 {len(buttons)} 个按钮:")
                    for btn in buttons[:5]:  # 只显示前5个
                        print(f"        - '{btn['text']}' ({btn['class']}) 可见:{btn['visible']} 可用:{btn['enabled']}")
                        if btn['rect']:
                            print(f"          位置: {btn['rect']}")
            print()
        return True
    else:
        print("未找到微信窗口")
        return False

def test_full_auto_login():
    """测试完整自动登录流程"""
    print("=== 测试完整自动登录流程 ===")
    
    # 确保微信已停止
    print("1. 停止微信...")
    stop_wechat()
    time.sleep(2)
    
    # 启动微信
    print("2. 启动微信...")
    if not start_wechat():
        print("启动微信失败")
        return False
    
    # 自动登录
    print("3. 尝试自动登录...")
    auto_login = WeChatAutoLogin()
    
    success = auto_login.detect_and_login(timeout=30)
    
    if success:
        print("[OK] 自动登录流程完成")
        auto_login.wait_for_login_completion()
    else:
        print("[X] 自动登录失败")
    
    return success

def test_interactive_login():
    """交互式测试登录功能"""
    print("=== 交互式登录测试 ===")
    
    auto_login = WeChatAutoLogin()
    
    print("请确保微信处于需要登录的状态...")
    input("准备好后按 Enter 继续...")
    
    success = auto_login.detect_and_login(timeout=60)
    
    if success:
        print("自动登录尝试完成，请检查微信是否已登录")
        return True
    else:
        print("自动登录失败")
        return False

def main():
    print("微信自动登录测试工具")
    print("=" * 50)
    
    choice = input("""选择测试项目:
1. 窗口检测测试
2. 完整自动登录流程测试  
3. 交互式登录测试
4. 全部测试
请输入 (1-4): """)
    
    if choice == "1":
        test_window_detection()
    elif choice == "2":
        test_full_auto_login()
    elif choice == "3":
        test_interactive_login()
    elif choice == "4":
        print("\n开始全部测试...")
        print("1/3: 窗口检测测试")
        test_window_detection()
        
        print("\n2/3: 完整流程测试")
        test_full_auto_login()
        
        print("\n3/3: 交互式测试")
        if input("\n是否进行交互式测试? (y/n): ").lower() == 'y':
            test_interactive_login()
    else:
        print("无效选择")

if __name__ == "__main__":
    main()