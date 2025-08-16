#!/usr/bin/env python3
"""
微信启动参数测试脚本
用于测试微信是否支持自动登录或其他有用的命令行参数
"""

import subprocess
import time
import os
import sys
from core.wechat_controller import find_wechat_processes, stop_wechat

def test_wechat_parameters():
    """测试微信的各种启动参数"""
    
    # 常见的微信安装路径
    wechat_paths = [
        "C:\\Program Files\\Tencent\\Weixin\\Weixin.exe",
        "C:\\Program Files (x86)\\Tencent\\Weixin\\Weixin.exe",
        os.path.expanduser("~\\AppData\\Roaming\\Tencent\\Weixin\\Weixin.exe"),
        os.path.expanduser("~\\AppData\\Local\\Tencent\\Weixin\\Weixin.exe")
    ]
    
    wechat_path = None
    for path in wechat_paths:
        if os.path.exists(path):
            wechat_path = path
            print(f"找到微信安装路径: {path}")
            break
    
    if not wechat_path:
        print("未找到微信安装路径")
        return
    
    # 要测试的参数列表
    test_params = [
        [],  # 正常启动
        ["/?"],  # 帮助
        ["/help"],  # 帮助
        ["--help"],  # 帮助
        ["-h"],  # 帮助
        ["/autologin"],  # 自动登录
        ["/auto"],  # 自动
        ["/silent"],  # 静默启动
        ["/background"],  # 后台启动
        ["/login"],  # 登录
        ["/start"],  # 启动
    ]
    
    print("\n=== 微信启动参数测试 ===")
    print("注意：请在每次测试后手动关闭微信窗口\n")
    
    for i, params in enumerate(test_params):
        print(f"测试 {i+1}/{len(test_params)}: {wechat_path} {' '.join(params)}")
        
        try:
            # 确保微信已停止
            stop_wechat()
            time.sleep(2)
            
            # 启动微信
            if params:
                proc = subprocess.Popen([wechat_path] + params, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                proc = subprocess.Popen([wechat_path])
            
            # 等待启动
            time.sleep(3)
            
            # 检查进程状态
            if find_wechat_processes():
                print("  ✓ 微信启动成功")
                
                # 等待用户观察结果
                input("  请观察微信窗口状态，然后按Enter继续...")
            else:
                print("  ✗ 微信启动失败")
            
        except Exception as e:
            print(f"  ✗ 启动出错: {e}")
        
        print()

def test_registry_settings():
    """检查微信注册表设置中是否有自动登录选项"""
    try:
        import winreg
        
        print("=== 微信注册表设置检查 ===")
        
        # 常见的微信注册表路径
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Tencent\Weixin"),
            (winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Tencent\Weixin"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Tencent\WeChat"),
        ]
        
        for hkey, path in registry_paths:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    print(f"\n找到注册表项: {path}")
                    
                    # 枚举所有值
                    i = 0
                    while True:
                        try:
                            name, value, type = winreg.EnumValue(key, i)
                            print(f"  {name}: {value} (类型: {type})")
                            i += 1
                        except WindowsError:
                            break
                            
            except FileNotFoundError:
                print(f"未找到注册表项: {path}")
            except Exception as e:
                print(f"读取注册表项 {path} 出错: {e}")
                
    except ImportError:
        print("无法导入winreg模块")

if __name__ == "__main__":
    print("微信启动参数和设置测试工具")
    print("="*50)
    
    choice = input("选择测试类型:\n1. 启动参数测试\n2. 注册表设置检查\n3. 全部测试\n请输入 (1/2/3): ")
    
    if choice == "1":
        test_wechat_parameters()
    elif choice == "2":
        test_registry_settings()
    elif choice == "3":
        test_registry_settings()
        print("\n" + "="*50 + "\n")
        test_wechat_parameters()
    else:
        print("无效选择")