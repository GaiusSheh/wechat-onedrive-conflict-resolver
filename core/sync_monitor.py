import time
import threading
import subprocess
import logging
import sys
import signal
import os
from datetime import datetime
from config_manager import ConfigManager
from idle_detector import IdleDetector
from task_scheduler import TaskScheduler

class SyncMonitor:
    """微信OneDrive同步监控服务"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.idle_detector = IdleDetector()
        self.scheduler = TaskScheduler()
        self.running = False
        self.last_idle_trigger = None
        self.last_scheduled_trigger = None
        
        # 设置日志
        self._setup_logging()
        
        # 初始化调度任务
        self._setup_scheduled_tasks()
    
    def _setup_logging(self):
        """设置日志"""
        if self.config.is_logging_enabled():
            log_level = getattr(logging, self.config.get_log_level().upper(), logging.INFO)
            
            # 创建日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # 文件日志
            file_handler = logging.FileHandler('sync_monitor.log', encoding='utf-8')
            file_handler.setFormatter(formatter)
            
            # 控制台日志
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            
            # 配置根日志记录器
            logging.basicConfig(
                level=log_level,
                handlers=[file_handler, console_handler]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("日志系统已初始化")
        else:
            # 禁用日志
            logging.disable(logging.CRITICAL)
            self.logger = logging.getLogger(__name__)
    
    def _setup_scheduled_tasks(self):
        """设置定时任务"""
        if self.config.is_scheduled_trigger_enabled():
            time_str = self.config.get_scheduled_time()
            days = self.config.get_scheduled_days()
            
            if "daily" in days:
                self.scheduler.add_daily_task(time_str, self._execute_sync_workflow, "每日同步任务")
            else:
                for day in days:
                    if day.lower() in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                        self.scheduler.add_weekly_task(day, time_str, self._execute_sync_workflow, f"每{day}同步任务")
            
            self.logger.info("定时任务已设置")
    
    def _execute_sync_workflow(self):
        """执行同步流程（定时触发）"""
        try:
            # NEW VERSION: 2025-08-07 - 添加全局冷却检查
            from global_cooldown import check_and_trigger_if_allowed
            cooldown_minutes = self.config.get_global_cooldown_minutes()
            
            if not check_and_trigger_if_allowed(cooldown_minutes, "定时触发"):
                remaining = self.get_remaining_global_cooldown(cooldown_minutes)
                self.logger.info(f"定时触发被全局冷却阻止，剩余 {remaining:.1f} 分钟")
                return False
            
            self.logger.info("开始执行微信OneDrive同步流程（定时触发）")
            print("\n" + "="*60)
            print("正在执行自动同步流程（定时触发）...")
            print("="*60)
            
            # 调用同步流程脚本，显示实时输出
            result = subprocess.run([
                sys.executable, 'core/sync_workflow.py', 'run'
            ], timeout=600)  # 10分钟超时，不捕获输出以显示实时进度
            
            print("="*60)
            if result.returncode == 0:
                self.logger.info("同步流程执行成功")
                return True
            else:
                self.logger.error("同步流程执行失败")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("同步流程执行超时")
            return False
        except Exception as e:
            self.logger.error(f"执行同步流程时发生错误: {e}")
            return False
    
    def _check_idle_trigger(self):
        """检查静置触发条件"""
        if not self.config.is_idle_trigger_enabled():
            return False
        
        idle_minutes = self.config.get_idle_minutes()
        current_idle = self.idle_detector.get_idle_time_minutes()
        
        # 调试日志：显示当前空闲时间
        self.logger.debug(f"检查空闲状态: 当前空闲 {current_idle:.1f} 分钟，阈值 {idle_minutes} 分钟")
        
        # 检查是否达到静置时间且距离上次触发超过冷却时间
        if current_idle >= idle_minutes:
            # OLD VERSION: 2025-08-07 - 仅检查静置触发的独立冷却
            # current_time = datetime.now()
            # cooldown_minutes = self.config.get_idle_cooldown_minutes()
            # cooldown_seconds = cooldown_minutes * 60
            # 
            # # 避免重复触发（在冷却时间内只触发一次）
            # if (self.last_idle_trigger is None or 
            #     (current_time - self.last_idle_trigger).total_seconds() > cooldown_seconds):
            #     
            #     self.logger.info(f"检测到系统静置 {current_idle:.1f} 分钟，触发同步")
            #     self.last_idle_trigger = current_time
            #     return True
            
            # NEW VERSION: 2025-08-07 - 使用全局冷却管理器
            from global_cooldown import check_and_trigger_if_allowed
            cooldown_minutes = self.config.get_global_cooldown_minutes()
            
            if check_and_trigger_if_allowed(cooldown_minutes, "静置触发"):
                self.logger.info(f"检测到系统静置 {current_idle:.1f} 分钟，触发同步")
                # 保持向后兼容，同时更新本地记录
                self.last_idle_trigger = datetime.now()
                return True
            else:
                remaining = self.get_remaining_global_cooldown(cooldown_minutes)
                self.logger.info(f"静置触发被全局冷却阻止，剩余 {remaining:.1f} 分钟")
        
        return False
    
    def get_remaining_global_cooldown(self, cooldown_minutes: float) -> float:
        """获取剩余全局冷却时间（分钟）"""
        from core.global_cooldown import get_remaining_global_cooldown
        return get_remaining_global_cooldown(cooldown_minutes)
    
    def start_monitoring(self):
        """启动监控服务"""
        if self.running:
            print("监控服务已经在运行")
            return
        
        self.running = True
        self.logger.info("微信OneDrive同步监控服务启动")
        
        # 启动定时任务调度器
        self.scheduler.start()
        
        # 显示配置信息
        print("="*60)
        print("微信OneDrive同步监控服务")
        print("="*60)
        print(f"静置触发: {'启用' if self.config.is_idle_trigger_enabled() else '禁用'}")
        if self.config.is_idle_trigger_enabled():
            print(f"  静置时间: {self.config.get_idle_minutes()} 分钟")
            print(f"  冷却时间: {self.config.get_idle_cooldown_minutes()} 分钟")
        
        print(f"定时触发: {'启用' if self.config.is_scheduled_trigger_enabled() else '禁用'}")
        if self.config.is_scheduled_trigger_enabled():
            print(f"  执行时间: {self.config.get_scheduled_time()}")
            print(f"  执行日期: {', '.join(self.config.get_scheduled_days())}")
        
        next_run = self.scheduler.get_next_run_time()
        if next_run:
            print(f"下次定时执行: {next_run}")
        
        print(f"日志记录: {'启用' if self.config.is_logging_enabled() else '禁用'}")
        print("="*60)
        print("监控服务正在运行... 按 Ctrl+Z 停止")
        
        # 设置信号处理器
        def signal_handler(signum, frame):
            self.logger.info("收到停止信号")
            self.running = False
        
        # Windows下使用SIGTERM，Linux下使用SIGTSTP (Ctrl+Z)
        if os.name == 'nt':  # Windows
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)  # 保留Ctrl+C支持
        else:  # Linux/Unix
            signal.signal(signal.SIGTSTP, signal_handler)
        
        # 主监控循环
        try:
            while self.running:
                # 检查静置触发
                if self._check_idle_trigger():
                    self._execute_sync_workflow()
                
                # 每10秒检查一次
                time.sleep(10)
                
        except KeyboardInterrupt:
            self.logger.info("收到停止信号")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """停止监控服务"""
        if not self.running:
            return
        
        self.running = False
        self.scheduler.stop()
        self.logger.info("微信OneDrive同步监控服务已停止")
        print("\n监控服务已停止")
    
    def status(self):
        """显示服务状态"""
        print("="*60)
        print("监控服务状态")
        print("="*60)
        
        print(f"服务状态: {'运行中' if self.running else '已停止'}")
        
        current_idle = self.idle_detector.get_idle_time_minutes()
        print(f"当前静置时间: {current_idle:.1f} 分钟")
        
        if self.config.is_idle_trigger_enabled():
            required_idle = self.config.get_idle_minutes()
            print(f"静置触发阈值: {required_idle} 分钟")
            print(f"静置触发状态: {'就绪' if current_idle >= required_idle else f'等待 {required_idle - current_idle:.1f} 分钟'}")
        
        if self.last_idle_trigger:
            print(f"上次静置触发: {self.last_idle_trigger.strftime('%Y-%m-%d %H:%M:%S')}")
        
        next_run = self.scheduler.get_next_run_time()
        if next_run:
            print(f"下次定时执行: {next_run}")
        
        self.scheduler.list_tasks()

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        monitor = SyncMonitor()
        
        if command == 'start':
            monitor.start_monitoring()
        elif command == 'status':
            monitor.status()
        elif command == 'test-sync':
            print("测试执行同步流程...")
            result = monitor._execute_sync_workflow()
            print(f"测试结果: {'成功' if result else '失败'}")
        elif command == 'test-idle':
            print("测试静置检测...")
            idle_time = monitor.idle_detector.format_idle_time()
            print(f"当前静置时间: {idle_time}")
            if monitor._check_idle_trigger():
                print("[OK] 达到静置触发条件")
            else:
                print("[--] 未达到静置触发条件")
        else:
            print(f"未知命令: {command}")
    else:
        print("微信OneDrive同步监控服务")
        print("\n用法:")
        print("  python sync_monitor.py start      # 启动监控服务")
        print("  python sync_monitor.py status     # 显示服务状态")
        print("  python sync_monitor.py test-sync  # 测试同步流程")
        print("  python sync_monitor.py test-idle  # 测试静置检测")
        print("\n配置:")
        print("  python config_manager.py edit     # 编辑配置")
        print("  python config_manager.py show     # 显示配置")
        print("\n功能:")
        print("- 静置时间触发自动同步")
        print("- 定时任务触发自动同步")
        print("- 可配置的触发条件")
        print("- 详细的日志记录")

if __name__ == "__main__":
    main()