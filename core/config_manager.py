import json
import os
import sys
from datetime import datetime

# 导入统一日志系统
try:
    from logger_helper import logger
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from logger_helper import logger

class ConfigManager:
    """配置文件管理器"""
    
    def __init__(self, config_file="configs/configs.json"):
        self.config_file = self._get_config_path(config_file)
        self.config = self._load_default_config()
        self.load()
    
    def _get_config_path(self, config_file):
        """获取正确的配置文件路径，支持打包后的exe环境"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe环境 - 直接使用exe同目录
            exe_dir = os.path.dirname(sys.executable)
            exe_config_path = os.path.join(exe_dir, config_file)
            exe_config_dir = os.path.dirname(exe_config_path)
            
            # 创建配置目录（如果不存在）
            if not os.path.exists(exe_config_dir):
                try:
                    os.makedirs(exe_config_dir)
                    logger.info(f"创建配置目录: {exe_config_dir}")
                except Exception as e:
                    logger.warning(f"创建配置目录失败: {e}")
            
            return exe_config_path
        else:
            # 开发环境 - 使用项目根目录
            base_path = os.path.dirname(os.path.dirname(__file__))
            return os.path.join(base_path, config_file)
    
    def _load_default_config(self):
        """加载默认配置"""
        return {
            "_comment_idle": "静置触发：当系统空闲指定时间后自动执行同步",
            "idle_trigger": {
                "enabled": True,
                "_comment_enabled": "是否启用静置触发 (true/false)",
                "idle_minutes": 10,
                "_comment_idle_minutes": "静置多少分钟后触发同步 (建议5-30分钟)",
                "cooldown_minutes": 60,
                "_comment_cooldown": "两次触发之间的最小间隔时间 (分钟，防止重复执行)"
            },
            "_comment_scheduled": "定时触发：在指定时间自动执行同步",
            "scheduled_trigger": {
                "enabled": False,
                "_comment_enabled": "是否启用定时触发 (true/false)",
                "time": "05:00",
                "_comment_time": "执行时间，24小时格式 (如: 05:00, 23:30)",
                "days": ["daily"],
                "_comment_days": "执行日期: ['daily'] 每天, 或 ['monday','friday'] 指定星期"
            },
            "_comment_sync": "同步设置：控制同步流程的行为",
            "sync_settings": {
                "wait_after_sync_minutes": 5,
                "_comment_wait": "OneDrive同步完成后等待时间 (分钟)",
                "max_retry_attempts": 3,
                "_comment_retry": "失败后最大重试次数"
            },
            "_comment_logging": "日志设置：记录程序运行日志",
            "logging": {
                "enabled": True,
                "_comment_enabled": "是否启用日志记录 (true/false)",
                "level": "info",
                "_comment_level": "日志级别: debug, info, warning, error",
                "max_log_files": 5,
                "_comment_max_files": "保留的最大日志文件数"
            },
            "_comment_startup": "启动设置：程序启动相关配置",
            "startup": {
                "auto_start_service": False,
                "_comment_auto_start": "开机自动启动监控服务 (未来功能)",
                "minimize_to_tray": False,
                "_comment_minimize": "启动时最小化到系统托盘 (未来功能)"
            },
            "_comment_gui": "GUI设置：图形界面相关配置",
            "gui": {
                "close_behavior": "ask",
                "_comment_close_behavior": "关闭行为: 'ask'=询问, 'minimize'=最小化到托盘, 'exit'=直接退出",
                "remember_close_choice": False,
                "_comment_remember": "是否记住关闭方式选择，避免重复询问"
            }
        }
    
    def load(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # 合并配置，确保有默认值
                self._merge_config(self.config, loaded_config)
                # logger.info(f"已加载配置文件: {self.config_file}")
            else:
                # logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
                self.save()  # 创建默认配置文件
        except Exception as e:
            # logger.error(f"加载配置文件失败: {e}")
            # logger.info("使用默认配置")
            pass
    
    def _merge_config(self, default, loaded):
        """递归合并配置，保留默认值"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            # logger.info(f"配置已保存: {self.config_file}")
            return True
        except Exception as e:
            # logger.error(f"保存配置失败: {e}")
            return False
    
    def get(self, key_path, default=None):
        """获取配置值
        
        Args:
            key_path: 配置路径，如 "idle_trigger.enabled" 或 "logging.level"
            default: 默认值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path, value):
        """设置配置值
        
        Args:
            key_path: 配置路径，如 "idle_trigger.enabled"
            value: 要设置的值
        """
        keys = key_path.split('.')
        config = self.config
        
        # 导航到倒数第二级
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置最后一级的值
        config[keys[-1]] = value
        # logger.debug(f"配置已更新: {key_path} = {value}")
    
    def is_idle_trigger_enabled(self):
        """检查静置触发是否启用"""
        return self.get("idle_trigger.enabled", False)
    
    def get_idle_minutes(self):
        """获取静置触发分钟数"""
        return self.get("idle_trigger.idle_minutes", 10)
    
    def get_gui_config(self):
        """获取GUI配置"""
        return self.config.get("gui", {})
    
    def reload(self):
        """重新加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # 合并默认配置和加载的配置
                default_config = self._load_default_config()
                self._merge_config(default_config, loaded_config)
                self.config = default_config
                # logger.info(f"配置文件已重新加载: {self.config_file}")
            else:
                # logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
                self.config = self._load_default_config()
        except Exception as e:
            # logger.error(f"重新加载配置失败: {e}")
            # 发生错误时保持当前配置不变
            if not hasattr(self, 'config') or self.config is None:
                self.config = self._load_default_config()
    
    # OLD VERSION: 2025-08-07 - 仅用于静置触发的冷却时间
    # def get_idle_cooldown_minutes(self):
    #     """获取静置触发冷却时间（分钟）"""
    #     return self.get("idle_trigger.cooldown_minutes", 60)
    
    def get_idle_cooldown_minutes(self):
        """获取静置触发冷却时间（分钟）- 兼容性保留"""
        return self.get_global_cooldown_minutes()
    
    def get_global_cooldown_minutes(self):
        """获取全局冷却时间（分钟），所有触发类型共享"""
        return self.get("idle_trigger.cooldown_minutes", 20)
    
    def is_scheduled_trigger_enabled(self):
        """检查定时触发是否启用"""
        return self.get("scheduled_trigger.enabled", False)
    
    def get_scheduled_time(self):
        """获取定时触发时间"""
        return self.get("scheduled_trigger.time", "05:00")
    
    def get_scheduled_days(self):
        """获取定时触发日期"""
        return self.get("scheduled_trigger.days", ["daily"])
    
    def get_sync_wait_minutes(self):
        """获取同步等待分钟数"""
        return self.get("sync_settings.wait_after_sync_minutes", 5)
    
    def is_logging_enabled(self):
        """检查日志是否启用"""
        return self.get("logging.enabled", True)
    
    def get_log_level(self):
        """获取日志级别"""
        return self.get("logging.level", "info")
    
    def display_config(self):
        """显示当前配置(命令行模式)"""
        # 这个print保留，因为是命令行工具的输出
        print("="*60)
        print("当前配置")
        print("="*60)
        
        print(f"配置文件: {self.config_file}")
        
        print("\n[静置触发]")
        print(f"  启用: {self.is_idle_trigger_enabled()}")
        print(f"  静置分钟: {self.get_idle_minutes()}")
        print(f"  冷却时间: {self.get_idle_cooldown_minutes()} 分钟")
        
        print("\n[定时触发]")
        print(f"  启用: {self.is_scheduled_trigger_enabled()}")
        print(f"  执行时间: {self.get_scheduled_time()}")
        print(f"  执行日期: {', '.join(self.get_scheduled_days())}")
        
        print("\n[同步设置]")
        print(f"  同步后等待: {self.get_sync_wait_minutes()} 分钟")
        print(f"  最大重试: {self.get('sync_settings.max_retry_attempts', 3)} 次")
        
        print("\n[日志设置]")
        print(f"  启用日志: {self.is_logging_enabled()}")
        print(f"  日志级别: {self.get_log_level()}")
        
        print("\n[启动设置]")
        print(f"  开机自启: {self.get('startup.auto_start_service', False)}")
        print(f"  最小化托盘: {self.get('startup.minimize_to_tray', True)}")
        
        print("\n[GUI设置]")
        print(f"  关闭行为: {self.get_close_behavior()}")
        print(f"  记住选择: {self.is_remember_close_choice()}")
    
    # GUI配置相关方法
    def get_close_behavior(self):
        """获取关闭行为设置"""
        return self.get("gui.close_behavior", "ask")
    
    def set_close_behavior(self, behavior):
        """设置关闭行为"""
        if behavior in ["ask", "minimize", "exit"]:
            self.config["gui"]["close_behavior"] = behavior
            self.save()
            return True
        return False
    
    def is_remember_close_choice(self):
        """检查是否记住关闭选择"""
        return self.get("gui.remember_close_choice", False)
    
    def set_remember_close_choice(self, remember):
        """设置是否记住关闭选择"""
        self.config["gui"]["remember_close_choice"] = bool(remember)
        self.save()
    
    def save_config(self, config_data):
        """保存配置数据"""
        self.config = config_data
        return self.save()

