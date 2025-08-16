import subprocess
import sys
import time
import os
from config_manager import ConfigManager
from debug_control.debug_config import SYNC_DEBUG_ENABLED

def get_python_executable():
    """获取当前Python可执行文件路径"""
    return sys.executable

def run_command(script, command, description, timeout=60):
    """运行命令并返回结果"""
    try:
        # logger.info(f"{description}...")
        python_exe = get_python_executable()
        
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(script):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if script.startswith('core/'):
                # 去掉core/前缀，因为我们已经在core目录下
                script = script[5:]
            script_path = os.path.join(script_dir, script)
        else:
            script_path = script
        
        result = subprocess.run([
            python_exe, script_path, command
        ], capture_output=True, text=True, timeout=timeout)
        
        # print(result.stdout.strip())  # Keep subprocess output
        
        if result.stderr:
            # logger.warning(f"警告: {result.stderr.strip()}")
            pass
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        # logger.error(f"执行超时: {description}")
        return False
    except Exception as e:
        # logger.error(f"执行失败: {description} - {e}")
        return False

def wait_with_countdown(seconds, message):
    """带倒计时的等待"""
    # logger.info(f"{message}")
    for i in range(seconds, 0, -1):
        # print(f"等待 {i} 秒后继续...", end='\r')
        sys.stdout.flush()  # 强制刷新输出缓冲区
        time.sleep(1)
    # print(" " * 30, end='\r')  # 清除倒计时显示

def run_full_sync_workflow():
    """执行完整的微信OneDrive同步流程（命令行版本）"""
    # logger.info("="*60)
    print("           微信 OneDrive 冲突解决工具")
    # logger.info("="*60)
    print("\n开始执行完整同步流程:")
    print("1. 停止微信")
    print("2. 重启OneDrive")  
    print("3. 等待OneDrive同步完成(5分钟)")
    print("4. 重启微信")
    print("\n按 Ctrl+C 可随时取消")
    
    wait_with_countdown(3, "3秒后开始执行...")
    
    # 步骤1: 停止微信
    print("\n" + "="*50)
    print("步骤 1/4: 停止微信")
    print("="*50)
    
    if not run_command('core/wechat_controller.py', 'stop', '正在停止微信'):
        print("[X] 停止微信失败，流程终止")
        return False
    
    wait_with_countdown(2, "微信已停止，等待2秒...")
    
    # 步骤2: 重启OneDrive
    print("\n" + "="*50)
    print("步骤 2/4: 重启OneDrive")
    print("="*50)
    
    # 先停止OneDrive
    if not run_command('core/onedrive_controller.py', 'pause', '正在停止OneDrive'):
        print("[!] 停止OneDrive失败，但继续执行")
    
    wait_with_countdown(3, "等待OneDrive完全停止...")
    
    # 重启OneDrive
    if not run_command('core/onedrive_controller.py', 'resume', '正在启动OneDrive'):
        print("[X] 启动OneDrive失败，流程终止")
        return False
    
    wait_with_countdown(3, "OneDrive已启动，等待3秒让其稳定...")
    
    # 步骤3: 等待同步完成
    print("\n" + "="*50)
    print("步骤 3/4: 等待OneDrive同步完成")
    print("="*50)
    
    # 从配置文件读取等待时间并设置相应的超时
    try:
        config = ConfigManager()
        wait_minutes = config.get_sync_wait_minutes()
        sync_timeout = (wait_minutes * 60) + 100  # 等待时间 + 100秒缓冲
        print(f"开始{wait_minutes}分钟同步等待...")
    except:
        wait_minutes = 5
        sync_timeout = 400
        print("开始5分钟同步等待...")
    
    if not run_command('core/onedrive_controller.py', 'wait-sync', '等待OneDrive同步完成', timeout=sync_timeout):
        print("[!] 等待同步过程中出现问题，但继续执行")
    
    # 步骤4: 重启微信
    print("\n" + "="*50)
    print("步骤 4/4: 重启微信")
    print("="*50)
    
    if not run_command('wechat_controller.py', 'start', '正在启动微信'):
        print("[X] 启动微信失败")
        print("请手动启动微信")
        return False
    
    # 提示用户登录
    print("\n[提示] 微信已重新启动")
    print("[提示] 如需登录，请手动点击微信窗口中的登录按钮")
    print("[提示] 同步流程已完成，OneDrive冲突已解决")
    
    print("\n" + "="*60)
    print("[OK] 同步流程完成!")
    # logger.info("="*60)
    print("\n微信和OneDrive应该已经正常运行")
    print("OneDrive文件冲突问题已解决")
    
    return True

def check_status():
    """检查当前微信和OneDrive状态"""
    print("="*50)
    print("当前系统状态")
    print("="*50)
    
    print("\n微信状态:")
    run_command('core/wechat_controller.py', 'status', '检查微信状态')
    
    print("\nOneDrive状态:")
    run_command('core/onedrive_controller.py', 'status', '检查OneDrive状态')

