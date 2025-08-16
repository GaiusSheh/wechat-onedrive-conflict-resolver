import os
import random
import string
import time

def generate_random_string(length):
    """生成指定长度的随机字符串"""
    characters = string.ascii_letters + string.digits + string.punctuation + ' \n'
    return ''.join(random.choice(characters) for _ in range(length))

def create_large_test_file(target_size_mb=5):
    """创建指定大小的测试文件"""
    # OneDrive路径
    onedrive_path = os.path.expanduser("~\\OneDrive")
    test_file_path = os.path.join(onedrive_path, "test_onedrive.txt")
    
    if not os.path.exists(onedrive_path):
        print(f"错误：OneDrive路径不存在: {onedrive_path}")
        return None
    
    print(f"正在创建 {target_size_mb}MB 的测试文件: {test_file_path}")
    
    # 目标字节数
    target_bytes = target_size_mb * 1024 * 1024
    
    try:
        with open(test_file_path, 'w', encoding='utf-8') as f:
            written_bytes = 0
            chunk_size = 100000  # 每次写入10万字符
            
            while written_bytes < target_bytes:
                # 生成随机字符串块
                chunk = generate_random_string(chunk_size)
                f.write(chunk)
                
                written_bytes += len(chunk.encode('utf-8'))
                
                # 显示进度
                progress = (written_bytes / target_bytes) * 100
                print(f"\r进度: {progress:.1f}% ({written_bytes / 1024 / 1024:.1f}MB)", end='', flush=True)
        
        print(f"\n✅ 测试文件创建完成!")
        
        # 获取实际文件大小
        actual_size = os.path.getsize(test_file_path)
        print(f"文件路径: {test_file_path}")
        print(f"文件大小: {actual_size / 1024 / 1024:.2f} MB")
        
        return test_file_path
        
    except Exception as e:
        print(f"\n❌ 创建文件失败: {e}")
        return None

def monitor_sync_status(duration_seconds=60):
    """监控OneDrive同步状态一段时间"""
    print(f"\n开始监控OneDrive同步状态 ({duration_seconds}秒)...")
    
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        # 调用我们的OneDrive控制器检查状态
        try:
            import subprocess
            result = subprocess.run([
                'python', 'onedrive_controller.py', 'sync-status'
            ], capture_output=True, text=True, timeout=10)
            
            status_output = result.stdout.strip()
            elapsed = int(time.time() - start_time)
            
            print(f"[{elapsed:02d}s] {status_output}")
            
            # 如果显示同步完成，可以提前结束监控
            if "同步已完成" in status_output:
                consecutive_complete = getattr(monitor_sync_status, 'consecutive_complete', 0) + 1
                monitor_sync_status.consecutive_complete = consecutive_complete
                
                if consecutive_complete >= 3:  # 连续3次显示完成
                    print("✅ 检测到同步完成，监控结束")
                    break
            else:
                monitor_sync_status.consecutive_complete = 0
            
        except Exception as e:
            print(f"[{elapsed:02d}s] 检查状态失败: {e}")
        
        time.sleep(5)  # 每5秒检查一次

def cleanup_test_file():
    """清理测试文件"""
    onedrive_path = os.path.expanduser("~\\OneDrive")
    test_file_path = os.path.join(onedrive_path, "test_onedrive.txt")
    
    if os.path.exists(test_file_path):
        try:
            os.remove(test_file_path)
            print(f"✅ 已删除测试文件: {test_file_path}")
        except Exception as e:
            print(f"❌ 删除测试文件失败: {e}")
    else:
        print("测试文件不存在，无需删除")

def main():
    print("=== OneDrive同步测试工具 ===\n")
    
    # 检查当前OneDrive状态
    print("1. 检查当前OneDrive状态...")
    try:
        import subprocess
        result = subprocess.run([
            'python', 'onedrive_controller.py', 'sync-status'
        ], capture_output=True, text=True, timeout=10)
        print(f"当前状态: {result.stdout.strip()}")
    except Exception as e:
        print(f"检查状态失败: {e}")
    
    print("\n2. 创建大型测试文件...")
    test_file = create_large_test_file(target_size_mb=5)
    
    if test_file:
        print("\n3. 监控同步状态...")
        monitor_sync_status(duration_seconds=120)  # 监控2分钟
        
        print("\n4. 清理测试文件...")
        cleanup_test_file()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()