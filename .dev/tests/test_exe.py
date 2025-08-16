#!/usr/bin/env python3
"""
测试打包后的exe文件功能
"""
import subprocess
import time
import os
import sys

def test_exe_basic():
    """测试exe文件基本功能"""
    exe_path = "dist/WeChatOneDriveTool.exe"
    
    if not os.path.exists(exe_path):
        print("ERROR: exe file not found!")
        return False
    
    print(f"Found exe file: {exe_path}")
    print(f"File size: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
    
    # 测试版本参数
    print("\n=== Testing --version ===")
    try:
        result = subprocess.run([exe_path, "--version"], 
                              capture_output=True, text=True, timeout=10)
        print(f"Version output: {result.stdout.strip()}")
        print(f"Return code: {result.returncode}")
    except subprocess.TimeoutExpired:
        print("Version test timed out")
    except Exception as e:
        print(f"Version test failed: {e}")
    
    # 测试帮助参数
    print("\n=== Testing --help ===")
    try:
        result = subprocess.run([exe_path, "--help"], 
                              capture_output=True, text=True, timeout=10)
        print(f"Help output (first 200 chars): {result.stdout[:200]}...")
        print(f"Return code: {result.returncode}")
    except subprocess.TimeoutExpired:
        print("Help test timed out")
    except Exception as e:
        print(f"Help test failed: {e}")
    
    print(f"\n=== Manual Testing Required ===")
    print("Please manually test the following:")
    print("1. Double-click the exe file to test GUI launch")
    print("2. Check if custom icon appears in taskbar")
    print("3. Test system tray functionality (right-click on tray icon)")
    print("4. Test minimize to tray feature")
    print("5. Test settings panel - especially auto-start options")
    print("6. Test the --start-minimized parameter:")
    print(f"   {exe_path} --start-minimized")
    
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("WeChatOneDriveTool.exe Test Script")
    print("=" * 50)
    
    if test_exe_basic():
        print("\n" + "=" * 50)
        print("Basic tests completed!")
        print("Please proceed with manual testing.")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("Tests failed!")
        print("=" * 50)
        sys.exit(1)