def main():
    if len(sys.argv) < 2:
        print("微信OneDrive冲突解决工具")
        print("\n用法:")
        print("  python sync_workflow.py run     # 执行完整同步流程")
        print("  python sync_workflow.py status  # 检查当前状态")
        print("\n完整流程说明:")
        print("1. 停止微信进程")
        print("2. 重启OneDrive进程") 
        print("3. 等待OneDrive同步完成(5分钟)")
        print("4. 重启微信进程")
        print("\n注意: 整个流程大约需要6-7分钟")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == 'run':
            success = run_full_sync_workflow()
            sys.exit(0 if success else 1)
        elif command == 'status':
            check_status()
        else:
            print(f"未知命令: {command}")
            print("支持的命令: run, status")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n[!] 用户取消操作")
        print("流程已中断，请检查微信和OneDrive状态")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] 执行过程中发生错误: {e}")
        sys.exit(1)

def run_full_sync_workflow_gui(log_callback=None):
    """执行完整的微信OneDrive同步流程（GUI版本）
    
    Args:
        log_callback: 日志回调函数，用于GUI显示日志
    """
    def log_message(message, level="INFO"):
        """统一的日志输出函数"""
        if log_callback:
            log_callback(message, level)
    
    # 使用统一的调试开关
    debug_mode = SYNC_DEBUG_ENABLED
    
    try:
        log_message("="*60)
        log_message("           微信 OneDrive 冲突解决工具")
        log_message("="*60)
        
        if debug_mode:
            log_message("🧪 调试模式：短路同步流程（3秒后完成）")
        
        log_message("1. 停止微信")
        log_message("2. 重启OneDrive")  
        log_message("3. 等待OneDrive同步完成")
        log_message("4. 重启微信")
        
        # 调试模式：短路同步流程，直接等3秒返回成功
        if debug_mode:
            log_message("🧪 调试模式：3秒后直接返回成功")
            time.sleep(3)
            log_message("")
            log_message("🚀 调试：跳过所有实际步骤，直接模拟成功")
        else:
            # === 完整同步流程 ===
            # 步骤1: 停止微信
            log_message("")
            log_message("="*50)
            log_message("步骤 1/4: 停止微信")
            log_message("="*50)
            
            log_message("正在停止微信...")
            from wechat_controller import stop_wechat
            if not stop_wechat():
                log_message("[X] 停止微信失败，流程终止", "ERROR")
                return False
            
            log_message("微信已停止，等待2秒...")
            time.sleep(2)
            
            # 步骤2: 重启OneDrive
            log_message("")
            log_message("="*50)
            log_message("步骤 2/4: 重启OneDrive")
            log_message("="*50)
            
            # 先停止OneDrive
            log_message("正在停止OneDrive...")
            from onedrive_controller import pause_onedrive_sync
            if not pause_onedrive_sync():
                log_message("[!] 停止OneDrive失败，但继续执行", "WARNING")
            
            log_message("等待OneDrive完全停止...")
            time.sleep(3)
            
            # 重启OneDrive
            log_message("正在启动OneDrive...")
            from onedrive_controller import resume_onedrive_sync
            if not resume_onedrive_sync():
                log_message("[X] 启动OneDrive失败，流程终止", "ERROR")
                return False
            
            log_message("OneDrive已启动，等待3秒让其稳定...")
            time.sleep(3)
            
            # 步骤3: 等待同步完成
            log_message("")
            log_message("="*50)
            log_message("步骤 3/4: 等待OneDrive同步完成")
            log_message("="*50)
            
            # 从配置文件读取等待时间
            try:
                from config_manager import ConfigManager
                config = ConfigManager()
                wait_minutes = config.get_sync_wait_minutes()
                log_message(f"开始{wait_minutes}分钟同步等待...")
            except:
                wait_minutes = 5
                log_message("开始5分钟同步等待...")
            
            log_message("等待OneDrive同步完成...")
            from onedrive_controller import wait_for_sync_complete
            if not wait_for_sync_complete(wait_minutes, log_callback=log_message):
                log_message("[!] 等待同步过程中出现问题，但继续执行", "WARNING")
            
            # 步骤4: 重启微信
            log_message("")
            log_message("="*50)
            log_message("步骤 4/4: 重启微信")
            log_message("="*50)
            
            log_message("正在启动微信...")
            from wechat_controller import start_wechat
            if not start_wechat():
                log_message("[X] 启动微信失败", "ERROR")
                log_message("请手动启动微信", "WARNING")
                return False
        
        # 提示用户登录
        log_message("")
        log_message("[提示] 微信已重新启动", "SUCCESS")
        log_message("[提示] 如需登录，请手动点击微信窗口中的登录按钮")
        log_message("[提示] 同步流程已完成，OneDrive冲突已解决", "SUCCESS")
        
        log_message("")
        log_message("="*60)
        log_message("[OK] 同步流程完成!", "SUCCESS")
        log_message("="*60)
        log_message("微信和OneDrive应该已经正常运行")
        log_message("OneDrive文件冲突问题已解决")
        
        return True
        
    except Exception as e:
        log_message(f"执行过程中发生错误: {e}", "ERROR")
        return False

if __name__ == "__main__":
    main()