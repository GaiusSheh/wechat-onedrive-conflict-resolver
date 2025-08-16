import subprocess
import os

def debug_onedrive_status_detailed():
    """详细调试OneDrive状态信息"""
    print("=== 详细调试OneDrive状态 ===\n")
    
    onedrive_path = os.path.expanduser("~\\OneDrive")
    
    # 获取更多列的状态信息
    powershell_script = f'''
    try {{
        $OneDrivePath = "{onedrive_path}"
        if (Test-Path $OneDrivePath) {{
            $Shell = New-Object -ComObject Shell.Application
            $Namespace = $Shell.NameSpace((Split-Path $OneDrivePath))
            $Item = $Namespace.ParseName((Split-Path $OneDrivePath -Leaf))
            
            Write-Output "=== OneDrive文件夹所有可用状态信息 ==="
            
            # 检查更多的列（0-350）
            for ($i = 0; $i -le 350; $i++) {{
                $detail = $Namespace.getDetailsOf($Item, $i)
                $columnName = $Namespace.getDetailsOf($null, $i)
                
                if ($detail -and $detail.Trim() -ne "" -and $columnName.Trim() -ne "") {{
                    Write-Output "列$i [$columnName]: $detail"
                }}
            }}
            
            Write-Output "`n=== 检查子文件状态 ==="
            # 检查最近修改的文件状态
            $recentFiles = Get-ChildItem $OneDrivePath -File | Sort-Object LastWriteTime -Descending | Select-Object -First 5
            
            foreach ($file in $recentFiles) {{
                $fileNamespace = $Shell.NameSpace($file.Directory.FullName)
                $fileItem = $fileNamespace.ParseName($file.Name)
                
                Write-Output "文件: $($file.Name)"
                Write-Output "  修改时间: $($file.LastWriteTime)"
                
                # 检查文件的状态信息
                for ($j = 300; $j -le 310; $j++) {{
                    $fileStatus = $fileNamespace.getDetailsOf($fileItem, $j)
                    if ($fileStatus -and $fileStatus.Trim() -ne "") {{
                        $colName = $fileNamespace.getDetailsOf($null, $j)
                        Write-Output "  列$j [$colName]: $fileStatus"
                    }}
                }}
                Write-Output ""
            }}
            
        }} else {{
            Write-Output "OneDrive路径不存在: $OneDrivePath"
        }}
    }} catch {{
        Write-Output "错误: $($_.Exception.Message)"
        Write-Output "详细错误: $($_.Exception)"
    }}
    '''
    
    try:
        cmd = ['powershell', '-Command', powershell_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print("详细状态信息:")
        print(result.stdout)
        
        if result.stderr:
            print("错误信息:")
            print(result.stderr)
            
    except Exception as e:
        print(f"调试失败: {e}")

def check_onedrive_process_activity():
    """检查OneDrive进程的详细活动信息"""
    print("\n=== OneDrive进程活动分析 ===\n")
    
    powershell_script = '''
    try {
        $oneDriveProcesses = Get-Process OneDrive -ErrorAction SilentlyContinue
        
        if ($oneDriveProcesses) {
            foreach ($proc in $oneDriveProcesses) {
                Write-Output "进程ID: $($proc.Id)"
                Write-Output "进程名: $($proc.ProcessName)"
                Write-Output "CPU时间: $($proc.CPU)"
                Write-Output "内存使用: $([math]::Round($proc.WorkingSet / 1MB, 2)) MB"
                Write-Output "句柄数: $($proc.HandleCount)"
                Write-Output "线程数: $($proc.Threads.Count)"
                
                # 检查进程的网络连接
                try {
                    $connections = Get-NetTCPConnection -OwningProcess $proc.Id -ErrorAction SilentlyContinue
                    if ($connections) {
                        Write-Output "网络连接数: $($connections.Count)"
                        $connections | ForEach-Object {
                            Write-Output "  $($_.LocalAddress):$($_.LocalPort) -> $($_.RemoteAddress):$($_.RemotePort) [$($_.State)]"
                        }
                    } else {
                        Write-Output "无网络连接"
                    }
                } catch {
                    Write-Output "无法获取网络连接信息"
                }
                
                Write-Output "---"
            }
        } else {
            Write-Output "OneDrive进程未运行"
        }
    } catch {
        Write-Output "错误: $($_.Exception.Message)"
    }
    '''
    
    try:
        cmd = ['powershell', '-Command', powershell_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        
        print("进程活动信息:")
        print(result.stdout)
        
    except Exception as e:
        print(f"进程分析失败: {e}")

def check_onedrive_registry():
    """检查OneDrive注册表状态信息"""
    print("\n=== OneDrive注册表状态 ===\n")
    
    powershell_script = '''
    try {
        # 检查OneDrive注册表项
        $regPaths = @(
            "HKCU:\\Software\\Microsoft\\OneDrive",
            "HKCU:\\Software\\Microsoft\\OneDrive\\Accounts",
            "HKLM:\\SOFTWARE\\Microsoft\\OneDrive"
        )
        
        foreach ($regPath in $regPaths) {
            if (Test-Path $regPath) {
                Write-Output "注册表路径: $regPath"
                $items = Get-ItemProperty $regPath -ErrorAction SilentlyContinue
                if ($items) {
                    $items.PSObject.Properties | ForEach-Object {
                        if ($_.Name -notlike "PS*") {
                            Write-Output "  $($_.Name): $($_.Value)"
                        }
                    }
                }
                Write-Output ""
            }
        }
    } catch {
        Write-Output "错误: $($_.Exception.Message)"
    }
    '''
    
    try:
        cmd = ['powershell', '-Command', powershell_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        print("注册表信息:")
        print(result.stdout)
        
    except Exception as e:
        print(f"注册表检查失败: {e}")

if __name__ == "__main__":
    debug_onedrive_status_detailed()
    check_onedrive_process_activity()
    check_onedrive_registry()