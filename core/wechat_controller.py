import psutil
import subprocess
import sys
import time
import os
import threading
try:
    import winreg
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False

# 导入统一日志系统
from core.logger_helper import logger

# 2025-08-08 性能优化：缓存机制
_wechat_status_cache = {
    'result': None,
    'timestamp': 0,
    'cache_duration': 5.0  # 缓存5秒
}

# 2025-08-08 架构优化：线程安全机制
_process_query_lock = threading.Lock()  # 防止并发查询
_cache_lock = threading.Lock()  # 保护缓存操作

# OLD VERSION: 2025-08-08 - 原始进程查找实现（性能较慢）
# def find_wechat_processes():
#     """查找所有微信进程（优化版 - 减少进程遍历耗时）"""
#     wechat_processes = []
#     try:
#         # 使用pids()而不是process_iter()，然后只检查指定进程
#         # 这样可以避免遍历所有进程的详细信息
#         for pid in psutil.pids():
#             try:
#                 proc = psutil.Process(pid)
#                 name = proc.name()
#                 # 微信的主进程名称是 Weixin.exe
#                 if name.lower() == 'weixin.exe':
#                     wechat_processes.append(proc)
#             except (psutil.NoSuchProcess, psutil.AccessDenied):
#                 continue
#     except Exception as e:
#         # 如果优化方法失败，回退到原方法
#         print(f"优化查找失败，使用备用方法: {e}")
#         for proc in psutil.process_iter(['pid', 'name']):
#             try:
#                 name = proc.info['name'] or ''
#                 if name.lower() == 'weixin.exe':
#                     wechat_processes.append(proc)
#             except (psutil.NoSuchProcess, psutil.AccessDenied):
#                 continue
#     return wechat_processes

