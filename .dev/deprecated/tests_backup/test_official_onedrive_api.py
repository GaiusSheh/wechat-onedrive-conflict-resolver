import subprocess
import os
import tempfile
import urllib.request

def download_onedrive_lib():
    """下载OneDriveLib.dll"""
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        dll_path = os.path.join(temp_dir, "OneDriveLib.dll")
        
        # OneDriveLib.dll的下载链接（来自微软官方GitHub）
        url = "https://github.com/rodneyviana/ODSyncService/raw/master/OneDriveLib.dll"
        
        print(f"正在下载OneDriveLib.dll到 {dll_path}")
        urllib.request.urlretrieve(url, dll_path)
        
        return dll_path
    except Exception as e:
        print(f"下载OneDriveLib.dll失败: {e}")
        return None

def test_get_odstatus():
    """测试微软官方的Get-ODStatus cmdlet"""
    print("=== 测试微软官方OneDrive API ===\n")
    
    # 先尝试下载OneDriveLib.dll
    dll_path = download_onedrive_lib()
    if not dll_path:
        print("无法下载OneDriveLib.dll，跳过官方API测试")
        return False
    
    try:
        # 测试PowerShell脚本
        powershell_script = f'''
        try {{
            Unblock-File -Path "{dll_path}" -ErrorAction SilentlyContinue
            Import-Module "{dll_path}" -ErrorAction Stop
            
            # 获取OneDrive状态
            $status = Get-ODStatus -Type Personal -ErrorAction Stop
            
            if ($status) {{
                Write-Output "OneDrive状态信息:"
                $status | ForEach-Object {{
                    Write-Output "路径: $($_.LocalPath)"
                    Write-Output "用户: $($_.UserName)" 
                    Write-Output "显示名: $($_.DisplayName)"
                    Write-Output "服务类型: $($_.ServiceType)"
                    Write-Output "状态: $($_.StatusString)"
                    Write-Output "---"
                }}
            }} else {{
                Write-Output "未找到OneDrive状态信息"
            }}
        }} catch {{
            Write-Output "错误: $($_.Exception.Message)"
        }}
        '''
        
        cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', powershell_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print("PowerShell输出:")
        print(result.stdout)
        if result.stderr:
            print("错误信息:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"测试Get-ODStatus失败: {e}")
        return False
    finally:
        # 清理临时文件
        try:
            if dll_path and os.path.exists(dll_path):
                os.remove(dll_path)
        except:
            pass

def test_shell_com_method():
    """测试Shell COM对象方法"""
    print("\n=== 测试Shell COM对象方法 ===\n")
    
    try:
        onedrive_path = os.path.expanduser("~\\OneDrive")
        
        powershell_script = f'''
        try {{
            $OneDrivePath = "{onedrive_path}"
            if (Test-Path $OneDrivePath) {{
                $Shell = New-Object -ComObject Shell.Application
                $Namespace = $Shell.NameSpace((Split-Path $OneDrivePath))
                $Item = $Namespace.ParseName((Split-Path $OneDrivePath -Leaf))
                
                # 尝试获取状态信息（列303通常是状态列）
                $Status = $Namespace.getDetailsOf($Item, 303)
                Write-Output "OneDrive状态: $Status"
                
                # 尝试其他可能的状态列
                for ($i = 300; $i -le 310; $i++) {{
                    $detail = $Namespace.getDetailsOf($Item, $i)
                    if ($detail) {{
                        Write-Output "列$i`: $detail"
                    }}
                }}
            }} else {{
                Write-Output "OneDrive路径不存在: $OneDrivePath"
            }}
        }} catch {{
            Write-Output "错误: $($_.Exception.Message)"
        }}
        '''
        
        cmd = ['powershell', '-Command', powershell_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        print("Shell COM方法输出:")
        print(result.stdout)
        if result.stderr:
            print("错误信息:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"测试Shell COM方法失败: {e}")
        return False

if __name__ == "__main__":
    # 测试官方API
    success1 = test_get_odstatus()
    
    # 测试Shell COM方法
    success2 = test_shell_com_method()
    
    if success1:
        print("\n✅ 官方Get-ODStatus API可用")
    elif success2:
        print("\n✅ Shell COM方法可用")
    else:
        print("\n❌ 两种方法都不可用，可能需要回退到CPU监控方法")