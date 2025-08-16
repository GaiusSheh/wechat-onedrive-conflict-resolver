import subprocess
import json
import os
import time

def test_powershell_onedrive_methods():
    """测试不同的PowerShell方法来检测OneDrive同步状态"""
    
    print("=== 测试OneDrive同步状态检测方法 ===\n")
    
    # 方法1：检查OneDrive进程的文件访问活动
    print("方法1：检查OneDrive进程活动")
    try:
        cmd = [
            'powershell', '-Command',
            'Get-Process OneDrive -ErrorAction SilentlyContinue | Select-Object ProcessName, CPU, WorkingSet'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"结果: {result.stdout.strip()}")
        print(f"错误: {result.stderr.strip()}" if result.stderr else "无错误")
    except Exception as e:
        print(f"方法1失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 方法2：检查OneDrive文件夹的最近修改时间
    print("方法2：检查OneDrive文件夹状态")
    try:
        onedrive_path = os.path.expanduser("~\\OneDrive")
        if os.path.exists(onedrive_path):
            print(f"OneDrive路径: {onedrive_path}")
            # 获取最近修改的文件
            cmd = [
                'powershell', '-Command',
                f'Get-ChildItem "{onedrive_path}" -Recurse -Force | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Select-Object Name, LastWriteTime, Length'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            print(f"最近修改的文件:")
            print(result.stdout.strip())
        else:
            print("未找到OneDrive文件夹")
    except Exception as e:
        print(f"方法2失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 方法3：尝试使用注册表查看OneDrive状态
    print("方法3：检查OneDrive注册表信息")
    try:
        cmd = [
            'powershell', '-Command',
            'Get-ItemProperty "HKCU:\\Software\\Microsoft\\OneDrive" -ErrorAction SilentlyContinue | Select-Object UserFolder, Version'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"注册表信息:")
        print(result.stdout.strip())
    except Exception as e:
        print(f"方法3失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 方法4：检查OneDrive的日志文件
    print("方法4：检查OneDrive日志文件")
    try:
        log_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\OneDrive\\logs")
        if os.path.exists(log_path):
            print(f"日志路径: {log_path}")
            cmd = [
                'powershell', '-Command',
                f'Get-ChildItem "{log_path}" -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | Select-Object Name, LastWriteTime, Length'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            print(f"最新日志文件:")
            print(result.stdout.strip())
        else:
            print("未找到OneDrive日志文件夹")
    except Exception as e:
        print(f"方法4失败: {e}")

def check_onedrive_activity_simple():
    """简单的活动检测方法"""
    print("\n=== 简单活动检测测试 ===")
    
    try:
        # 获取OneDrive进程的CPU使用率
        cmd = [
            'powershell', '-Command',
            '''
            $process = Get-Process OneDrive -ErrorAction SilentlyContinue
            if ($process) {
                $cpu1 = $process.CPU
                Start-Sleep -Seconds 2
                $process = Get-Process OneDrive -ErrorAction SilentlyContinue
                $cpu2 = $process.CPU
                $cpuUsage = $cpu2 - $cpu1
                Write-Output "CPU使用情况: $cpuUsage"
                Write-Output "工作集: $($process.WorkingSet / 1MB) MB"
            } else {
                Write-Output "OneDrive进程未运行"
            }
            '''
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        print(result.stdout.strip())
        
    except Exception as e:
        print(f"简单检测失败: {e}")

if __name__ == "__main__":
    test_powershell_onedrive_methods()
    check_onedrive_activity_simple()