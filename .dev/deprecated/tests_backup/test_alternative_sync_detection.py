import subprocess
import os
import time

def check_onedrive_network_activity():
    """检查OneDrive的网络活动作为同步指标"""
    powershell_script = '''
    try {
        $oneDriveProcess = Get-Process OneDrive -ErrorAction SilentlyContinue
        if ($oneDriveProcess) {
            # 获取网络连接
            $connections = Get-NetTCPConnection -OwningProcess $oneDriveProcess.Id -ErrorAction SilentlyContinue | Where-Object {$_.State -eq "Established"}
            $connectionCount = ($connections | Measure-Object).Count
            
            # 获取进程的IO统计
            $process = Get-WmiObject -Query "SELECT * FROM Win32_Process WHERE ProcessId = $($oneDriveProcess.Id)" -ErrorAction SilentlyContinue
            
            Write-Output "网络连接数: $connectionCount"
            Write-Output "进程线程数: $($oneDriveProcess.Threads.Count)"
            Write-Output "内存使用: $([math]::Round($oneDriveProcess.WorkingSet / 1MB, 2)) MB"
            
            # 检查最近的文件IO活动
            $ioActivity = Get-Counter "\\Process(OneDrive*)\\IO Data Bytes/sec" -SampleInterval 1 -MaxSamples 2 -ErrorAction SilentlyContinue
            if ($ioActivity) {
                $avgIO = ($ioActivity.CounterSamples | Measure-Object -Property CookedValue -Average).Average
                Write-Output "IO活动: $([math]::Round($avgIO, 2)) 字节/秒"
            }
            
        } else {
            Write-Output "OneDrive进程未运行"
        }
    } catch {
        Write-Output "检查失败: $($_.Exception.Message)"
    }
    '''
    
    try:
        cmd = ['powershell', '-Command', powershell_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.stdout.strip()
    except Exception as e:
        return f"网络活动检查失败: {e}"

def check_file_level_sync_status():
    """检查具体文件的同步状态"""
    print("=== 检查文件级别的同步状态 ===")
    
    onedrive_path = os.path.expanduser("~\\OneDrive")
    
    powershell_script = f'''
    try {{
        $OneDrivePath = "{onedrive_path}"
        
        # 获取最近修改的文件
        $recentFiles = Get-ChildItem $OneDrivePath -File -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 10
        
        $Shell = New-Object -ComObject Shell.Application
        
        foreach ($file in $recentFiles) {{
            $namespace = $Shell.NameSpace($file.Directory.FullName)
            $item = $namespace.ParseName($file.Name)
            
            # 获取文件的详细状态信息
            $status = $namespace.getDetailsOf($item, 303)  # 云端状态
            $syncStatus = $namespace.getDetailsOf($item, 305)  # 同步状态
            
            Write-Output "文件: $($file.Name)"
            Write-Output "  修改时间: $($file.LastWriteTime)"
            Write-Output "  云端状态: $status"
            Write-Output "  同步状态: $syncStatus"
            Write-Output "  大小: $([math]::Round($file.Length / 1KB, 2)) KB"
            Write-Output ""
        }}
    }} catch {{
        Write-Output "文件状态检查失败: $($_.Exception.Message)"
    }}
    '''
    
    try:
        cmd = ['powershell', '-Command', powershell_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        print(result.stdout)
    except Exception as e:
        print(f"文件状态检查失败: {e}")

def monitor_onedrive_activity():
    """综合监控OneDrive活动"""
    print("=== OneDrive活动综合监控 ===\n")
    
    for i in range(6):  # 监控30秒
        print(f"--- 第{i+1}次检查 ({time.strftime('%H:%M:%S')}) ---")
        
        # 检查网络活动
        network_info = check_onedrive_network_activity()
        print(f"网络活动: {network_info}")
        
        # 检查文件夹状态
        try:
            result = subprocess.run([
                'python', 'onedrive_controller.py', 'sync-status'
            ], capture_output=True, text=True, timeout=10)
            print(f"API状态: {result.stdout.strip()}")
        except:
            print("API状态: 检查失败")
        
        print()
        
        if i < 5:  # 最后一次不等待
            time.sleep(5)

def test_sync_detection_with_new_file():
    """创建新文件测试同步检测"""
    print("=== 创建新文件测试同步检测 ===\n")
    
    onedrive_path = os.path.expanduser("~\\OneDrive")
    test_file = os.path.join(onedrive_path, f"sync_test_{int(time.time())}.txt")
    
    try:
        # 创建测试文件
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("这是一个同步测试文件\n" * 1000)  # 约20KB
        
        print(f"创建测试文件: {test_file}")
        
        # 立即检查状态
        for i in range(5):
            print(f"\n检查 {i+1}/5:")
            
            # 检查文件本身的状态
            powershell_script = f'''
            try {{
                $testFile = "{test_file}"
                if (Test-Path $testFile) {{
                    $shell = New-Object -ComObject Shell.Application
                    $namespace = $shell.NameSpace((Split-Path $testFile))
                    $item = $namespace.ParseName((Split-Path $testFile -Leaf))
                    
                    $status = $namespace.getDetailsOf($item, 303)
                    Write-Output "文件状态: $status"
                }} else {{
                    Write-Output "文件不存在"
                }}
            }} catch {{
                Write-Output "检查失败: $($_.Exception.Message)"
            }}
            '''
            
            cmd = ['powershell', '-Command', powershell_script]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            print(f"  文件状态: {result.stdout.strip()}")
            
            # 检查整体状态
            try:
                result = subprocess.run([
                    'python', 'onedrive_controller.py', 'sync-status'
                ], capture_output=True, text=True, timeout=10)
                print(f"  整体状态: {result.stdout.strip()}")
            except:
                print("  整体状态: 检查失败")
            
            time.sleep(3)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n已删除测试文件: {test_file}")
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    check_file_level_sync_status()
    test_sync_detection_with_new_file()
    monitor_onedrive_activity()