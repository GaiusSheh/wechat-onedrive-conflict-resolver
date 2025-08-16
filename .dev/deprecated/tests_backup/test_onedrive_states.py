import subprocess
import os

def test_onedrive_sync_states():
    """测试OneDrive的不同同步状态"""
    print("=== 测试OneDrive同步状态检测 ===\n")
    
    onedrive_path = os.path.expanduser("~\\OneDrive")
    
    # 测试脚本获取更多状态信息
    powershell_script = f'''
    try {{
        $OneDrivePath = "{onedrive_path}"
        if (Test-Path $OneDrivePath) {{
            $Shell = New-Object -ComObject Shell.Application
            $Namespace = $Shell.NameSpace((Split-Path $OneDrivePath))
            $Item = $Namespace.ParseName((Split-Path $OneDrivePath -Leaf))
            
            Write-Output "=== OneDrive文件夹状态 ==="
            # 获取状态相关的列信息
            for ($i = 300; $i -le 320; $i++) {{
                $detail = $Namespace.getDetailsOf($Item, $i)
                if ($detail -and $detail.Trim() -ne "") {{
                    $columnName = $Namespace.getDetailsOf($null, $i)
                    Write-Output "列$i ($columnName): $detail"
                }}
            }}
            
            Write-Output "`n=== OneDrive子文件夹状态 ==="
            # 检查子文件夹的状态
            $subItems = Get-ChildItem $OneDrivePath -Directory | Select-Object -First 3
            foreach ($subItem in $subItems) {{
                $subNamespace = $Shell.NameSpace($subItem.FullName)
                $parentNamespace = $Shell.NameSpace($subItem.Directory.FullName) 
                $item = $parentNamespace.ParseName($subItem.Name)
                
                $status = $parentNamespace.getDetailsOf($item, 303)
                Write-Output "$($subItem.Name): $status"
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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        
        print("输出:")
        print(result.stdout)
        if result.stderr:
            print("错误信息:")
            print(result.stderr)
        
        # 分析状态信息
        output = result.stdout
        if "正在同步" in output or "Syncing" in output.lower():
            print("\n🔄 检测到同步活动")
        elif "最新" in output or "up to date" in output.lower():
            print("\n✅ 同步已完成")
        elif "在此设备上可用" in output:
            print("\n📱 OneDrive在线，状态正常")
        else:
            print("\n❓ 状态未知")
            
    except Exception as e:
        print(f"测试失败: {e}")

def create_test_file_and_check():
    """创建测试文件并检查同步状态变化"""
    print("\n=== 创建测试文件检查状态变化 ===")
    
    try:
        onedrive_path = os.path.expanduser("~\\OneDrive")
        test_file = os.path.join(onedrive_path, "sync_test_file.txt")
        
        # 创建测试文件
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(f"同步测试文件 - 创建时间: {os.popen('echo %TIME%').read().strip()}")
        
        print(f"已创建测试文件: {test_file}")
        
        # 立即检查状态
        powershell_script = f'''
        try {{
            $TestFile = "{test_file}"
            if (Test-Path $TestFile) {{
                $Shell = New-Object -ComObject Shell.Application
                $Namespace = $Shell.NameSpace((Split-Path $TestFile))
                $Item = $Namespace.ParseName((Split-Path $TestFile -Leaf))
                
                $status = $Namespace.getDetailsOf($Item, 303)
                Write-Output "测试文件状态: $status"
            }}
        }} catch {{
            Write-Output "检查测试文件状态失败: $($_.Exception.Message)"
        }}
        '''
        
        cmd = ['powershell', '-Command', powershell_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        print("测试文件状态:")
        print(result.stdout)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print("已删除测试文件")
            
    except Exception as e:
        print(f"测试文件创建失败: {e}")

if __name__ == "__main__":
    test_onedrive_sync_states()
    create_test_file_and_check()