def validate_config():
    """验证配置文件有效性"""
    config = ConfigManager()
    
    # 这个print保留，因为是命令行工具的输出
    print("=== 配置文件验证 ===\n")
    
    errors = []
    warnings = []
    
    # 验证静置触发设置
    if config.is_idle_trigger_enabled():
        idle_minutes = config.get_idle_minutes()
        if not isinstance(idle_minutes, (int, float)) or idle_minutes <= 0:
            errors.append("idle_trigger.idle_minutes 必须是正数")
        elif idle_minutes < 1:
            warnings.append("静置时间少于1分钟可能会频繁触发")
        
        cooldown_minutes = config.get_idle_cooldown_minutes()
        if not isinstance(cooldown_minutes, (int, float)) or cooldown_minutes <= 0:
            errors.append("idle_trigger.cooldown_minutes 必须是正数")
        elif cooldown_minutes < 1:
            warnings.append("冷却时间少于1分钟可能导致重复触发")
        elif cooldown_minutes < idle_minutes:
            warnings.append("冷却时间小于静置时间可能导致意外行为")
    
    # 验证定时触发设置
    if config.is_scheduled_trigger_enabled():
        time_str = config.get_scheduled_time()
        try:
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                errors.append("scheduled_trigger.time 格式错误，应为 HH:MM")
        except:
            errors.append("scheduled_trigger.time 格式错误，应为 HH:MM")
        
        days = config.get_scheduled_days()
        valid_days = ['daily', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if day.lower() not in valid_days:
                errors.append(f"无效的日期设置: {day}")
    
    # 验证同步设置
    wait_minutes = config.get_sync_wait_minutes()
    if not isinstance(wait_minutes, (int, float)) or wait_minutes < 0:
        errors.append("sync_settings.wait_after_sync_minutes 必须是非负数")
    
    # 验证日志设置
    if config.is_logging_enabled():
        log_level = config.get_log_level().lower()
        if log_level not in ['debug', 'info', 'warning', 'error']:
            errors.append("logging.level 必须是 debug, info, warning, error 之一")
    
    # 显示结果 (这些print保留，因为是命令行工具的输出)
    if errors:
        print("配置文件有错误:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("\n配置文件有警告:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("配置文件验证通过")
    
    return len(errors) == 0

def main():
    # 这个函数的print保留，因为是命令行工具的输出
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'show':
            config = ConfigManager()
            config.display_config()
        elif command == 'create':
            config = ConfigManager("configs/configs.json")
            config.save()
            print("已创建默认配置文件")
        elif command == 'validate':
            validate_config()
        else:
            print(f"未知命令: {command}")
    else:
        print("配置文件管理器")
        print("\n用法:")
        print("  python config_manager.py show     # 显示当前配置")
        print("  python config_manager.py create   # 创建默认配置文件")
        print("  python config_manager.py validate # 验证配置文件")
        print("\n配置文件: configs/configs.json")
        print("直接编辑 configs/configs.json 文件来修改配置")

if __name__ == "__main__":
    main()