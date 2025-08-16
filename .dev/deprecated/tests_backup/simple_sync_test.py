import subprocess
import os
import time

def get_detailed_onedrive_status():
    """获取详细的OneDrive状态"""
    onedrive_path = os.path.expanduser("~\\OneDrive")
    
    powershell_script = f'''
    $OneDrivePath = "{onedrive_path}"
    $Shell = New-Object -ComObject Shell.Application
    $Namespace = $Shell.NameSpace((Split-Path $OneDrivePath))
    $Item = $Namespace.ParseName((Split-Path $OneDrivePath -Leaf))
    
    # 获取多个状态列
    $status303 = $Namespace.getDetailsOf($Item, 303)
    $status305 = $Namespace.getDetailsOf($Item, 305)
    
    Write-Output "状态303: $status303"
    Write-Output "状态305: $status305"
    '''
    
    try:
        cmd = ['powershell', '-Command', powershell_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception as e:
        return f"检查失败: {e}"

def create_test_file_and_monitor():
    """创建测试文件并监控"""
    onedrive_path = os.path.expanduser("~\\OneDrive")
    test_file = os.path.join(onedrive_path, "sync_test.txt")
    
    print("=== 创建测试文件并监控同步状态 ===\n")
    
    try:
        # 创建一个较大的测试文件（1MB）
        with open(test_file, 'w', encoding='utf-8') as f:
            content = "这是一个同步测试文件。" * 50000  # 约1MB
            f.write(content)
        
        print(f"已创建测试文件: {test_file}")
        print(f"文件大小: {os.path.getsize(test_file) / 1024:.1f} KB\n")
        
        # 监控状态变化
        print("监控状态变化:")
        for i in range(10):
            print(f"第{i+1}次检查:")
            
            # 获取详细状态
            status = get_detailed_onedrive_status()
            print(f"  详细状态: {status}")
            
            # 使用我们的API检查
            try:
                result = subprocess.run([
                    'python', 'onedrive_controller.py', 'sync-status'
                ], capture_output=True, text=True, timeout=5)
                api_status = result.stdout.strip()
                print(f"  API检测: {api_status}")
            except:
                print("  API检测: 失败")
            
            print()
            time.sleep(2)
        
        # 清理
        if os.path.exists(test_file):
            os.remove(test_file)
            print("已删除测试文件")
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    print("当前OneDrive状态:")
    print(get_detailed_onedrive_status())
    print("\n" + "="*50 + "\n")
    
    create_test_file_and_monitor()