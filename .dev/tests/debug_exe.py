#!/usr/bin/env python3
"""
调试exe文件启动问题
"""
import subprocess
import time
import os
import psutil

def check_running_processes():
    """检查是否有WeChatOneDriveTool进程在运行"""
    print("=== 检查运行中的进程 ===")
    found_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and 'WeChatOneDriveTool' in proc.info['name']:
                found_processes.append(proc.info)
                print(f"找到进程: PID={proc.info['pid']}, Name={proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if not found_processes:
        print("未找到WeChatOneDriveTool相关进程")
    
    return found_processes

def test_exe_with_console():
    """在控制台模式下测试exe"""
    exe_path = "dist/WeChatOneDriveTool.exe"
    
    if not os.path.exists(exe_path):
        print(f"错误：找不到exe文件 {exe_path}")
        return False
    
    print(f"=== 测试exe文件: {exe_path} ===")
    
    # 1. 检查当前进程
    print("\n1. 启动前进程检查:")
    check_running_processes()
    
    # 2. 尝试启动exe并等待
    print("\n2. 启动exe文件...")
    try:
        # 使用subprocess.Popen来启动，不等待结束
        process = subprocess.Popen([exe_path], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        print(f"进程已启动，PID: {process.pid}")
        
        # 等待3秒看看是否有输出或错误
        time.sleep(3)
        
        # 检查进程状态
        if process.poll() is None:
            print("进程仍在运行...")
            
            # 检查是否有新的进程
            print("\n3. 启动后进程检查:")
            check_running_processes()
            
            # 尝试获取输出
            try:
                stdout, stderr = process.communicate(timeout=5)
                if stdout:
                    print(f"标准输出: {stdout}")
                if stderr:
                    print(f"错误输出: {stderr}")
            except subprocess.TimeoutExpired:
                print("进程仍在运行，超时无输出")
                process.terminate()
                
        else:
            # 进程已退出
            return_code = process.returncode
            stdout, stderr = process.communicate()
            
            print(f"进程已退出，返回码: {return_code}")
            if stdout:
                print(f"标准输出: {stdout}")
            if stderr:
                print(f"错误输出: {stderr}")
        
    except Exception as e:
        print(f"启动exe时出错: {e}")
        return False
    
    return True

def test_dependencies_in_exe():
    """测试exe中的依赖是否正确"""
    print("\n=== 测试当前环境依赖 ===")
    
    try:
        import tkinter
        print("OK: tkinter available")
    except ImportError as e:
        print(f"ERROR: tkinter not available: {e}")
    
    try:
        import ttkbootstrap
        print("OK: ttkbootstrap available")
    except ImportError as e:
        print(f"ERROR: ttkbootstrap not available: {e}")
    
    try:
        import PIL
        print("OK: PIL/Pillow available")
    except ImportError as e:
        print(f"ERROR: PIL/Pillow not available: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("WeChatOneDriveTool.exe 调试脚本")
    print("=" * 60)
    
    test_dependencies_in_exe()
    test_exe_with_console()
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("如果进程启动但没有窗口，可能是以下原因：")
    print("1. 程序在系统托盘中运行（检查任务栏右下角）")
    print("2. GUI初始化失败但程序未正确退出")
    print("3. 缺少必要的GUI组件或字体")
    print("4. 防病毒软件阻止了窗口显示")
    print("=" * 60)