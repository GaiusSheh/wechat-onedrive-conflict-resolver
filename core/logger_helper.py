#!/usr/bin/env python3
"""
统一日志系统辅助工具 v2.0
实现四套独立的日志系统：
1. 主日志系统 - 用户级别，可调节日志级别
2. 性能调试系统 - 开发者级别，性能监控专用
3. GUI调试系统 - 开发者级别，界面调试专用  
4. 图标调试系统 - 开发者级别，图标处理专用
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import threading
from typing import Optional, Callable

# 导入调试管理器
from debug_control.debug_manager import debug_manager

class LoggerHelper:
    """统一日志管理器 v2.0"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LoggerHelper, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        # 主日志系统
        self.main_logger = None
        self.main_console_handler = None
        self.main_file_handler = None
        
        # 专门调试日志器
        self.perf_logger = None
        self.gui_logger = None
        self.icon_logger = None
        
        self.gui_callback = None  # GUI日志回调函数
        self._debug_mode = False  # 调试模式开关
        
        # 初始化所有日志系统
        self.setup_all_loggers()
    
    def _get_base_directory(self):
        """获取基础目录（exe所在目录或开发环境根目录）"""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller打包后的exe运行时
            return Path(sys.executable).parent
        else:
            # 开发环境运行时
            return Path(__file__).parent.parent
    
    def _create_log_directories(self):
        """创建日志目录结构"""
        base_log_dir = self._get_base_directory() / "logs"
        directories = ['main', 'perf', 'gui', 'icon']
        
        for dir_name in directories:
            log_dir = base_log_dir / dir_name
            log_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_all_loggers(self):
        """初始化所有日志系统"""
        # 创建日志目录结构
        self._create_log_directories()
        
        # 设置主日志系统
        self.setup_main_logger()
        
        # 设置专门调试日志系统
        self.setup_debug_loggers()
    
    def setup_main_logger(self):
        """设置主日志系统（用户可见）"""
        self.main_logger = logging.getLogger('WeChat_OneDrive_Main')
        self.main_logger.setLevel(logging.DEBUG)
        
        if self.main_logger.handlers:
            self.main_logger.handlers.clear()
        
        # 创建格式器
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台输出（开发环境）
        if self._should_use_console():
            self.main_console_handler = logging.StreamHandler(sys.stdout)
            self.main_console_handler.setLevel(logging.INFO)
            self.main_console_handler.setFormatter(console_formatter)
            self.main_logger.addHandler(self.main_console_handler)
        
        # 主日志文件（总是创建）
        try:
            log_dir = self._get_base_directory() / "logs" / "main"
            log_file = log_dir / f"main_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
            
            self.main_file_handler = logging.FileHandler(log_file, encoding='utf-8')
            self.main_file_handler.setLevel(logging.DEBUG)
            self.main_file_handler.setFormatter(file_formatter)
            self.main_logger.addHandler(self.main_file_handler)
            
            # 清理旧日志
            self._cleanup_old_logs(log_dir, "main_*.log", keep_count=10)
            
        except Exception as e:
            temp_logger = logging.getLogger('temp_main_setup')
            temp_logger.error(f"主日志设置失败: {e}")
    
    def setup_debug_loggers(self):
        """设置专门调试日志系统"""
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        base_log_dir = self._get_base_directory() / "logs"
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # 性能调试日志
        if debug_manager.is_performance_debug_enabled():
            try:
                self.perf_logger = logging.getLogger('WeChat_OneDrive_Perf')
                self.perf_logger.setLevel(logging.DEBUG)
                if self.perf_logger.handlers:
                    self.perf_logger.handlers.clear()
                    
                log_file = base_log_dir / "perf" / f"perf_{timestamp}.log"
                handler = logging.FileHandler(log_file, encoding='utf-8')
                handler.setLevel(logging.DEBUG)
                handler.setFormatter(file_formatter)
                self.perf_logger.addHandler(handler)
                
                self._cleanup_old_logs(base_log_dir / "perf", "perf_*.log", keep_count=5)
            except Exception as e:
                pass
        
        # GUI调试日志
        if debug_manager.is_gui_debug_enabled():
            try:
                self.gui_logger = logging.getLogger('WeChat_OneDrive_GUI')
                self.gui_logger.setLevel(logging.DEBUG)
                if self.gui_logger.handlers:
                    self.gui_logger.handlers.clear()
                    
                log_file = base_log_dir / "gui" / f"gui_{timestamp}.log"
                handler = logging.FileHandler(log_file, encoding='utf-8')
                handler.setLevel(logging.DEBUG)
                handler.setFormatter(file_formatter)
                self.gui_logger.addHandler(handler)
                
                self._cleanup_old_logs(base_log_dir / "gui", "gui_*.log", keep_count=5)
            except Exception as e:
                pass
        
        # 图标调试日志
        if debug_manager.is_icon_debug_enabled():
            try:
                self.icon_logger = logging.getLogger('WeChat_OneDrive_Icon')
                self.icon_logger.setLevel(logging.DEBUG)
                if self.icon_logger.handlers:
                    self.icon_logger.handlers.clear()
                    
                log_file = base_log_dir / "icon" / f"icon_{timestamp}.log"
                handler = logging.FileHandler(log_file, encoding='utf-8')
                handler.setLevel(logging.DEBUG)
                handler.setFormatter(file_formatter)
                self.icon_logger.addHandler(handler)
                
                self._cleanup_old_logs(base_log_dir / "icon", "icon_*.log", keep_count=5)
            except Exception as e:
                pass
    
    def _cleanup_old_logs(self, log_dir: Path, pattern: str, keep_count: int = 10):
        """清理旧的日志文件，保留最近的N个"""
        try:
            # 获取所有匹配的日志文件
            log_files = list(log_dir.glob(pattern))
            if len(log_files) <= keep_count:
                return
            
            # 按修改时间排序，保留最新的keep_count个
            log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            files_to_delete = log_files[keep_count:]
            
            for old_file in files_to_delete:
                try:
                    old_file.unlink()
                    if self.main_logger:
                        self.main_logger.info(f"已删除旧日志文件: {old_file.name}")
                except Exception as e:
                    if self.main_logger:
                        self.main_logger.error(f"删除旧日志文件失败 {old_file.name}: {e}")
                    
        except Exception as e:
            if self.main_logger:
                self.main_logger.error(f"清理日志文件失败: {e}")
    
    def _should_use_console(self) -> bool:
        """判断是否应该使用控制台输出"""
        # 如果是从命令行运行或开发环境，启用控制台输出
        return (
            hasattr(sys, 'ps1') or  # 交互式Python
            '--debug' in sys.argv or  # 显式调试模式
            os.environ.get('WECHAT_ONEDRIVE_DEBUG', '').lower() in ('1', 'true', 'on')
        )
    
    def set_gui_callback(self, callback: Callable[[str, str], None]):
        """设置GUI日志回调函数
        
        Args:
            callback: 回调函数，参数为(level, message)
        """
        self.gui_callback = callback
    
    def set_debug_mode(self, enabled: bool):
        """设置调试模式"""
        self._debug_mode = enabled
        
        # 动态调整控制台日志级别
        if self.main_console_handler:
            if enabled:
                self.main_console_handler.setLevel(logging.DEBUG)
            else:
                self.main_console_handler.setLevel(logging.INFO)
    
    def set_log_level_from_config(self, level_str: str):
        """从配置文件设置日志级别
        
        Args:
            level_str: 日志级别字符串 ('debug', 'info', 'warning', 'error')
        """
        level_str = level_str.lower()
        
        # 根据配置级别决定是否显示DEBUG信息
        if level_str == 'debug':
            self._debug_mode = True
        else:
            self._debug_mode = False
        
        # 同时调整控制台处理器级别
        if self.main_console_handler:
            if level_str == 'debug':
                self.main_console_handler.setLevel(logging.DEBUG)
            elif level_str == 'info':
                self.main_console_handler.setLevel(logging.INFO)
            elif level_str == 'warning':
                self.main_console_handler.setLevel(logging.WARNING)
            elif level_str == 'error':
                self.main_console_handler.setLevel(logging.ERROR)
    
    def _log_and_gui(self, level: str, message: str):
        """记录到主日志和GUI"""
        # 记录到主日志文件
        if self.main_logger:
            log_method = getattr(self.main_logger, level.lower(), self.main_logger.info)
            log_method(message)
        
        # 发送到GUI（如果有回调）
        if self.gui_callback:
            try:
                self.gui_callback(level.upper(), message)
            except Exception as e:
                if self.main_logger:
                    self.main_logger.error(f"GUI日志回调失败: {e}")
    
    # 标准日志接口
    def debug(self, message: str):
        """调试信息 - 只在调试模式下显示"""
        if self._debug_mode:
            self._log_and_gui('debug', message)
    
    def info(self, message: str):
        """一般信息"""
        self._log_and_gui('info', message)
    
    def warning(self, message: str):
        """警告信息"""
        self._log_and_gui('warning', message)
    
    def error(self, message: str):
        """错误信息"""
        self._log_and_gui('error', message)
    
    def critical(self, message: str):
        """严重错误"""
        self._log_and_gui('critical', message)
    
    # 替换print的便捷方法
    def print_info(self, *args, **kwargs):
        """替换print语句 - 信息级别"""
        message = ' '.join(str(arg) for arg in args)
        self.info(message)
    
    def print_debug(self, *args, **kwargs):
        """替换print语句 - 调试级别"""
        message = ' '.join(str(arg) for arg in args)
        self.debug(message)
    
    def print_error(self, *args, **kwargs):
        """替换print语句 - 错误级别"""
        message = ' '.join(str(arg) for arg in args)
        self.error(message)
    
    def print_warning(self, *args, **kwargs):
        """替换print语句 - 警告级别"""
        message = ' '.join(str(arg) for arg in args)
        self.warning(message)
    
    # 性能监控相关
    def perf_debug(self, operation: str, duration: float, threshold: float = 0.1):
        """性能调试信息
        
        Args:
            operation: 操作描述
            duration: 耗时（秒）
            threshold: 警告阈值（秒）
        """
        message = f"[性能] {operation} 耗时: {duration:.3f}秒"
        
        # 根据耗时选择日志级别和输出位置
        if duration > threshold:
            # 性能警告，记录到主日志
            self.warning(f"{message} (超过阈值{threshold:.3f}秒)")
        
        # 详细性能信息，记录到性能调试日志
        if self.perf_logger:
            if duration > threshold:
                self.perf_logger.warning(message + f" (超过阈值{threshold:.3f}秒)")
            else:
                self.perf_logger.debug(message)
    
    def gui_update_debug(self, component: str, duration: float):
        """GUI更新性能调试"""
        self.perf_debug(f"GUI更新-{component}", duration, threshold=0.05)
    
    def api_call_debug(self, api_name: str, duration: float):
        """API调用性能调试"""
        self.perf_debug(f"API调用-{api_name}", duration, threshold=0.2)
    
    # GUI调试相关
    def gui_debug(self, component: str, message: str, level: str = "debug"):
        """GUI调试信息
        
        Args:
            component: 组件名称 (layout, buttons, status_updates, window_events)
            message: 调试信息
            level: 日志级别
        """
        if self.gui_logger and debug_manager.is_gui_component_debug_enabled(component):
            full_message = f"[GUI-{component}] {message}"
            log_method = getattr(self.gui_logger, level.lower(), self.gui_logger.debug)
            log_method(full_message)
    
    def icon_debug(self, operation: str, message: str, level: str = "debug"):
        """图标调试信息
        
        Args:
            operation: 操作类型 (load, process, convert, scale)
            message: 调试信息  
            level: 日志级别
        """
        if self.icon_logger and debug_manager.is_icon_debug_enabled():
            full_message = f"[ICON-{operation}] {message}"
            log_method = getattr(self.icon_logger, level.lower(), self.icon_logger.debug)
            log_method(full_message)
    
    # 系统状态记录
    def system_status(self, component: str, status: str, details: str = ""):
        """记录系统状态变化"""
        message = f"[系统] {component}: {status}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def user_action(self, action: str, details: str = ""):
        """记录用户操作"""
        message = f"[用户] {action}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def sync_operation(self, operation: str, result: str, details: str = ""):
        """记录同步操作"""
        message = f"[同步] {operation}: {result}"
        if details:
            message += f" - {details}"
        
        if result.lower() in ['成功', 'success', '完成']:
            self.info(message)
        elif result.lower() in ['失败', 'error', '错误']:
            self.error(message)
        else:
            self.info(message)