def find_wechat_processes_optimized():
    """高效查找微信进程 - Windows系统命令优化版 (2025-08-08)
    
    使用Windows tasklist命令直接查询微信进程，避免遍历所有系统进程。
    预期性能：从5-27秒优化到0.1-0.5秒。
    """
    wechat_processes = []
    
    try:
        # 使用Windows tasklist命令直接查询微信进程
        result = subprocess.run([
            'tasklist', '/fi', 'imagename eq Weixin.exe', '/fo', 'csv'
        ], capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            # 跳过标题行，处理数据行
            for line in lines[1:] if len(lines) > 1 else []:
                if 'Weixin.exe' in line:
                    try:
                        # 解析CSV格式: "进程名","PID","会话名","会话#","内存使用"
                        # 使用简单的分割而不是完整的CSV解析，提高性能
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
                                    # 快速验证进程名称仍然正确（防止PID重用）
                                    if proc.name().lower() == 'weixin.exe':
                                        wechat_processes.append(proc)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                # PID已失效或无权限，跳过
                                continue
                    except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
                        # 忽略无效的PID或无权限访问的进程
                        continue
                        
        return wechat_processes
        
    except subprocess.TimeoutExpired:
        # 命令超时，记录并回退到psutil方法
        try:
            from core.logger_helper import logger
            logger.warning("tasklist命令超时，回退到psutil方法")
        except:
            # logger.warning("tasklist命令超时，回退到psutil方法")
            pass
        return find_wechat_processes_fallback()
        
    except Exception as e:
        # 其他异常（命令不存在、权限问题等），回退到psutil方法
        try:
            from core.logger_helper import logger
            logger.warning(f"tasklist命令失败: {e}，回退到psutil方法")
        except:
            # logger.warning(f"tasklist命令失败: {e}，回退到psutil方法")
            pass
        return find_wechat_processes_fallback()

def find_wechat_processes_fallback():
    """回退方案：使用psutil查询 - 保留原有实现"""
    # 这里是原有的find_wechat_processes实现，重命名为fallback
    wechat_processes = []
    try:
        # 性能优化：使用process_iter一次性获取所需信息
        # 避免为每个PID单独创建Process对象和调用name()方法
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info.get('name', '') or ''
                # 微信的主进程名称是 Weixin.exe
                if name.lower() == 'weixin.exe':
                    wechat_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        # logger.warning(f"高效查找失败，回退到兼容模式: {e}")
        # OLD VERSION FALLBACK: 保留原始逻辑作为备用
        for pid in psutil.pids():
            try:
                proc = psutil.Process(pid)
                name = proc.name()
                if name.lower() == 'weixin.exe':
                    wechat_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return wechat_processes

def find_wechat_processes():
    """查找所有微信进程（线程安全优化版 - 2025-08-08）
    
    使用线程锁防止并发查询，优先使用系统命令，性能大幅提升。
    """
    with _process_query_lock:
        return find_wechat_processes_optimized()

def find_wechat_process():
    """查找微信进程（返回第一个找到的进程，保持向后兼容）"""
    processes = find_wechat_processes()
    return processes[0] if processes else None

# OLD VERSION: 2025-08-08 - 无缓存的实时状态检查
# def is_wechat_running():
#     """检查微信是否正在运行"""
#     return find_wechat_process() is not None

def is_wechat_running(force_refresh=False):
    """检查微信是否正在运行（线程安全智能缓存版 - 2025-08-08）
    
    Args:
        force_refresh (bool): 是否强制刷新，忽略缓存（用于用户操作后的实时反馈）
    
    使用5秒缓存机制 + 线程安全保护，大幅提升响应速度。
    预期性能：缓存命中<10ms，优化查询0.1-0.5秒（而非之前的5-27秒）
    """
    global _wechat_status_cache
    
    with _cache_lock:
        current_time = time.time()
        cache_age = current_time - _wechat_status_cache['timestamp']
        
        # 如果缓存还有效且不强制刷新，直接返回缓存结果
        if not force_refresh and cache_age < _wechat_status_cache['cache_duration'] and _wechat_status_cache['result'] is not None:
            return _wechat_status_cache['result']
        
        # 缓存过期或强制刷新，重新检查状态（使用优化的查询方法）
        result = find_wechat_process() is not None
        
        # 更新缓存
        _wechat_status_cache['result'] = result
        _wechat_status_cache['timestamp'] = current_time
        
        return result

def clear_wechat_status_cache():
    """清理微信状态缓存，强制下次检查时重新查询（线程安全版）"""
    global _wechat_status_cache
    with _cache_lock:
        _wechat_status_cache['result'] = None
        _wechat_status_cache['timestamp'] = 0

def stop_wechat():
    """停止所有微信进程"""
    wechat_processes = find_wechat_processes()
    
    # 在操作完成后清理缓存，确保状态及时更新
    success = False
    if not wechat_processes:
        logger.info("微信未运行")
        return True
    
    logger.info(f"找到 {len(wechat_processes)} 个微信进程")
    success_count = 0
    
    for proc in wechat_processes:
        try:
            logger.info(f"正在停止微信进程 (PID: {proc.pid})")
            proc.terminate()
            success_count += 1
        except psutil.NoSuchProcess:
            logger.debug(f"进程 {proc.pid} 已经停止")
            success_count += 1
        except psutil.AccessDenied:
            logger.error(f"错误：没有权限停止进程 {proc.pid}，请以管理员身份运行")
        except Exception as e:
            logger.error(f"停止进程 {proc.pid} 时发生错误：{e}")
    
    # 等待所有进程优雅退出
    logger.info("等待微信进程退出...")
    time.sleep(3)
    
    # 检查是否还有进程在运行，如果有则强制结束
    remaining_processes = find_wechat_processes()
    if remaining_processes:
        logger.warning(f"还有 {len(remaining_processes)} 个进程未退出，强制结束...")
        for proc in remaining_processes:
            try:
                proc.kill()
                proc.wait(timeout=5)
                logger.info(f"强制结束进程 {proc.pid}")
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                pass
            except Exception as e:
                logger.error(f"强制结束进程 {proc.pid} 失败：{e}")
    
    # 最终检查
    final_processes = find_wechat_processes()
    if not final_processes:
        logger.info("所有微信进程已成功停止")
        # 清理状态缓存，确保下次检查状态时获取最新结果
        clear_wechat_status_cache()
        return True
    else:
        logger.warning(f"仍有 {len(final_processes)} 个微信进程在运行")
        # 也要清理缓存，因为状态可能已经改变
        clear_wechat_status_cache()
        return False

def find_wechat_install_path():
    """查找微信安装路径"""
    wechat_paths = []
    
    # 1. 尝试从注册表查找
    if REGISTRY_AVAILABLE:
        try:
            # 查找卸载注册表项
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall") as uninstall_key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        with winreg.OpenKey(uninstall_key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if "微信" in display_name or "WeChat" in display_name:
                                    try:
                                        install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                        wechat_exe = os.path.join(install_location, "Weixin.exe")
                                        if os.path.exists(wechat_exe):
                                            wechat_paths.append(wechat_exe)
                                    except FileNotFoundError:
                                        pass
                            except FileNotFoundError:
                                pass
                        i += 1
                    except OSError:
                        break
        except Exception as e:
            logger.debug(f"注册表查找失败: {e}")
    
    # 2. 常见的微信安装路径
    common_paths = [
        "C:\\Program Files\\Tencent\\Weixin\\Weixin.exe",
        "C:\\Program Files (x86)\\Tencent\\Weixin\\Weixin.exe",
        os.path.expanduser("~\\AppData\\Roaming\\Tencent\\Weixin\\Weixin.exe"),
        os.path.expanduser("~\\AppData\\Local\\Tencent\\Weixin\\Weixin.exe"),
        "D:\\Program Files\\Tencent\\Weixin\\Weixin.exe",
        "E:\\Program Files\\Tencent\\Weixin\\Weixin.exe"
    ]
    
    wechat_paths.extend(common_paths)
    
    # 返回第一个存在的路径
    for path in wechat_paths:
        if os.path.exists(path):
            return path
    
    return None

def start_wechat(auto_login=False):
    """启动微信（异步版本 - 2025-08-08 Phase 2优化）
    
    立即启动微信并返回，不等待启动确认。
    让GUI的状态更新线程自然地检测到微信运行状态变化。
    用户体验：点击立即响应，状态自然更新。
    """
    if is_wechat_running():
        logger.info("微信已经在运行")
        return True
    
    # 查找微信安装路径
    wechat_path = find_wechat_install_path()
    
    if not wechat_path:
        logger.error("错误：未找到微信安装路径")
        logger.error("请检查微信是否已正确安装")
        return False
    
    try:
        logger.info(f"正在启动微信：{wechat_path}")
        # 异步启动微信进程
        subprocess.Popen([wechat_path])
        
        # Phase 2优化：立即返回成功，不等待确认
        # GUI状态更新线程会在几秒内自动检测到微信运行
        # 通过GUI日志系统记录，不使用print
        # print("微信启动命令已执行")
        
        # 如果启用自动登录，延迟执行（避免阻塞用户界面）
        if auto_login:
            def delayed_auto_login():
                time.sleep(3)  # 给微信一些启动时间
                try:
                    from wechat_auto_login import auto_login_after_restart
                    # logger.info("正在尝试自动登录...")
                    auto_login_after_restart()
                except ImportError:
                    # logger.warning("自动登录模块未找到，跳过自动登录")
                    pass
                except Exception as e:
                    # logger.error(f"自动登录失败：{e}")
                    pass
            
            # 在后台线程执行自动登录，不阻塞主流程
            import threading
            threading.Thread(target=delayed_auto_login, daemon=True).start()
        
        return True
        
    except Exception as e:
        logger.error(f"启动微信失败：{e}")
        return False

def start_wechat_sync(auto_login=False):
    """启动微信（同步版本 - 保留原有实现作为备用）
    
    等待确认微信启动成功后才返回。
    在某些场景下可能需要这种确认机制。
    """
    if is_wechat_running():
        logger.info("微信已经在运行")
        return True
    
    # 查找微信安装路径
    wechat_path = find_wechat_install_path()
    
    if not wechat_path:
        logger.error("错误：未找到微信安装路径")
        logger.error("请检查微信是否已正确安装")
        return False
    
    try:
        logger.info(f"正在启动微信：{wechat_path}")
        subprocess.Popen([wechat_path])
        
        # 等待几秒钟检查是否启动成功
        for _ in range(10):
            time.sleep(1)
            if is_wechat_running():
                # logger.info("微信启动成功")
                
                # 如果启用自动登录
                if auto_login:
                    try:
                        from wechat_auto_login import auto_login_after_restart
                        # logger.info("正在尝试自动登录...")
                        auto_login_after_restart()
                    except ImportError:
                        # logger.warning("自动登录模块未找到，跳过自动登录")
                        pass
                    except Exception as e:
                        # logger.error(f"自动登录失败：{e}")
                        pass
                
                return True
        
        # logger.warning("微信可能启动失败，请手动检查")
        return False
        
    except Exception as e:
        logger.error(f"启动微信失败：{e}")
        return False

def get_wechat_status():
    """获取微信状态"""
    processes = find_wechat_processes()
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

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python wechat_controller.py start    # 启动微信")
        print("  python wechat_controller.py stop     # 停止微信") 
        print("  python wechat_controller.py status   # 查看微信状态")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        start_wechat()
    elif command == 'stop':
        stop_wechat()
    elif command == 'status':
        status = get_wechat_status()
        if status['running']:
            print(f"微信正在运行，共有 {status['process_count']} 个进程:")
            for proc in status['processes']:
                print(f"  PID: {proc['pid']}, 进程名: {proc['name']}")
                print(f"  路径: {proc['exe']}")
        else:
            print("微信未运行")
    else:
        print(f"未知命令: {command}")
        print("支持的命令: start, stop, status")
        sys.exit(1)

if __name__ == "__main__":
    main()