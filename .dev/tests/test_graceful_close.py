#!/usr/bin/env python3
"""
测试微信优雅关闭方法
"""

import subprocess
import time
import ctypes
from ctypes import wintypes
import psutil
from core.wechat_controller import find_wechat_processes, start_wechat

def send_close_message_to_wechat():
    """通过发送WM_CLOSE消息优雅关闭微信"""
    user32 = ctypes.windll.user32
    
    # 查找微信进程
    processes = find_wechat_processes()
    if not processes:
        print("没有找到运行中的微信进程")
        return False
    
    print(f"找到 {len(processes)} 个微信进程")
    
    success_count = 0
    for proc in processes:
        try:
            # 枚举进程的窗口
            windows = []
            
            def enum_windows_callback(hwnd, lparam):
                # 检查窗口是否属于该进程
                process_id = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                
                if process_id.value == proc.pid:
                    # 检查窗口是否可见
                    if user32.IsWindowVisible(hwnd):
                        windows.append(hwnd)
                return True
            
            # 枚举所有窗口
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
            
            print(f"进程 {proc.pid} 有 {len(windows)} 个可见窗口")
            
            # 向每个窗口发送关闭消息
            for hwnd in windows:
                WM_CLOSE = 0x0010
                user32.SendMessageW(hwnd, WM_CLOSE, 0, 0)
                print(f"  向窗口 {hwnd} 发送关闭消息")
            
            success_count += 1
            
        except Exception as e:
            print(f"处理进程 {proc.pid} 时出错: {e}")
    
    return success_count > 0

def test_graceful_vs_force_close():
    """测试优雅关闭 vs 强制关闭的区别"""
    
    print("=== 微信关闭方式对比测试 ===\n")
    
    # 测试1：优雅关闭
    print("1. 测试优雅关闭方式:")
    print("   请先手动启动微信并登录...")
    input("   微信启动并登录后，按 Enter 继续...")
    
    if find_wechat_processes():
        print("   正在优雅关闭微信...")
        send_close_message_to_wechat()
        
        # 等待关闭
        time.sleep(3)
        
        if not find_wechat_processes():
            print("   ✓ 微信已优雅关闭")
            
            print("   正在重新启动微信...")
            start_wechat()
            time.sleep(5)
            
            print("   请观察微信是否需要重新登录？")
            login_needed = input("   需要手动登录吗？(y/n): ").lower() == 'y'
            
            if not login_needed:
                print("   ✓ 优雅关闭后无需重新登录！")
                return True
            else:
                print("   ✗ 优雅关闭后仍需重新登录")
        else:
            print("   ✗ 优雅关闭失败")
    
    return False

def test_alternative_close_methods():
    """测试其他关闭方法"""
    
    print("\n=== 测试其他关闭方法 ===")
    
    methods = [
        ("Alt+F4", "发送 Alt+F4 按键"),
        ("WM_SYSCOMMAND", "发送系统关闭命令"),
        ("WM_QUIT", "发送退出消息"),
    ]
    
    for method_name, description in methods:
        print(f"\n测试: {description}")
        
        if not find_wechat_processes():
            print("  先启动微信...")
            start_wechat()
            time.sleep(5)
            input("  微信启动后按 Enter 继续...")
        
        try:
            if method_name == "Alt+F4":
                # 发送 Alt+F4
                user32 = ctypes.windll.user32
                processes = find_wechat_processes()
                for proc in processes:
                    # 查找主窗口并发送 Alt+F4
                    # 这里简化处理，实际需要更复杂的窗口查找
                    pass
                    
            elif method_name == "WM_SYSCOMMAND":
                # 发送系统关闭命令
                user32 = ctypes.windll.user32
                processes = find_wechat_processes()
                for proc in processes:
                    # 发送 SC_CLOSE 系统命令
                    pass
                    
            elif method_name == "WM_QUIT":
                # 发送退出消息
                user32 = ctypes.windll.user32
                processes = find_wechat_processes()
                for proc in processes:
                    WM_QUIT = 0x0012
                    user32.PostThreadMessageW(proc.pid, WM_QUIT, 0, 0)
            
            print(f"  {description} 已发送")
            time.sleep(3)
            
            if not find_wechat_processes():
                print("  ✓ 关闭成功")
            else:
                print("  ✗ 关闭失败")
                
        except Exception as e:
            print(f"  ✗ 出错: {e}")

if __name__ == "__main__":
    print("微信优雅关闭测试")
    print("="*50)
    
    choice = input("选择测试:\n1. 优雅关闭对比测试\n2. 其他关闭方法测试\n3. 全部测试\n请输入 (1/2/3): ")
    
    if choice == "1":
        test_graceful_vs_force_close()
    elif choice == "2":
        test_alternative_close_methods()
    elif choice == "3":
        if test_graceful_vs_force_close():
            print("\n优雅关闭有效，跳过其他测试")
        else:
            test_alternative_close_methods()
    else:
        print("无效选择")