# 全局实例
logger = LoggerHelper()

# 便捷函数 - 直接替换print使用
def log_info(*args, **kwargs):
    """替换print - 信息"""
    logger.print_info(*args, **kwargs)

def log_debug(*args, **kwargs):
    """替换print - 调试"""
    logger.print_debug(*args, **kwargs)

def log_error(*args, **kwargs):
    """替换print - 错误"""
    logger.print_error(*args, **kwargs)

def log_warning(*args, **kwargs):
    """替换print - 警告"""
    logger.print_warning(*args, **kwargs)

# 设置函数
def set_gui_callback(callback):
    """设置GUI回调"""
    logger.set_gui_callback(callback)

def set_debug_mode(enabled: bool):
    """设置调试模式"""
    logger.set_debug_mode(enabled)

def set_log_level_from_config(level_str: str):
    """从配置文件设置日志级别"""
    logger.set_log_level_from_config(level_str)

def enable_debug():
    """启用调试模式"""
    set_debug_mode(True)

def disable_debug():
    """禁用调试模式"""
    set_debug_mode(False)

if __name__ == "__main__":
    # 测试四套日志系统
    logger.info("测试统一日志系统 v2.0...")
    
    logger.info("这是一条信息")
    logger.debug("这是调试信息")
    logger.warning("这是警告")
    logger.error("这是错误")
    
    # 测试性能监控
    import time
    
    start_time = time.time()
    time.sleep(0.1)
    duration = time.time() - start_time
    logger.perf_debug("测试操作", duration)
    
    # 测试GUI调试
    logger.gui_debug("layout", "组件尺寸更新: 800x600")
    logger.gui_debug("buttons", "按钮点击事件: 开始同步")
    
    # 测试图标调试
    logger.icon_debug("load", "加载PNG文件: main.png")
    logger.icon_debug("process", "缩放图像到64x64")
    
    # 测试便捷函数
    log_info("使用便捷函数记录信息")
    log_debug("使用便捷函数记录调试")
    
    logger.info("四套日志系统测试完成")