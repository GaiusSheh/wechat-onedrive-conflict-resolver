import psutil
import subprocess
import sys
import time
import os
import threading
import winreg
from config_manager import ConfigManager

# 导入统一日志系统
from core.logger_helper import logger

# 2025-08-08 性能优化：缓存机制
_onedrive_status_cache = {
    'result': None,
    'timestamp': 0,
    'cache_duration': 5.0  # 缓存5秒
}

# 2025-08-08 架构优化：线程安全机制
_onedrive_query_lock = threading.Lock()  # 防止并发查询
_onedrive_cache_lock = threading.Lock()  # 保护缓存操作

def find_onedrive_processes_optimized():
    """高效查找OneDrive进程 - Windows系统命令优化版 (2025-08-08)
    
    使用Windows tasklist命令直接查询OneDrive进程，避免遍历所有系统进程。
    预期性能：从5-27秒优化到0.1-0.5秒。
    """
    onedrive_processes = []
    
    try:
        # Phase 2优化：OneDrive专项优化，同时查询多种可能的OneDrive进程
        # OneDrive可能以不同名称运行：OneDrive.exe, Microsoft.SharePoint.exe等
        onedrive_names = ['OneDrive.exe', 'Microsoft.SharePoint.exe']
        
        for process_name in onedrive_names:
            result = subprocess.run([
                'tasklist', '/fi', f'imagename eq {process_name}', '/fo', 'csv'
            ], capture_output=True, text=True, timeout=2, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                # 跳过标题行，处理数据行
                for line in lines[1:] if len(lines) > 1 else []:
                    if process_name in line:
                        try:
                            # 解析CSV格式: "进程名","PID","会话名","会话#","内存使用"
                            parts = [p.strip(' "') for p in line.split(',')]
                            if len(parts) >= 2:
                                pid_str = parts[1]
                                pid = int(pid_str)
                                # Phase 2优化：轻量级PID验证，避免立即创建Process对象
                                try:
                                    # 快速验证PID是否仍然存在且可访问
                                    if psutil.pid_exists(pid):
                                        # 只有确认PID有效时才创建Process对象
                                        proc = psutil.Process(pid)
                                        # 验证进程名称（支持多种OneDrive进程名）
                                        proc_name = proc.name().lower()
                                        if proc_name in ['onedrive.exe', 'microsoft.sharepoint.exe']:
                                            onedrive_processes.append(proc)
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    # PID已失效或无权限，跳过
                                    continue
                        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
                            # 忽略无效的PID或无权限访问的进程
                            continue
        
        # 如果找到了进程，返回结果
        return onedrive_processes
        
    except subprocess.TimeoutExpired:
        # 命令超时，记录并回退到psutil方法
        try:
            from core.logger_helper import logger
            logger.warning("OneDrive tasklist命令超时，回退到psutil方法")
        except:
            # logger.warning("OneDrive tasklist命令超时，回退到psutil方法")
            pass
        return find_onedrive_processes_fallback()
        
    except Exception as e:
        # 其他异常，回退到psutil方法
        try:
            from core.logger_helper import logger
            logger.warning(f"OneDrive tasklist命令失败: {e}，回退到psutil方法")
        except:
            # logger.warning(f"OneDrive tasklist命令失败: {e}，回退到psutil方法")
            pass
        return find_onedrive_processes_fallback()

def find_onedrive_processes_fallback():
    """回退方案：使用psutil查询 - 保留原有实现"""
    onedrive_processes = []
    try:
        # 性能优化：使用process_iter一次性获取所需信息  
        # 避免为每个PID单独创建Process对象和调用name()方法
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info.get('name', '') or ''
                # OneDrive进程名称通常是 OneDrive.exe
                if name.lower() == 'onedrive.exe':
                    onedrive_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        # logger.warning(f"OneDrive高效查找失败，回退到兼容模式: {e}")
        pass
        # OLD VERSION FALLBACK: 保留原始逻辑作为备用
        for pid in psutil.pids():
            try:
                proc = psutil.Process(pid)
                name = proc.name()
                if name.lower() == 'onedrive.exe':
                    onedrive_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return onedrive_processes

def find_onedrive_processes():
    """查找所有OneDrive进程（线程安全优化版 - 2025-08-08）
    
    使用线程锁防止并发查询，优先使用系统命令，性能大幅提升。
    """
    with _onedrive_query_lock:
        return find_onedrive_processes_optimized()

def is_onedrive_running(force_refresh=False):
    """检查OneDrive是否正在运行（线程安全智能缓存版 - 2025-08-08）
    
    Args:
        force_refresh (bool): 是否强制刷新，忽略缓存（用于用户操作后的实时反馈）
    
    使用5秒缓存机制 + 线程安全保护，大幅提升响应速度。
    预期性能：缓存命中<10ms，优化查询0.1-0.5秒（而非之前的5-27秒）
    """
    global _onedrive_status_cache
    
    with _onedrive_cache_lock:
        current_time = time.time()
        cache_age = current_time - _onedrive_status_cache['timestamp']
        
        # 如果缓存还有效且不强制刷新，直接返回缓存结果
        if not force_refresh and cache_age < _onedrive_status_cache['cache_duration'] and _onedrive_status_cache['result'] is not None:
            return _onedrive_status_cache['result']
        
        # 缓存过期或强制刷新，重新检查状态（使用优化的查询方法）
        result = len(find_onedrive_processes()) > 0
        
        # 更新缓存
        _onedrive_status_cache['result'] = result
        _onedrive_status_cache['timestamp'] = current_time
        
        return result

def clear_onedrive_status_cache():
    """清理OneDrive状态缓存，强制下次检查时重新查询（线程安全版）"""
    global _onedrive_status_cache
    with _onedrive_cache_lock:
        _onedrive_status_cache['result'] = None
        _onedrive_status_cache['timestamp'] = 0

def get_onedrive_status():
    """获取OneDrive状态"""
    processes = find_onedrive_processes()
    if processes:
        try:
            return {
                'running': True,
                'process_count': len(processes),
                'processes': [{'pid': proc.pid, 'name': proc.info['name'], 'exe': proc.info.get('exe', 'Unknown')} 
                             for proc in processes]
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {'running': False}
    else:
        return {'running': False}

def pause_onedrive_sync():
    """暂停OneDrive同步（通过停止进程实现）"""
    if not is_onedrive_running():
        # logger.info("OneDrive未运行，无需暂停")
        return True
    
    # logger.info("正在暂停OneDrive同步...")
    return stop_onedrive()

def resume_onedrive_sync():
    """恢复OneDrive同步（异步版本 - 2025-08-08 Phase 2优化）
    
    立即启动OneDrive并返回，不等待启动确认。
    让GUI的状态更新线程自然地检测到OneDrive运行状态变化。
    """
    try:
        # 查找OneDrive安装路径
        onedrive_paths = [
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\OneDrive\\OneDrive.exe"),
            "C:\\Program Files\\Microsoft OneDrive\\OneDrive.exe",
            "C:\\Program Files (x86)\\Microsoft OneDrive\\OneDrive.exe"
        ]
        
        onedrive_path = None
        for path in onedrive_paths:
            if os.path.exists(path):
                onedrive_path = path
                break
        
        if not onedrive_path:
            # logger.error("未找到OneDrive安装路径")
            return False
        
        # logger.info(f"正在启动OneDrive（后台模式）：{onedrive_path}")
        subprocess.Popen([onedrive_path, "/background"])
        
        # Phase 2优化：立即返回成功，不等待确认
        # GUI状态更新线程会在几秒内自动检测到OneDrive运行
        # logger.info("OneDrive启动命令已执行")
        return True
        
    except Exception as e:
        # logger.error(f"恢复OneDrive同步时发生错误：{e}")
        return False

def resume_onedrive_sync_old():
    """恢复OneDrive同步（同步版本 - 保留原有实现作为备用）
    
    等待确认OneDrive启动成功后才返回。
    """
    try:
        # 查找OneDrive安装路径
        onedrive_paths = [
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\OneDrive\\OneDrive.exe"),
            "C:\\Program Files\\Microsoft OneDrive\\OneDrive.exe",
            "C:\\Program Files (x86)\\Microsoft OneDrive\\OneDrive.exe"
        ]
        
        onedrive_path = None
        for path in onedrive_paths:
            if os.path.exists(path):
                onedrive_path = path
                break
        
        if not onedrive_path:
            # logger.error("未找到OneDrive安装路径")
            return False
        
        # logger.info(f"正在启动OneDrive（后台模式）：{onedrive_path}")
        subprocess.Popen([onedrive_path, "/background"])
        
        # 等待3秒钟检查是否启动成功
        # logger.info("等待OneDrive启动...")
        for i in range(3, 0, -1):
            # print(f"检查启动状态，剩余 {i} 秒...", end='\r')
            time.sleep(1)
            if is_onedrive_running():
                # logger.info("OneDrive启动成功")
                return True
        
        # 最后检查一次
        if is_onedrive_running():
            # logger.info("OneDrive启动成功")
            return True
        else:
            # logger.warning("OneDrive可能启动失败，请手动检查")
            return False
        
    except Exception as e:
        # logger.error(f"恢复OneDrive同步时发生错误：{e}")
        return False

def stop_onedrive():
    """停止OneDrive进程"""
    onedrive_processes = find_onedrive_processes()
    if not onedrive_processes:
        # logger.info("OneDrive未运行")
        return True
    
    # logger.info(f"找到 {len(onedrive_processes)} 个OneDrive进程")
    
    for proc in onedrive_processes:
        try:
            # logger.info(f"正在停止OneDrive进程 (PID: {proc.pid})")
            proc.terminate()
        except psutil.NoSuchProcess:
            # logger.info(f"进程 {proc.pid} 已经停止")
            pass
        except psutil.AccessDenied:
            # logger.error(f"没有权限停止进程 {proc.pid}，请以管理员身份运行")
            pass
        except Exception as e:
            # logger.error(f"停止进程 {proc.pid} 时发生错误：{e}")
            pass
    
    # 等待进程退出
    # logger.info("等待OneDrive进程退出...")
    time.sleep(3)
    
    # 检查是否还有进程在运行
    remaining_processes = find_onedrive_processes()
    if remaining_processes:
        # logger.warning(f"还有 {len(remaining_processes)} 个进程未退出，强制结束...")
        for proc in remaining_processes:
            try:
                proc.kill()
                proc.wait(timeout=5)
                # logger.info(f"强制结束进程 {proc.pid}")
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                pass
            except Exception as e:
                # logger.error(f"强制结束进程 {proc.pid} 失败：{e}")
                pass
    
    # 最终检查
    final_processes = find_onedrive_processes()
    if not final_processes:
        # logger.info("所有OneDrive进程已成功停止")
        return True
    else:
        # logger.warning(f"仍有 {len(final_processes)} 个OneDrive进程在运行")
        return False

def wait_for_sync_complete(wait_minutes=None, log_callback=None):
    """等待OneDrive同步完成（从配置文件读取等待时间）"""
    # 判断是GUI环境还是命令行环境
    is_gui_mode = log_callback is not None
    
    def log_message(msg, level="INFO"):
        if log_callback:
            # GUI环境：可以使用emoji和彩色文本
            log_callback(msg, level)
        else:
            # 命令行环境：使用纯文本
            logger.info(msg)
    
    if not is_onedrive_running():
        log_message("OneDrive未运行，无需等待同步")
        return True
    
    # 如果没有指定等待时间，从配置文件读取
    if wait_minutes is None:
        try:
            config = ConfigManager()
            wait_minutes = config.get_sync_wait_minutes()
        except:
            wait_minutes = 5  # 默认5分钟
    
    wait_seconds = wait_minutes * 60
    log_message(f"等待OneDrive同步完成，等待 {wait_minutes} 分钟...")
    log_message("倒计时开始（每10秒更新一次）:")
    
    # 每10秒更新一次倒计时
    for remaining in range(wait_seconds, 0, -10):
        minutes = remaining // 60
        seconds = remaining % 60
        
        if is_gui_mode:
            # GUI环境：使用emoji
            log_message(f"⏱️ 剩余时间: {minutes}分{seconds}秒")
        else:
            # 命令行环境：纯文本
            log_message(f"剩余时间: {minutes}分{seconds}秒")
        
        # 最后10秒时每秒更新
        if remaining <= 10:
            for i in range(remaining, 0, -1):
                if is_gui_mode:
                    log_message(f"⏱️ 剩余时间: 0分{i}秒")
                else:
                    log_message(f"剩余时间: 0分{i}秒")
                time.sleep(1)
            break
        else:
            time.sleep(10)
    
    if is_gui_mode:
        log_message("⏰ 等待时间结束，OneDrive同步应该已完成")
    else:
        log_message("等待时间结束，OneDrive同步应该已完成")
    return True

def start_onedrive():
    """启动OneDrive"""
    if is_onedrive_running():
        # logger.info("OneDrive已经在运行")
        return True
    
    return resume_onedrive_sync()

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python onedrive_controller.py start    # 启动OneDrive")
        print("  python onedrive_controller.py stop     # 停止OneDrive")
        print("  python onedrive_controller.py pause    # 暂停OneDrive同步")
        print("  python onedrive_controller.py resume   # 恢复OneDrive同步")
        print("  python onedrive_controller.py status   # 查看OneDrive状态")
        print("  python onedrive_controller.py wait-sync   # 等待同步完成（5分钟）")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        start_onedrive()
    elif command == 'stop':
        stop_onedrive()
    elif command == 'pause':
        pause_onedrive_sync()
    elif command == 'resume':
        resume_onedrive_sync()
    elif command == 'status':
        status = get_onedrive_status()
        if status['running']:
            print(f"OneDrive正在运行，共有 {status['process_count']} 个进程:")
            for proc in status['processes']:
                print(f"  PID: {proc['pid']}, 进程名: {proc['name']}")
                print(f"  路径: {proc['exe']}")
        else:
            print("OneDrive未运行")
    elif command == 'wait-sync':
        wait_for_sync_complete()
    else:
        print(f"未知命令: {command}")
        print("支持的命令: start, stop, pause, resume, status, wait-sync")
        sys.exit(1)

if __name__ == "__main__":
    main()