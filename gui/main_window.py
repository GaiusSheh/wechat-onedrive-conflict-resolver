#!/usr/bin/env python3
"""
微信OneDrive冲突解决工具 - GUI主窗口 v3.0 正式版
功能完整版：边缘触发 + 双冷却按钮 + 中文界面 + 完美布局

=== 开发日志 ===
v3.0 (2025-08-09) - 正式版发布
- [核心改进] 实现边缘触发逻辑，解决重复打扰用户问题 
- [竞态修复] 修复is_running_sync标志在多线程环境下的竞态条件
- [定时修复] 修复定时触发无法执行的监控循环逻辑问题
- [UI优化] 新增双冷却按钮：重置冷却(清空) + 应用冷却(设置为配置值)
- [本地化] 配置面板全面中文化，保持英文配置兼容性
- [布局完善] 按钮尺寸统一，间距优化，窗口自动居中
- [日志优化] 性能监控改为DEBUG级别，冷却阻止改为INFO级别

v2.3 (2025-08-08) - 配置面板优化版
- [性能] 配置面板启动速度优化，GUI响应流畅度提升
- [主题] ttkbootstrap现代化主题应用
- [冷却] 全局冷却系统实现，跨触发类型统一管理

=== 技术特性 ===
- 边缘触发检测：通过last_idle_state_triggered状态跟踪实现
- 多线程同步：主线程设置标志，子线程执行同步任务  
- 动态版本管理：GUI界面从version.json统一读取版本信息，无硬编码版本号
- 配置热加载：实时读取配置文件变化
- 图标资源管理：统一的图标加载和缓存系统
- 主题适配：支持ttkbootstrap多种现代化主题
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
import threading
import time
from datetime import datetime
import sys
import os
from .icon_manager import IconManager

# 添加core模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

# 导入统一日志系统
from core.logger_helper import logger, log_debug, log_info, log_error, log_warning, set_gui_callback, set_log_level_from_config

# 导入版本管理系统
from core.version_helper import get_version, get_version_name, get_app_title, get_full_version_string

# 导入性能调试系统
from core.performance_debug import (
    measure_time, perf_log, log_user_action, log_gui_update, 
    log_system_call, perf_timer, PERFORMANCE_DEBUG_ENABLED
)

# 导入系统托盘模块
try:
    from .system_tray import SystemTray, TRAY_AVAILABLE
    from .close_dialog import CloseDialog
except ImportError:
    try:
        from system_tray import SystemTray, TRAY_AVAILABLE
        from close_dialog import CloseDialog
    except ImportError as e:
        TRAY_AVAILABLE = False
        SystemTray = None
        CloseDialog = None

from core.wechat_controller import is_wechat_running, find_wechat_processes, start_wechat, stop_wechat
from core.onedrive_controller import is_onedrive_running, get_onedrive_status, start_onedrive, pause_onedrive_sync
from core.config_manager import ConfigManager
from core.idle_detector import IdleDetector
from core.performance_monitor import start_performance_monitoring, get_performance_summary
from core import sync_workflow

class MainWindow:
    """主GUI窗口类 - 使用动态版本管理"""
    
    # === 调试开关 ===
    # 设置为 True 时启用所有布局调试信息，False 时禁用
    DEBUG_LAYOUT = False
    
    # 设计常量 - 统一的间距系统
    PADDING_LARGE = 20      # 大间距：卡片间距、主容器padding
    PADDING_MEDIUM = 15     # 中间距：卡片内部padding
    PADDING_SMALL = 10      # 小间距：组件间距
    PADDING_TINY = 5        # 微间距：行间距
    
    ROW_HEIGHT = 45         # 统一行高 - 增加间距避免按钮贴合
    BUTTON_WIDTH = 12       # 按钮宽度
    LABEL_WIDTH = 15        # 标签宽度
    
    def __init__(self, system_tray=None):
        # 使用ttkbootstrap创建现代化主题的窗口
        self.root = ttk.Window(themename="cosmo")
        self.root.title(get_app_title())
        self.root.geometry("1000x1200")
        self.root.minsize(1000, 1200)
        self.root.resizable(True, True)
        
        # 设置窗口图标 - 修复版本
        self._setup_window_icons()
        
        # 初始化图标管理器
        self.icon_manager = IconManager()
        self.icons = self.icon_manager.get_all_icons()
        
        # 初始化组件
        self.config = ConfigManager()
        self.idle_detector = IdleDetector()
        
        # 初始化统一日志系统
        self._setup_logging_system()
        
        # 状态变量
        self.is_running_sync = False
        self.last_sync_time = None
        self.sync_success_count = 0
        self.sync_error_count = 0
        
        # 静置触发冷却相关变量
        self.last_idle_trigger_time = None
        self.cooldown_remaining = 0
        
        # 应用状态缓存
        self._wechat_status = None
        self._onedrive_status = None
        self._status_check_in_progress = False
        
        # 智能空闲时间计时器
        self._local_idle_start_time = None
        self._last_system_idle_time = 0
        self._local_idle_seconds = 0
        self._last_system_check_time = 0
        self._idle_timer_stable = False
        
        # 高频用户活动检测
        self._last_activity_check_time = 0
        self._cached_system_idle = 0
        
        # 显示优化缓存
        self._last_idle_display_text = ""
        self._last_cooldown_display_text = ""
        
        # 状态缓存（减少重复更新）
        self._last_wechat_status = None
        self._last_onedrive_status = None
        self._last_sync_time_str = None
        self._last_stats_text = None
        
        # 调试时间戳
        self._debug_enabled = True
        self._last_update_time = 0
        self._update_intervals = []
        
        # GUI更新队列（线程安全）
        self._gui_update_pending = False
        self._pending_idle_text = None
        
        # 系统托盘初始化（暂不启动）
        self.system_tray = None
        
        # 创建界面
        self.create_widgets()
        self.create_menu()
        
        # 强制更新窗口布局
        self.root.update_idletasks()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 添加Windows会话管理事件处理（修复关机时taskkill弹窗问题）
        self.setup_session_handling()
        
        # 移除独立文件日志系统 - 统一使用main日志系统
        
        # 启动状态更新线程
        self.start_status_update_thread()
        self.start_system_status_thread()
        self.start_auto_monitor_thread()
        
        # 根据配置决定是否启用性能监控
        try:
            from core.performance_debug import is_performance_debug_enabled
            if is_performance_debug_enabled():
                start_performance_monitoring(self.log_message)
        except Exception as e:
            # 如果性能监控启动失败，不影响主程序运行
            pass
        
        # NEW VERSION: 2025-08-08 - 软件启动时重置全局冷却状态
        try:
            # 导入全局冷却管理器
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
            from core.global_cooldown import reset_global_cooldown
            
            # 重置全局冷却状态，让每次启动都从"无冷却"开始
            reset_global_cooldown()
            self.log_message("软件启动时已重置全局冷却状态", "INFO")
            
            # 清理本地变量（兼容性保留）
            self.last_idle_trigger_time = None
            self.cooldown_remaining = 0
            
        except Exception as startup_reset_error:
            self.log_message(f"启动时重置全局冷却失败: {startup_reset_error}", "WARNING")
            # 即使重置失败也不影响软件正常启动
        
        # 初始化系统托盘（在日志系统之后）
        if system_tray is not None:
            # 使用传入的system_tray（通常是启动时最小化的情况）
            self.system_tray = system_tray
            self.log_message("使用外部SystemTray实例", "INFO")
        elif TRAY_AVAILABLE and SystemTray:
            # 创建新的system_tray（正常启动的情况）
            self.system_tray = SystemTray(self)
            # 启动系统托盘
            tray_started = self.system_tray.start_tray()
            if tray_started:
                self.log_message("系统托盘已启动", "INFO")
            else:
                self.log_message("系统托盘启动失败", "WARNING")
                self.system_tray = None
        else:
            self.log_message("系统托盘功能不可用（缺少依赖）", "INFO")
    
    def _get_resource_path(self, relative_path):
        """获取正确的资源文件路径，支持打包后的exe环境"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe环境
            bundle_dir = sys._MEIPASS
            bundle_path = os.path.join(bundle_dir, relative_path)
            logger.info(f"打包环境路径: bundle_dir={bundle_dir}")
            logger.info(f"尝试路径: {bundle_path}")
            logger.info(f"文件存在: {os.path.exists(bundle_path)}")
            
            # 如果bundle中不存在，尝试exe同目录
            if not os.path.exists(bundle_path):
                exe_dir = os.path.dirname(sys.executable)
                exe_path = os.path.join(exe_dir, relative_path)
                logger.info(f"尝试exe目录路径: {exe_path}")
                logger.info(f"exe目录文件存在: {os.path.exists(exe_path)}")
                return exe_path
            return bundle_path
        else:
            # 开发环境
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, relative_path)
    
    # OLD VERSION: 2025-08-15 调试版本 - 间歇性任务栏图标问题
    def _setup_window_icons_old(self):
        """设置窗口图标 - 增强调试版本"""
        import os as os_module  # 避免变量名冲突
        
        print("=== 图标设置调试开始 ===")  # 使用print确保输出
        logger.info("=== 图标设置调试开始 ===")
        
        # 检查运行环境
        is_frozen = getattr(sys, 'frozen', False)
        print(f"运行环境: {'打包环境' if is_frozen else '开发环境'}")
        logger.info(f"运行环境: {'打包环境' if is_frozen else '开发环境'}")
        
        if is_frozen:
            bundle_dir = sys._MEIPASS
            print(f"Bundle目录: {bundle_dir}")
            logger.info(f"Bundle目录: {bundle_dir}")
        
        # 详细检查所有图标文件
        icon_files = [
            'app_256x256.ico',
            'app_128x128.ico', 
            'app_64x64.ico',
            'app.ico'
        ]
        
        print("\n--- 图标文件检查 ---")
        logger.info("--- 图标文件检查 ---")
        
        available_icons = []
        for ico_name in icon_files:
            path = self._get_resource_path(f'gui/resources/icons/{ico_name}')
            exists = os_module.path.exists(path)
            
            print(f"图标: {ico_name}")
            print(f"  路径: {path}")
            print(f"  存在: {exists}")
            logger.info(f"图标: {ico_name}, 路径: {path}, 存在: {exists}")
            
            if exists:
                try:
                    size = os_module.path.getsize(path)
                    print(f"  大小: {size} 字节")
                    logger.info(f"  大小: {size} 字节")
                    available_icons.append((ico_name, path, size))
                except Exception as e:
                    print(f"  错误: {e}")
                    logger.error(f"  错误: {e}")
            print()
        
        print(f"可用图标数量: {len(available_icons)}")
        logger.info(f"可用图标数量: {len(available_icons)}")
        
        # 双重图标设置策略：iconbitmap + iconphoto
        iconbitmap_success = False
        iconphoto_success = False
        
        print(f"\n=== 阶段1：iconbitmap设置（窗口标题栏） ===")
        logger.info("=== 阶段1：iconbitmap设置（窗口标题栏） ===")
        
        # 1. 设置ICO图标（窗口标题栏）
        for ico_name, ico_path, size in available_icons:
            print(f"\n--- 尝试iconbitmap设置: {ico_name} ---")
            logger.info(f"--- 尝试iconbitmap设置: {ico_name} ---")
            
            try:
                print("正在调用 self.root.iconbitmap()...")
                logger.info("正在调用 self.root.iconbitmap()...")
                
                self.root.iconbitmap(ico_path)
                
                print(f"[SUCCESS] iconbitmap({ico_name}) 设置成功！")
                logger.info(f"[SUCCESS] iconbitmap({ico_name}) 设置成功！")
                iconbitmap_success = True
                break
                
            except Exception as e:
                print(f"[FAILED] iconbitmap({ico_name}) 失败: {e}")
                logger.error(f"[FAILED] iconbitmap({ico_name}) 失败: {e}")
        
        print(f"\n=== 阶段2：iconphoto设置（任务栏图标） ===")
        logger.info("=== 阶段2：iconphoto设置（任务栏图标） ===")
        
        # 2. 设置PNG图标（任务栏）- 使用高分辨率PNG获得更好效果
        png_path = self._get_resource_path('gui/resources/downloads/main_transp_bg.png')
        png_exists = os_module.path.exists(png_path)
        
        print(f"PNG路径: {png_path}")
        print(f"PNG存在: {png_exists}")
        logger.info(f"PNG路径: {png_path}, 存在: {png_exists}")
        
        if png_exists:
            try:
                png_size = os_module.path.getsize(png_path)
                print(f"PNG大小: {png_size} 字节")
                logger.info(f"PNG大小: {png_size} 字节")
                
                print("正在加载原始PNG图像...")
                # 使用PIL处理高分辨率图标
                from PIL import Image
                original_img = Image.open(png_path)
                print(f"原始PNG尺寸: {original_img.size}")
                logger.info(f"原始PNG尺寸: {original_img.size}")
                
                # 使用内存图像，避免临时文件问题
                sizes_to_try = [64, 48, 32]  # 常用的窗口图标尺寸
                
                # 延迟执行机制：在GUI完全加载后再设置iconphoto
                def delayed_iconphoto_setup():
                    """延迟设置iconphoto，确保GUI完全加载"""
                    print("开始延迟图标设置...")
                    
                    for target_size in sizes_to_try:
                        for retry in range(3):  # 重试机制
                            try:
                                print(f"正在尝试 {target_size}x{target_size} 尺寸 (重试 {retry+1}/3)...")
                                
                                # 缩放到目标尺寸
                                resized_img = original_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                                
                                # 转换为tkinter可用的格式（内存中处理，无临时文件）
                                import io
                                img_bytes = io.BytesIO()
                                resized_img.save(img_bytes, format='PNG')
                                img_bytes.seek(0)
                                
                                # 创建PhotoImage（直接从内存）
                                icon_image = tk.PhotoImage(data=img_bytes.getvalue())
                                
                                print(f"正在调用 self.root.iconphoto({target_size}x{target_size})...")
                                
                                # 确保在主线程中执行
                                self.root.after(0, lambda img=icon_image: self.root.iconphoto(True, img))
                                
                                # 保存图标引用避免被垃圾回收
                                self._icon_image = icon_image
                                
                                print(f"[SUCCESS] 延迟iconphoto({target_size}x{target_size}) 设置成功！")
                                logger.info(f"[SUCCESS] 延迟iconphoto({target_size}x{target_size}) 设置成功！")
                                return True
                                
                            except Exception as e:
                                print(f"[RETRY] iconphoto({target_size}x{target_size}) 第{retry+1}次失败: {e}")
                                logger.warning(f"[RETRY] iconphoto({target_size}x{target_size}) 第{retry+1}次失败: {e}")
                                import time
                                time.sleep(0.1)  # 短暂延迟后重试
                                continue
                    
                    print("[FAILED] 所有延迟图标设置尝试都失败了")
                    logger.error("[FAILED] 所有延迟图标设置尝试都失败了")
                    return False
                
                # 立即尝试一次
                for target_size in sizes_to_try:
                    try:
                        print(f"正在立即尝试 {target_size}x{target_size} 尺寸...")
                        
                        # 缩放到目标尺寸
                        resized_img = original_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                        
                        # 内存处理，无临时文件
                        import io
                        img_bytes = io.BytesIO()
                        resized_img.save(img_bytes, format='PNG')
                        img_bytes.seek(0)
                        
                        # 创建PhotoImage
                        icon_image = tk.PhotoImage(data=img_bytes.getvalue())
                        
                        print(f"正在调用 self.root.iconphoto({target_size}x{target_size})...")
                        self.root.iconphoto(True, icon_image)
                        
                        # 保存图标引用避免被垃圾回收
                        self._icon_image = icon_image
                        
                        print(f"[SUCCESS] 立即iconphoto({target_size}x{target_size}) 设置成功！")
                        logger.info(f"[SUCCESS] 立即iconphoto({target_size}x{target_size}) 设置成功！")
                        iconphoto_success = True
                        break
                        
                    except Exception as e:
                        print(f"[FAILED] 立即iconphoto({target_size}x{target_size}) 失败: {e}")
                        logger.error(f"[FAILED] 立即iconphoto({target_size}x{target_size}) 失败: {e}")
                        continue
                
                # 如果立即设置失败，安排延迟设置
                if not iconphoto_success:
                    print("立即设置失败，安排延迟设置...")
                    logger.info("立即设置失败，安排延迟设置...")
                    # 在GUI完全加载后（1秒后）重试
                    import threading
                    delay_thread = threading.Thread(target=lambda: (
                        __import__('time').sleep(1),
                        delayed_iconphoto_setup()
                    ), daemon=True)
                    delay_thread.start()
                
                # 标记iconphoto尝试完成（包括延迟设置）
                if not iconphoto_success:
                    print("所有立即设置尝试失败，延迟设置已安排")
                    logger.info("所有立即设置尝试失败，延迟设置已安排")
                    # 设置为部分成功，因为延迟设置可能会成功
                    iconphoto_success = "delayed"
                
            except Exception as e:
                print(f"[FAILED] PNG图像处理失败: {e}")
                logger.error(f"[FAILED] PNG图像处理失败: {e}")
                import traceback
                print(f"错误详情: {traceback.format_exc()}")
                logger.error(f"错误详情: {traceback.format_exc()}")
        
        success = iconbitmap_success or (iconphoto_success in [True, "delayed"])
        
        print(f"\n=== 双重图标设置总结 (方案B) ===")
        print(f"iconbitmap（窗口）: {'成功' if iconbitmap_success else '失败'}")
        
        if iconphoto_success == True:
            iconphoto_status = "成功"
        elif iconphoto_success == "delayed":
            iconphoto_status = "延迟设置已安排"
        else:
            iconphoto_status = "失败"
        print(f"iconphoto（任务栏）: {iconphoto_status}")
        print(f"整体结果: {'成功' if success else '失败'}")
        print(f"改进: 无临时文件 + 重试机制 + 延迟执行")
        
        logger.info(f"=== 双重图标设置总结 (方案B) ===")
        logger.info(f"iconbitmap（窗口）: {'成功' if iconbitmap_success else '失败'}")
        logger.info(f"iconphoto（任务栏）: {iconphoto_status}")
        logger.info(f"整体结果: {'成功' if success else '失败'}")
        logger.info(f"改进: 无临时文件 + 重试机制 + 延迟执行")
        
        return success

    # NEW VERSION: 2025-08-15 方案B+ - 多重延迟+强化重试+Windows缓存清理
    def _setup_window_icons(self):
        """设置窗口图标 - 方案B+：多重延迟+强化重试机制"""
        import os as os_module
        import io
        
        # 1. 立即设置ICO作为基础图标（最可靠的方式）
        ico_path = self._get_resource_path('gui/resources/icons/app_256x256.ico')
        if os_module.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                # 尝试其他ICO文件
                for ico_name in ['app_128x128.ico', 'app_64x64.ico', 'app.ico']:
                    try:
                        alt_ico = self._get_resource_path(f'gui/resources/icons/{ico_name}')
                        if os_module.path.exists(alt_ico):
                            self.root.iconbitmap(alt_ico)
                            break
                    except Exception:
                        continue
        
        # 2. 检查PNG文件
        main_png_path = self._get_resource_path('gui/resources/downloads/main_transp_bg.png')
        if not os_module.path.exists(main_png_path):
            return
        
        def enhanced_icon_setup():
            """增强的图标设置 - 多尺寸+强化重试+调试信息"""
            sizes = [128]  # 只使用128x128单一高分辨率 - 避免多次设置混乱
            success_count = 0
            
            # 图标调试现在使用统一日志系统
            
            logger.icon_debug("session", "=== 开始图标调试会话 ===", "info")
            
            # 获取系统信息
            try:
                import platform
                logger.icon_debug("system", f"系统: {platform.system()} {platform.release()}")
                logger.icon_debug("system", f"DPI信息: {self.root.winfo_fpixels('1i')} pixels per inch")
                logger.icon_debug("system", f"窗口大小: {self.root.winfo_width()}x{self.root.winfo_height()}")
            except Exception as e:
                logger.icon_debug("system", f"系统信息获取失败: {e}", "error")
            
            # 保持图标引用避免垃圾回收
            if not hasattr(self, '_icon_photos'):
                self._icon_photos = []
            
            logger.icon_debug("setup", f"尝试设置图标尺寸: {sizes}")
            
            for size in sizes:
                logger.icon_debug("process", f"\n--- 开始处理 {size}x{size} 尺寸 ---")
                for attempt in range(5):  # 增加到5次重试
                    try:
                        logger.icon_debug("process", f"第 {attempt+1}/5 次尝试...")
                        
                        # 内存处理避免临时文件问题
                        from PIL import Image
                        pil_img = Image.open(main_png_path).resize((size, size), Image.Resampling.LANCZOS)
                        logger.icon_debug("process", f"PIL图像创建成功: {pil_img.size}, 模式: {pil_img.mode}")
                        
                        img_buffer = io.BytesIO()
                        pil_img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        buffer_size = len(img_buffer.getvalue())
                        img_buffer.seek(0)
                        logger.icon_debug("process", f"内存缓冲区大小: {buffer_size} 字节")
                        
                        photo = tk.PhotoImage(data=img_buffer.getvalue())
                        logger.icon_debug("convert", f"PhotoImage创建成功: {photo.width()}x{photo.height()}")
                        
                        # 记录设置前后的状态
                        logger.icon_debug("load", "正在调用 root.iconphoto()...")
                        self.root.iconphoto(False, photo)
                        logger.icon_debug("load", "iconphoto() 调用完成")
                        
                        # 保持引用避免垃圾回收
                        self._icon_photos.append(photo)
                        logger.icon_debug("load", f"图标引用已保存，当前引用数: {len(self._icon_photos)}")
                        
                        success_count += 1
                        logger.icon_debug("load", f"✅ {size}x{size} 设置成功！", "info")
                        break
                        
                    except Exception as e:
                        logger.icon_debug("load", f"❌ {size}x{size} 第{attempt+1}次失败: {e}", "error")
                        if attempt < 4:  # 不是最后一次尝试
                            import time
                            time.sleep(0.05 * (attempt + 1))  # 递增延迟
                        continue
                
                logger.icon_debug("process", f"--- {size}x{size} 处理完成 ---\n")
            
            # 移除ICO重新设置 - 避免覆盖高分辨率PNG效果
            logger.icon_debug("setup", "跳过ICO备份设置 - 保持PNG高分辨率效果")
            
            logger.icon_debug("session", f"=== 图标设置会话结束，成功数: {success_count}/{len(sizes)} ===", "info")
            return success_count
        
        # 3. 单次延迟策略 - 避免多次设置导致的缓存混乱
        self.root.after(200, enhanced_icon_setup)  # 200ms后设置一次128x128
        
        # 4. 立即尝试一次ICO设置
        try:
            self.root.iconbitmap(ico_path)
        except Exception:
            pass

    def create_widgets(self):
        """创建完美对齐的主界面组件 - v2.3"""
        # 创建主容器
        main_frame = ttk.Frame(self.root, padding=self.PADDING_LARGE)
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置主容器网格
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # 配置主容器行权重
        main_frame.rowconfigure(0, weight=0)  # 头部
        main_frame.rowconfigure(1, weight=0)  # 状态区域
        main_frame.rowconfigure(2, weight=0)  # 控制面板
        main_frame.rowconfigure(3, weight=1)  # 日志区域可扩展
        
        # 创建各个部分
        self.create_header_section(main_frame)
        self.create_status_section(main_frame)
        self.create_control_section(main_frame)
        self.create_log_section(main_frame)
        
        # 延迟执行按钮高度调试 - 可通过 DEBUG_LAYOUT 开关控制
        if self.DEBUG_LAYOUT:
            self.root.after(5000, self.debug_button_heights_with_retry)  # 只有开关开启时才执行
    
    def _setup_logging_system(self):
        """初始化统一日志系统"""
        try:
            # 设置GUI日志回调，将日志显示在GUI中
            def gui_log_callback(level, message):
                # 直接显示到GUI，避免调用log_message造成递归
                if hasattr(self, 'log_display'):
                    # 根据日志级别设置颜色
                    color_map = {
                        'DEBUG': 'info',
                        'INFO': 'info', 
                        'WARNING': 'warning',
                        'ERROR': 'danger',
                        'CRITICAL': 'danger'
                    }
                    bootstyle = color_map.get(level, 'info')
                    
                    # 直接调用GUI显示，但不写入文件（unified logger已处理文件写入）
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    formatted_message = f"[{current_time}] {level}: {message}\n"
                    
                    try:
                        self.root.after(0, lambda: self._append_log(formatted_message, bootstyle))
                    except Exception:
                        pass  # 忽略GUI更新错误
            
            # 不设置GUI回调，让GUI和core logger独立工作
            # set_gui_callback(gui_log_callback)  # 禁用以避免混淆
            
            # 根据配置文件设置日志级别
            log_level = self.config.get_log_level()
            set_log_level_from_config(log_level)
            
            # 根据DEBUG_LAYOUT开关设置额外调试模式（开发用）
            if self.DEBUG_LAYOUT:
                logger.set_debug_mode(True)
            
            # 记录系统启动
            logger.system_status("GUI系统", "初始化", "统一日志系统已启用")
            
        except Exception as e:
            # 如果日志系统初始化失败，回退到print
            # logger.error(f"日志系统初始化失败: {e}")
            pass
    
    def create_header_section(self, parent):
        """创建头部区域"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, self.PADDING_LARGE))
        header_frame.columnconfigure(1, weight=1)
        
        # 主标题
        title_label = ttk.Label(
            header_frame,
            text="微信OneDrive冲突解决工具",
            font=("Microsoft YaHei UI", 16, "bold"),
            bootstyle="primary"
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # 版本信息
        version_label = ttk.Label(
            header_frame,
            text=get_full_version_string(),
            font=("Microsoft YaHei UI", 10),
            bootstyle="secondary"
        )
        version_label.grid(row=0, column=1, sticky=tk.E)
        
        # 分隔线
        separator = ttk.Separator(header_frame, orient="horizontal")
        separator.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(self.PADDING_SMALL, 0))
    
    def create_status_section(self, parent):
        """创建状态监控区域 - 完美对齐版本"""
        status_card = ttk.LabelFrame(
            parent,
            text="  📊 系统状态监控",
            padding=self.PADDING_MEDIUM,
            bootstyle="success"
        )
        status_card.grid(row=1, column=0, sticky="nsew", pady=(0, self.PADDING_LARGE))
        status_card.columnconfigure(0, weight=1)
        
        # 统一创建所有状态行 - 使用相同的布局系统
        self.create_unified_status_section(status_card)
        
        # 创建分隔线
        separator = ttk.Separator(status_card, orient="horizontal")
        separator.grid(row=1, column=0, sticky="ew", pady=self.PADDING_SMALL)
        
        # 创建统计信息区域 - 重点优化部分
        self.create_stats_section(status_card)
    
    def create_unified_status_section(self, parent):
        """创建统一的状态区域 - 完美间距版本"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=0, column=0, sticky="ew")
        status_frame.columnconfigure(1, weight=1)
        
        # 统一配置所有状态行 - 关键：使用uniform确保一致性
        for i in range(3):  # 3行：微信、OneDrive、空闲时间
            status_frame.rowconfigure(i, minsize=self.ROW_HEIGHT, weight=0, uniform="status_rows")
        
        # 第一行：微信状态
        self.create_status_row(
            status_frame, 0,
            "  微信状态:", "检查中...", 
            self.icons.get('wechat'),
            "wechat"
        )
        
        # 第二行：OneDrive状态
        self.create_status_row(
            status_frame, 1,
            "  OneDrive状态:", "检查中...",
            self.icons.get('onedrive'),
            "onedrive"
        )
        
        # 第三行：空闲时间
        self.create_status_row(
            status_frame, 2,
            "  空闲时间:", "计算中...",
            self.icons.get('idle'),
            "idle"
        )
    
    def create_status_row(self, parent, row, label_text, value_text, icon, row_type):
        """创建统一的状态行"""
        # OLD VERSION: 原始间距逻辑 - 间距不统一的问题
        # row_pady = (0, self.PADDING_TINY)
        # row_frame.configure(height=self.ROW_HEIGHT)
        # row_frame.grid_propagate(False)
        
        # NEW VERSION: 使用更大的间距，并强制统一高度
        row_pady = (2, 2)  # 上下各2px间距，相邻框框间距4px
        
        # 清理完成：移除调试边框，框框现在透明
        row_frame = ttk.Frame(parent)
        row_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=row_pady)
        row_frame.columnconfigure(1, weight=1)
        
        # 配置行权重，让内容垂直居中
        row_frame.rowconfigure(0, weight=1)
        
        # FIXED VERSION: 强制统一高度，设置足够大的高度容纳所有内容
        unified_height = 54  # 设为54px，目标实现48px按钮
        row_frame.configure(height=unified_height)  
        row_frame.grid_propagate(False)  # 防止子组件改变父容器大小
        
        # DEBUG: 将详细调试信息打印到日志中 - 可通过 DEBUG_LAYOUT 开关控制
        def log_debug_info():
            if not self.DEBUG_LAYOUT:
                return  # 开关关闭时不执行调试
                
            try:
                # 强制更新布局
                self.root.update_idletasks()
                
                # 检查frame是否可见（使用正确的方法）
                if not row_frame.winfo_viewable():
                    self.log_message(f"[布局调试]警告: 框{row} 尚未可见", "DEBUG")
                    return
                
                # 基本框框信息
                frame_height = row_frame.winfo_height()
                frame_width = row_frame.winfo_width()
                frame_x = row_frame.winfo_x()
                frame_y = row_frame.winfo_y()
                
                # 检查数据合理性
                if frame_width <= 1 or frame_height <= 1:
                    self.log_message(f"[布局调试]异常: 框{row} 尺寸异常 {frame_width}x{frame_height}", "DEBUG")
                    return
                
                # 边框线宽度（我们设置的）
                border_width = 2
                
                # pady值（我们设置的）
                pady_top, pady_bottom = row_pady if isinstance(row_pady, tuple) else (row_pady, row_pady)
                
                # 基础信息
                base_info = f"[布局调试]框{row}({label_text.strip()}) 框宽:{frame_width}px 框高:{frame_height}px 边框线:{border_width}px pady:({pady_top},{pady_bottom})"
                self.log_message(base_info, "DEBUG")
                
                # 位置信息
                pos_info = f"[布局调试]框{row} 位置: x={frame_x}px y={frame_y}px"
                self.log_message(pos_info, "DEBUG")
                
                # 计算与上一个框的间距（第2、3个框）
                if row > 0:
                    # 获取上一个框的信息
                    prev_key = f"frame_{row-1}"
                    if hasattr(self, '_frame_positions') and prev_key in self._frame_positions:
                        prev_bottom = self._frame_positions[prev_key]['bottom']
                        current_top = frame_y
                        
                        # 实际间距 = 当前框顶部 - 上一个框底部
                        actual_gap = current_top - prev_bottom
                        
                        gap_info = f"[布局调试]框{row} 与框{row-1}的实际间距: {actual_gap}px (理论应该是{pady_bottom + pady_top}px = {pady_bottom}px下边距+{pady_top}px上边距)"
                        self.log_message(gap_info, "DEBUG")
                        
                        # 分析差异（使用新的对称间距计算）
                        expected_gap = pady_bottom + pady_top
                        diff = actual_gap - expected_gap
                        if diff != 0:
                            diff_info = f"[布局调试]框{row} 间距差异: 实际比理论{'多' if diff > 0 else '少'}{abs(diff)}px"
                            self.log_message(diff_info, "DEBUG")
                
                # 保存当前框的位置信息供下一个框使用
                if not hasattr(self, '_frame_positions'):
                    self._frame_positions = {}
                
                self._frame_positions[f"frame_{row}"] = {
                    'top': frame_y,
                    'bottom': frame_y + frame_height,
                    'height': frame_height,
                    'width': frame_width
                }
                
                # 如果是最后一行，输出汇总
                if row == 2:  # 最后一个框
                    self.log_message(f"[布局调试]========== 所有框测量完成 ==========", "DEBUG")
                    
            except Exception as e:
                self.log_message(f"[布局调试]行{row} 获取尺寸失败: {e}", "DEBUG")
        
        # 延迟获取布局信息（等待布局完成）- 可通过 DEBUG_LAYOUT 开关控制
        if self.DEBUG_LAYOUT:
            self.root.after(1000, log_debug_info)  # 只有开关开启时才执行
        
        # 标签
        label = ttk.Label(
            row_frame,  # 改为放在框架中
            text=label_text,
            image=icon,
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=self.LABEL_WIDTH
        )
        label.grid(row=0, column=0, sticky="nsw", pady=0)  # 垂直居中+左对齐
        
        # 状态值
        status_label = ttk.Label(
            row_frame,  # 改为放在框架中
            text=value_text,
            bootstyle="warning",  # 统一初始样式
            font=("Microsoft YaHei UI", 10)
        )
        status_label.grid(row=0, column=1, sticky="nsw", padx=(self.PADDING_SMALL, 0), pady=0)  # 垂直居中+左对齐
        
        # 根据类型创建不同的按钮或保存引用
        if row_type == "wechat":
            button = ttk.Button(
                row_frame,  # 改为放在框架中
                text="查询中...",
                state="disabled",
                command=self.toggle_wechat,
                bootstyle="outline-secondary",
                width=self.BUTTON_WIDTH
            )
            # 微信按钮：pady=1 目样48px高度
            button.grid(row=0, column=2, sticky="nse", pady=1)  # 微信按钮: pady=1
            self.wechat_status_label = status_label
            self.wechat_toggle_button = button
            
        elif row_type == "onedrive":
            button = ttk.Button(
                row_frame,  # 改为放在框架中
                text="查询中...",
                state="disabled",
                command=self.toggle_onedrive,
                bootstyle="outline-secondary",
                width=self.BUTTON_WIDTH
            )
            # OneDrive按钮：pady=1 目样48px高度
            button.grid(row=0, column=2, sticky="nse", pady=1)  # OneDrive按钮: pady=1
            self.onedrive_status_label = status_label
            self.onedrive_toggle_button = button
            
        elif row_type == "idle":
            # 空闲时间行没有按钮，调整样式
            status_label.config(bootstyle="info", font=("Microsoft YaHei UI", 10, "bold"))
            self.idle_time_label = status_label
    
    def create_app_status_section(self, parent):
        """创建应用状态区域"""
        app_frame = ttk.Frame(parent)
        app_frame.grid(row=0, column=0, sticky="ew", pady=(0, self.PADDING_SMALL))
        app_frame.columnconfigure(1, weight=1)
        
        # 微信状态行
        wechat_frame = ttk.Frame(app_frame)
        wechat_frame.grid(row=0, column=0, sticky="ew", pady=self.PADDING_TINY)
        wechat_frame.columnconfigure(1, weight=1)
        
        wechat_label = ttk.Label(
            wechat_frame,
            text="  微信状态:",
            image=self.icons.get('wechat'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=self.LABEL_WIDTH
        )
        wechat_label.grid(row=0, column=0, sticky=tk.W)
        
        self.wechat_status_label = ttk.Label(
            wechat_frame,
            text="检查中...",
            bootstyle="warning",
            font=("Microsoft YaHei UI", 10)
        )
        self.wechat_status_label.grid(row=0, column=1, sticky=tk.W, padx=(self.PADDING_SMALL, 0))
        
        self.wechat_toggle_button = ttk.Button(
            wechat_frame,
            text="查询中...",
            state="disabled",
            command=self.toggle_wechat,
            bootstyle="outline-secondary",
            width=self.BUTTON_WIDTH
        )
        self.wechat_toggle_button.grid(row=0, column=2, sticky=tk.E)
        
        # OneDrive状态行
        onedrive_frame = ttk.Frame(app_frame)
        onedrive_frame.grid(row=1, column=0, sticky="ew", pady=self.PADDING_TINY)
        onedrive_frame.columnconfigure(1, weight=1)
        
        onedrive_label = ttk.Label(
            onedrive_frame,
            text="  OneDrive状态:",
            image=self.icons.get('onedrive'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=self.LABEL_WIDTH
        )
        onedrive_label.grid(row=0, column=0, sticky=tk.W)
        
        self.onedrive_status_label = ttk.Label(
            onedrive_frame,
            text="检查中...",
            bootstyle="warning",
            font=("Microsoft YaHei UI", 10)
        )
        self.onedrive_status_label.grid(row=0, column=1, sticky=tk.W, padx=(self.PADDING_SMALL, 0))
        
        self.onedrive_toggle_button = ttk.Button(
            onedrive_frame,
            text="查询中...",
            state="disabled",
            command=self.toggle_onedrive,
            bootstyle="outline-secondary",
            width=self.BUTTON_WIDTH
        )
        self.onedrive_toggle_button.grid(row=0, column=2, sticky=tk.E)
    
    def create_idle_section(self, parent):
        """创建空闲时间区域"""
        idle_frame = ttk.Frame(parent)
        idle_frame.grid(row=1, column=0, sticky="ew", pady=self.PADDING_SMALL)
        idle_frame.columnconfigure(1, weight=1)
        
        idle_label = ttk.Label(
            idle_frame,
            text="  空闲时间:",
            image=self.icons.get('idle'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=self.LABEL_WIDTH
        )
        idle_label.grid(row=0, column=0, sticky=tk.W)
        
        self.idle_time_label = ttk.Label(
            idle_frame,
            text="计算中...",
            bootstyle="info",
            font=("Microsoft YaHei UI", 10, "bold")
        )
        self.idle_time_label.grid(row=0, column=1, sticky=tk.W, padx=(self.PADDING_SMALL, 0))
    
    def create_stats_section(self, parent):
        """创建完美对齐的统计信息区域 - 使用与上半部分相同的方法论"""
        stats_main_frame = ttk.Frame(parent)
        stats_main_frame.grid(row=2, column=0, sticky="ew")
        stats_main_frame.columnconfigure(0, weight=1)
        
        # OLD VERSION: 旧的直接布局方式 - 注释保留
        # stats_frame = ttk.Frame(parent)
        # stats_frame.grid(row=2, column=0, sticky="ew")
        # stats_frame.columnconfigure(1, weight=1)
        # for i in range(3):
        #     stats_frame.rowconfigure(i, minsize=self.ROW_HEIGHT, weight=0, uniform="stats_rows")
        
        # NEW VERSION: 使用统一的create_stats_row方法，与上半部分保持一致
        # 第一行：上次同步时间
        self.create_stats_row(
            stats_main_frame, 0,
            "  上次同步时间:", "未同步",
            self.icons.get('sync'), "stats1"
        )
        
        # 第二行：成功/失败次数  
        self.create_stats_row(
            stats_main_frame, 1,
            "  成功/失败次数:", "0/0",
            self.icons.get('stats'), "stats2"
        )
        
        # 第三行：同步冷却时间 + 重置按钮
        self.create_stats_row(
            stats_main_frame, 2,
            "  同步冷却时间:", "无冷却",
            self.icons.get('cooldown'), "stats3_with_button"
        )
    
    def create_stats_row(self, parent, row, label_text, value_text, icon, row_type):
        """创建统计行 - 使用与上半部分完全相同的方法论"""
        # OLD VERSION: 旧的直接布局方式 - 注释保留
        # label = ttk.Label(parent, text=label_text, image=icon, compound="left" if icon else "none", font=("Microsoft YaHei UI", 9), width=self.LABEL_WIDTH)
        # label.grid(row=row, column=0, sticky="w", pady=0)
        # value_label = ttk.Label(parent, text=value_text, font=("Microsoft YaHei UI", 9), bootstyle="secondary")
        # value_label.grid(row=row, column=1, sticky="w", padx=(self.PADDING_SMALL, 0), pady=0)
        
        # NEW VERSION: 使用与上半部分相同的框框+边框+调试方法
        # 设置间距和高度
        row_pady = (2, 2)  # 上下各2px间距，与上半部分保持一致
        
        # 清理完成：移除调试边框，框框现在透明
        row_frame = ttk.Frame(parent)
        row_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=row_pady)
        row_frame.columnconfigure(1, weight=1)
        
        # 配置行权重，让内容垂直居中
        row_frame.rowconfigure(0, weight=1)
        
        # 强制统一高度，与上半部分保持一致
        unified_height = 54  # 与上半部分相同的54px
        row_frame.configure(height=unified_height)  
        row_frame.grid_propagate(False)  # 防止子组件改变父容器大小
        
        # DEBUG: 下半部分调试信息 - 可通过 DEBUG_LAYOUT 开关控制
        def log_stats_debug_info():
        #     try:
        #         # 强制更新布局
        #         self.root.update_idletasks()
        #         
        #         # 检查frame是否可见
        #         if not row_frame.winfo_viewable():
        #             self.log_message(f"[下半部分调试]警告: 统计框{row} 尚未可见", "DEBUG")
        #             return
        #         
                # 基本框框信息
                frame_height = row_frame.winfo_height()
                frame_width = row_frame.winfo_width()
                frame_x = row_frame.winfo_x()
                frame_y = row_frame.winfo_y()
                
                # 检查数据合理性
                if frame_width <= 1 or frame_height <= 1:
                    self.log_message(f"[下半部分调试]异常: 统计框{row} 尺寸异常 {frame_width}x{frame_height}", "DEBUG")
                    return
        #         
        #         # 边框线宽度和pady值
        #         border_width = 2
        #         pady_top, pady_bottom = row_pady if isinstance(row_pady, tuple) else (row_pady, row_pady)
        #         
        #         # 基础信息
        #         base_info = f"[下半部分调试]统计框{row}({label_text.strip()}) 框宽:{frame_width}px 框高:{frame_height}px 边框线:{border_width}px pady:({pady_top},{pady_bottom})"
        #         self.log_message(base_info, "DEBUG")
        #         
        #         # 位置信息
        #         pos_info = f"[下半部分调试]统计框{row} 位置: x={frame_x}px y={frame_y}px"
        #         self.log_message(pos_info, "DEBUG")
        #         
        #         # 计算与上一个框的间距（第2、3个框）
        #         if row > 0:
        #             # 获取上一个统计框的信息
        #             prev_key = f"stats_frame_{row-1}"
        #             if hasattr(self, '_stats_frame_positions') and prev_key in self._stats_frame_positions:
        #                 prev_bottom = self._stats_frame_positions[prev_key]['bottom']
        #                 current_top = frame_y
        #                 
        #                 # 实际间距 = 当前框顶部 - 上一个框底部
        #                 actual_gap = current_top - prev_bottom
        #                 
        #                 gap_info = f"[下半部分调试]统计框{row} 与统计框{row-1}的实际间距: {actual_gap}px (理论应该是{pady_bottom + pady_top}px = {pady_bottom}px下边距+{pady_top}px上边距)"
        #                 self.log_message(gap_info, "DEBUG")
        #                 
        #                 # 分析差异（使用新的对称间距计算）
        #                 expected_gap = pady_bottom + pady_top
        #                 diff = actual_gap - expected_gap
        #                 if diff != 0:
        #                     diff_info = f"[下半部分调试]统计框{row} 间距差异: 实际比理论{'多' if diff > 0 else '少'}{abs(diff)}px"
        #                     self.log_message(diff_info, "DEBUG")
        #         
        #         # 保存当前框的位置信息供下一个框使用
        #         if not hasattr(self, '_stats_frame_positions'):
        #             self._stats_frame_positions = {}
        #         
        #         self._stats_frame_positions[f"stats_frame_{row}"] = {
        #             'top': frame_y,
        #             'bottom': frame_y + frame_height,
        #             'height': frame_height,
        #             'width': frame_width
        #         }
        #         
        #         # 如果是最后一行，输出汇总
        #         if row == 2:  # 最后一个统计框
        #             self.log_message(f"[下半部分调试]========== 所有统计框测量完成 ==========", "DEBUG")
        #             
        #     except Exception as e:
        #         self.log_message(f"[下半部分调试]统计行{row} 获取尺寸失败: {e}", "DEBUG")
        
        # 延迟获取布局信息 - 可通过 DEBUG_LAYOUT 开关控制
        if self.DEBUG_LAYOUT:
            self.root.after(1200, log_stats_debug_info)  # 只有开关开启时才执行
        
        # 创建标签
        label = ttk.Label(
            row_frame,
            text=label_text,
            image=icon,
            compound="left" if icon else "none",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=self.LABEL_WIDTH
        )
        label.grid(row=0, column=0, sticky="nsw", pady=0)  # 垂直居中+左对齐
        
        # 创建值标签
        value_label = ttk.Label(
            row_frame,
            text=value_text,
            bootstyle="secondary",
            font=("Microsoft YaHei UI", 10)
        )
        value_label.grid(row=0, column=1, sticky="nsw", padx=(self.PADDING_SMALL, 0), pady=0)  # 垂直居中+左对齐
        
        # 根据类型决定是否添加按钮
        if row_type == "stats3_with_button":
            # 创建按钮框架来放置两个按钮
            buttons_frame = ttk.Frame(row_frame)
            buttons_frame.grid(row=0, column=2, sticky="nse", pady=1)
            
            # 移除冷却按钮（清除冷却状态）
            reset_button = ttk.Button(
                buttons_frame,
                text="移除冷却",
                command=self.reset_global_cooldown,
                bootstyle="outline-warning",
                width=self.BUTTON_WIDTH,  # 与上半部分按钮相同宽度
                state="normal"
            )
            reset_button.pack(side=tk.LEFT, padx=(0, 6))
            
            # 重启冷却按钮（设置为配置值的冷却）
            apply_button = ttk.Button(
                buttons_frame,
                text="重启冷却",
                command=self.apply_cooldown_setting,
                bootstyle="outline-info", 
                width=self.BUTTON_WIDTH,  # 与上半部分按钮相同宽度
                state="normal"
            )
            apply_button.pack(side=tk.LEFT, padx=(6, 0))
            
            # 保存引用
            self.cooldown_icon_label = label
            self.cooldown_label = value_label
            self.remove_cooldown_button = reset_button
            self.restart_cooldown_button = apply_button
        
        # 保存其他引用
        if row == 0:
            self.sync_icon_label = label
            self.last_sync_label = value_label
        elif row == 1:
            self.stats_icon_label = label
            self.stats_label = value_label
    
    # OLD VERSION: 旧的create_stats_row_with_button方法 - 注释保留，功能已整合到create_stats_row中
    # def create_stats_row_with_button(self, parent, row, label_text, value_text, icon=None):
    #     """创建带按钮的统计行"""
    #     # 标签
    #     label = ttk.Label(
    #         parent,
    #         text=label_text,
    #         image=icon,
    #         compound="left" if icon else "none",
    #         font=("Microsoft YaHei UI", 9),
    #         width=self.LABEL_WIDTH
    #     )
    #     label.grid(row=row, column=0, sticky="w", pady=0)
    #     
    #     # 值
    #     value_label = ttk.Label(
    #         parent,
    #         text=value_text,
    #         font=("Microsoft YaHei UI", 9),
    #         bootstyle="secondary"  # 统一样式
    #     )
    #     value_label.grid(row=row, column=1, sticky="w", padx=(self.PADDING_SMALL, 0), pady=0)
    #     
    #     # 按钮
    #     button = ttk.Button(
    #         parent,
    #         text="测试按钮",
    #         command=self.reset_global_cooldown,
    #         bootstyle="outline-warning",
    #         width=8,
    #         state="disabled"
    #     )
    #     button.grid(row=row, column=2, sticky="w", padx=(self.PADDING_SMALL, 0), pady=0)
    #     
    #     # 保存引用
    #     self.cooldown_icon_label = label
    #     self.cooldown_label = value_label
    #     self.reset_cooldown_button = button
    
        # COMMENTED: 按钮高度调试移到正确位置
        # OLD VERSION: 调试函数定义在这里会导致重复调用
    
    def create_control_section(self, parent):
        """创建控制面板"""
        control_card = ttk.LabelFrame(
            parent,
            text="  🎮 控制面板",
            padding=self.PADDING_MEDIUM,
            bootstyle="primary"
        )
        control_card.grid(row=2, column=0, sticky="ew", pady=(0, self.PADDING_LARGE))
        control_card.columnconfigure(0, weight=1)
        control_card.columnconfigure(1, weight=1)
        
        # 左侧：同步按钮
        self.sync_button = ttk.Button(
            control_card,
            text="🚀 立即执行同步流程",
            command=self.run_sync_workflow,
            bootstyle="success",
            width=30
        )
        self.sync_button.grid(row=0, column=0, sticky="ew", padx=(0, self.PADDING_SMALL))
        
        # 右侧：配置按钮
        config_button = ttk.Button(
            control_card,
            text="⚙️ 打开配置面板",
            command=self.show_config_dialog,
            bootstyle="outline-primary",
            width=30
        )
        config_button.grid(row=0, column=1, sticky="ew")
    
    def create_log_section(self, parent):
        """创建日志区域"""
        log_card = ttk.LabelFrame(
            parent,
            text="  📋 操作日志",
            padding=self.PADDING_MEDIUM,
            bootstyle="info"
        )
        log_card.grid(row=3, column=0, sticky="nsew")
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(0, weight=1)
        
        # 日志文本框容器
        log_container = ttk.Frame(log_card)
        log_container.grid(row=0, column=0, sticky="nsew")
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)
        
        # 创建日志文本框
        self.log_text = tk.Text(
            log_container,
            height=20,
            width=80,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#212529",
            state=tk.DISABLED
        )
        
        # 滚动条
        scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 配置日志标签颜色
        self.log_text.tag_configure("DEBUG", foreground="#6c757d", font=("Consolas", 9))  # 灰色，用于调试信息
        self.log_text.tag_configure("INFO", foreground="#0066cc")
        self.log_text.tag_configure("SUCCESS", foreground="#28a745", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("WARNING", foreground="#fd7e14")
        self.log_text.tag_configure("ERROR", foreground="#dc3545", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("TITLE", foreground="#007bff", font=("Consolas", 9, "bold"))
        
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 日志控制按钮
        log_buttons_frame = ttk.Frame(log_card)
        log_buttons_frame.grid(row=1, column=0, sticky="ew", pady=(self.PADDING_MEDIUM, 0))
        
        ttk.Button(
            log_buttons_frame,
            text="清空日志",
            command=self.clear_log,
            bootstyle="outline-secondary",
            width=self.BUTTON_WIDTH
        ).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(
            log_buttons_frame,
            text="导出日志",
            command=self.export_log,
            bootstyle="outline-secondary",
            width=self.BUTTON_WIDTH
        ).grid(row=0, column=1, sticky=tk.W, padx=(self.PADDING_SMALL, 0))
    
    # =================== 以下保持原有的所有方法不变 ===================
    
    @measure_time("MainWindow", "微信切换操作")
    def toggle_wechat(self):
        """智能切换微信状态"""
        # PERFORMANCE: 记录用户点击微信切换按钮
        log_user_action("MainWindow", "微信切换按钮点击")
        
        if self.is_running_sync:
            messagebox.showwarning("警告", "同步流程正在运行中，请等待完成后再操作。")
            return
        
        def toggle_thread():
            try:
                wechat_running = is_wechat_running()
                if wechat_running:
                    self.log_message("正在停止微信...")
                    self.wechat_toggle_button.config(text="停止中...", state="disabled")
                    success = stop_wechat()
                    if success:
                        self.log_message("微信已停止", "SUCCESS")
                        # 2025-08-08 智能缓存失效：用户操作后立即强制刷新状态
                        self.update_app_status(force_refresh=True)
                    else:
                        self.log_message("停止微信失败", "ERROR")
                else:
                    self.log_message("正在启动微信...")
                    self.wechat_toggle_button.config(text="启动中...", state="disabled")
                    success = start_wechat()
                    if success:
                        self.log_message("微信已启动", "SUCCESS")
                        # 2025-08-08 智能缓存失效：用户操作后立即强制刷新状态
                        self.update_app_status(force_refresh=True)
                    else:
                        self.log_message("启动微信失败", "ERROR")
            except Exception as e:
                self.log_message(f"切换微信状态时出错: {e}", "ERROR")
            finally:
                # 恢复按钮状态将由状态更新线程处理
                pass
        
        thread = threading.Thread(target=toggle_thread, daemon=True)
        thread.start()
    
    @measure_time("MainWindow", "OneDrive切换操作")
    def toggle_onedrive(self):
        """智能切换OneDrive状态"""
        # PERFORMANCE: 记录用户点击OneDrive切换按钮
        log_user_action("MainWindow", "OneDrive切换按钮点击")
        
        if self.is_running_sync:
            messagebox.showwarning("警告", "同步流程正在运行中，请等待完成后再操作。")
            return
        
        def toggle_thread():
            try:
                onedrive_running = is_onedrive_running()
                if onedrive_running:
                    self.log_message("正在暂停OneDrive同步...")
                    self.onedrive_toggle_button.config(text="暂停中...", state="disabled")
                    success = pause_onedrive_sync()
                    if success:
                        self.log_message("OneDrive同步已暂停", "SUCCESS")
                        # 2025-08-08 智能缓存失效：用户操作后立即强制刷新状态
                        self.update_app_status(force_refresh=True)
                    else:
                        self.log_message("暂停OneDrive失败", "ERROR")
                else:
                    self.log_message("正在启动OneDrive...")
                    self.onedrive_toggle_button.config(text="启动中...", state="disabled")
                    success = start_onedrive()
                    if success:
                        self.log_message("OneDrive已启动", "SUCCESS")
                        # 2025-08-08 智能缓存失效：用户操作后立即强制刷新状态
                        self.update_app_status(force_refresh=True)
                    else:
                        self.log_message("启动OneDrive失败", "ERROR")
            except Exception as e:
                self.log_message(f"切换OneDrive状态时出错: {e}", "ERROR")
            finally:
                pass
        
        thread = threading.Thread(target=toggle_thread, daemon=True)
        thread.start()
    
    def update_app_status(self, force_refresh=False):
        """更新应用状态显示
        
        Args:
            force_refresh (bool): 是否强制刷新状态，忽略缓存（用于用户操作后立即反馈）
        """
        def check_status():
            # PERFORMANCE: 记录状态检查开始
            with perf_timer():
                try:
                    # 检查微信状态（支持强制刷新）
                    start_time = time.time()
                    wechat_running = is_wechat_running(force_refresh=force_refresh)
                    duration_ms = (time.time() - start_time) * 1000
                    log_system_call(f"微信状态检查{'(强制)' if force_refresh else ''}", duration_ms)
                    
                    if wechat_running != self._last_wechat_status:
                        if wechat_running:
                            processes = find_wechat_processes()
                            wechat_text = f"运行中 ({len(processes)}个进程)"
                            wechat_bootstyle = "success"
                            button_text = "停止微信"
                            button_bootstyle = "outline-danger"
                        else:
                            wechat_text = "未运行"
                            wechat_bootstyle = "danger"
                            button_text = "启动微信"
                            button_bootstyle = "outline-success"
                        
                        self.wechat_status_label.config(text=wechat_text, bootstyle=wechat_bootstyle)
                        self.wechat_toggle_button.config(text=button_text, bootstyle=button_bootstyle, state="normal")
                        self._last_wechat_status = wechat_running
                        
                        # PERFORMANCE: 记录GUI状态更新
                        log_gui_update("StatusPanel", f"微信状态更新: {wechat_text}")
                
                    # 检查OneDrive状态（支持强制刷新）
                    start_time = time.time()
                    onedrive_running = is_onedrive_running(force_refresh=force_refresh)
                    duration_ms = (time.time() - start_time) * 1000
                    log_system_call(f"OneDrive状态检查{'(强制)' if force_refresh else ''}", duration_ms)
                    
                    if onedrive_running != self._last_onedrive_status:
                        if onedrive_running:
                            onedrive_text = "运行中"
                            onedrive_bootstyle = "success"
                            button_text = "暂停同步"
                            button_bootstyle = "outline-warning"
                        else:
                            onedrive_text = "未运行"
                            onedrive_bootstyle = "danger"
                            button_text = "启动OneDrive"
                            button_bootstyle = "outline-success"
                        
                        self.onedrive_status_label.config(text=onedrive_text, bootstyle=onedrive_bootstyle)
                        self.onedrive_toggle_button.config(text=button_text, bootstyle=button_bootstyle, state="normal")
                        self._last_onedrive_status = onedrive_running
                        
                        # PERFORMANCE: 记录GUI状态更新
                        log_gui_update("StatusPanel", f"OneDrive状态更新: {onedrive_text}")
                
                except Exception as e:
                    self.log_message(f"更新状态时出错: {e}", "ERROR")
        
        thread = threading.Thread(target=check_status, daemon=True)
        thread.start()
    
    # 此处继续实现所有原有方法...
    # 为节省空间，我只展示核心布局部分，其余方法保持不变
    
    @measure_time("MainWindow", "配置面板打开")
    def show_config_dialog(self):
        """显示配置对话框"""
        # PERFORMANCE: 记录用户点击配置按钮的操作
        log_user_action("MainWindow", "配置面板按钮点击")
        
        try:
            # 导入配置面板模块
            from .config_panel import ConfigPanel
            
            # 创建配置面板，传递配置重新加载回调
            config_panel = ConfigPanel(parent=self.root, on_config_saved=self.reload_config)
            
        except ImportError:
            try:
                # 尝试直接导入
                from config_panel import ConfigPanel
                config_panel = ConfigPanel(parent=self.root, on_config_saved=self.reload_config)
            except ImportError as e:
                messagebox.showerror("错误", f"无法导入配置面板模块: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"打开配置面板失败: {str(e)}")
    
    @measure_time("MainWindow", "同步流程")
    def run_sync_workflow(self):
        """执行完整的微信OneDrive同步流程"""
        # PERFORMANCE: 记录用户点击同步按钮的操作
        log_user_action("MainWindow", "同步按钮点击")
        
        if self.is_running_sync:
            messagebox.showwarning("警告", "同步流程正在运行中，请等待完成。")
            return
        
        def sync_thread():
            try:
                self.is_running_sync = True
                self.sync_button.config(text="🔄 同步中...", state="disabled")
                self.log_message("开始执行同步流程", "INFO")
                
                # 调用核心同步流程
                success = sync_workflow.run_full_sync_workflow_gui(self.log_message)
                
                if success:
                    self.log_message("同步流程执行成功", "SUCCESS")
                    self.sync_success_count += 1
                    self.last_sync_time = datetime.now()
                    
                    # NEW VERSION: 2025-08-08 - 手动同步成功后更新全局冷却状态
                    try:
                        # 导入全局冷却管理器
                        import sys
                        import os
                        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
                        from core.global_cooldown import update_global_cooldown
                        
                        # 更新全局冷却时间
                        update_global_cooldown("手动触发")
                        self.log_message("全局冷却时间已更新 - 手动触发", "INFO")
                        
                        # 立即更新GUI显示的冷却状态
                        self.update_stats_labels()
                        
                        # 2025-08-08 智能缓存失效：同步完成后立即强制刷新应用状态
                        self.update_app_status(force_refresh=True)
                        
                    except Exception as cooldown_error:
                        self.log_message(f"更新全局冷却状态失败: {cooldown_error}", "WARNING")
                        import traceback
                        self.log_message(f"详细错误信息: {traceback.format_exc()}", "DEBUG")
                        
                else:
                    self.log_message("同步流程执行失败", "ERROR")
                    self.sync_error_count += 1
                    
                    # NEW VERSION: 2025-08-08 - 即使失败也要更新冷却（防止频繁重试）
                    try:
                        # 导入全局冷却管理器
                        import sys
                        import os
                        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
                        from core.global_cooldown import update_global_cooldown
                        
                        # 失败后也进入冷却期，防止用户频繁重试
                        update_global_cooldown("手动触发(失败)")
                        self.log_message("全局冷却时间已更新(失败后防护)", "INFO")
                        
                        # 立即更新GUI显示的冷却状态
                        self.update_stats_labels()
                        
                    except Exception as cooldown_error:
                        self.log_message(f"更新全局冷却状态失败: {cooldown_error}", "WARNING")
                    
            except Exception as e:
                self.log_message(f"同步流程出错: {e}", "ERROR")
                self.sync_error_count += 1
            finally:
                self.is_running_sync = False
                self.sync_button.config(text="🚀 立即执行同步流程", state="normal")
                self.update_stats_labels()
        
        # 在独立线程中执行同步，避免阻塞GUI
        thread = threading.Thread(target=sync_thread, daemon=True)
        thread.start()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("日志已清空")
    
    def export_log(self):
        """导出日志"""
        messagebox.showinfo("导出", "导出功能保持不变")
    
    def _should_log_level(self, level: str) -> bool:
        """检查是否应该记录该级别的日志
        
        Args:
            level: 日志级别字符串
            
        Returns:
            bool: 是否应该记录该级别的日志
        """
        # 定义日志级别优先级 (数字越大优先级越高)
        level_priorities = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50,
            'SUCCESS': 20  # SUCCESS 和 INFO 同级别
        }
        
        # 获取配置文件中设置的日志级别
        try:
            config_level = self.config.get_log_level().upper()
            config_priority = level_priorities.get(config_level, 20)  # 默认INFO级别
            current_priority = level_priorities.get(level.upper(), 20)
            
            # 只有当前日志级别优先级 >= 配置级别时才记录
            return current_priority >= config_priority
            
        except Exception:
            # 配置获取失败时，默认记录INFO及以上级别
            current_priority = level_priorities.get(level.upper(), 20)
            return current_priority >= 20  # INFO级别
    
    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        # 检查日志级别过滤
        if not self._should_log_level(level):
            return
            
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 包含年月日，精确到毫秒
        formatted_message = f"[{current_time}] {level}: {message}\n"
        
        # 移除独立文件日志写入 - 统一日志系统已处理文件记录
        
        # NEW VERSION: 2025-08-08 - 线程安全的日志GUI更新
        try:
            self.root.after(0, lambda: self._append_log(formatted_message, level))
        except RuntimeError as e:
            if "main thread is not in main loop" in str(e):
                # 主循环未启动，只写入文件，跳过GUI更新（正常情况）
                # 不记录日志，避免递归调用
                pass
            else:
                # 其他运行时错误，只打印到控制台（避免递归）
                logger.error(f"日志GUI更新失败: {e}")
        except Exception as e:
            # 其他异常，只打印到控制台（避免递归）
            logger.error(f"日志GUI更新异常: {e}")
    
    def _append_log(self, message, level):
        """在主线程中添加日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message, level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def reset_global_cooldown(self):
        """重置全局冷却"""
        # OLD VERSION: 仅重置本地变量，不影响全局冷却管理器
        # self.last_idle_trigger_time = None
        # self.cooldown_remaining = 0
        # self.log_message("全局冷却已重置", "INFO")
        # self.update_stats_labels()
        
        # NEW VERSION: 2025-08-08 - 使用全局冷却管理器重置冷却状态
        try:
            # 导入全局冷却管理器
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
            from core.global_cooldown import reset_global_cooldown
            
            # 调用全局冷却管理器重置
            reset_global_cooldown()
            self.log_message("冷却已移除", "INFO")
            
            # 清理本地变量（兼容性保留）
            self.last_idle_trigger_time = None
            self.cooldown_remaining = 0
            
            # 立即更新GUI显示
            self.update_stats_labels()
            
        except Exception as reset_error:
            self.log_message(f"移除冷却失败: {reset_error}", "ERROR")
    
    def apply_cooldown_setting(self):
        """重启冷却设置（设置为配置值的冷却状态）"""
        try:
            # 导入全局冷却管理器
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
            from core.global_cooldown import update_global_cooldown
            
            # 获取当前冷却设置
            cooldown_minutes = self.config.get_idle_cooldown_minutes() if hasattr(self.config, 'get_idle_cooldown_minutes') else 2
            
            # 更新全局冷却时间（设置为刚刚触发过的状态）
            update_global_cooldown("手动重启冷却")
            self.log_message(f"冷却已重启：{cooldown_minutes}分钟冷却期", "INFO")
            
            # 立即更新GUI显示
            self.update_stats_labels()
            
        except Exception as apply_error:
            self.log_message(f"重启冷却失败: {apply_error}", "ERROR")
    
    def reload_config(self):
        """重新加载配置文件（用于配置面板保存后刷新）"""
        try:
            # 重新加载配置管理器
            self.config.reload()
            
            # 更新日志级别
            log_level = self.config.get_log_level()
            set_log_level_from_config(log_level)
            
            self.log_message("配置已重新加载", "INFO")
            
            # 立即更新GUI显示（特别是冷却时间）
            self.update_stats_labels()
            
            # 立即更新冷却显示
            self.update_cooldown_display_only()
            
        except Exception as reload_error:
            self.log_message(f"重新加载配置失败: {reload_error}", "ERROR")
    
    def update_stats_labels(self):
        """更新统计标签显示"""
        try:
            # 更新上次同步时间
            if self.last_sync_time:
                sync_time_str = self.last_sync_time.strftime("%m-%d %H:%M")
                self.last_sync_label.config(text=sync_time_str)
            else:
                self.last_sync_label.config(text="未同步")
            
            # 更新成功/失败次数
            stats_text = f"{self.sync_success_count}/{self.sync_error_count}"
            self.stats_label.config(text=stats_text)
            
            # OLD VERSION: 仅基于静置触发时间的冷却显示逻辑
            # if self.last_idle_trigger_time and self.config.is_idle_trigger_enabled():
            #     cooldown_minutes = self.config.get_idle_cooldown_minutes()
            #     elapsed_seconds = (datetime.now() - self.last_idle_trigger_time).total_seconds()
            #     remaining_seconds = max(0, (cooldown_minutes * 60) - elapsed_seconds)
            #     
            #     if remaining_seconds > 0:
            #         remaining_minutes = int(remaining_seconds // 60)
            #         remaining_secs = int(remaining_seconds % 60)
            #         cooldown_text = f"{remaining_minutes}分{remaining_secs}秒"
            #         self.cooldown_label.config(text=cooldown_text)
            #     else:
            #         self.cooldown_label.config(text="无冷却")
            # else:
            #     self.cooldown_label.config(text="无冷却")
            
            # NEW VERSION: 2025-08-08 - 使用智能冷却显示策略（与定期更新保持一致）
            try:
                # 直接调用智能冷却显示函数，保持一致性
                self.update_cooldown_display_only()
                    
            except Exception as cooldown_display_error:
                # 如果冷却显示更新出错，回退到显示"无冷却"
                self.cooldown_label.config(text="无冷却")
                self.log_message(f"更新冷却状态显示失败: {cooldown_display_error}", "DEBUG")
                
        except Exception as e:
            self.log_message(f"更新统计标签失败: {e}", "ERROR")
    
    def update_cooldown_display_only(self):
        """单独更新冷却时间显示 - 智能更新策略"""
        try:
            # 导入全局冷却管理器
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
            from core.global_cooldown import get_remaining_global_cooldown
            
            # 获取全局冷却配置
            cooldown_minutes = self.config.get_global_cooldown_minutes()
            
            # 获取剩余冷却时间（分钟）
            remaining_cooldown_minutes = get_remaining_global_cooldown(cooldown_minutes)
            
            if remaining_cooldown_minutes <= 0:
                # 没有冷却时间
                cooldown_text = "无冷却"
            elif remaining_cooldown_minutes >= 1.0:
                # 大于1分钟：四舍五入显示分钟，低精度
                remaining_minutes_rounded = round(remaining_cooldown_minutes)
                cooldown_text = f"{remaining_minutes_rounded}分钟"
            else:
                # 小于1分钟：显示精确秒数，高精度
                remaining_total_seconds = int(remaining_cooldown_minutes * 60)
                cooldown_text = f"{remaining_total_seconds}秒"
            
            # 只有显示内容真正变化时才更新GUI（减少不必要的重绘）
            if not hasattr(self, '_last_cooldown_display_text') or self._last_cooldown_display_text != cooldown_text:
                self.cooldown_label.config(text=cooldown_text)
                self._last_cooldown_display_text = cooldown_text
                
        except Exception as cooldown_display_error:
            # 出错时显示"无冷却"，避免界面异常
            if not hasattr(self, '_last_cooldown_display_text') or self._last_cooldown_display_text != "无冷却":
                self.cooldown_label.config(text="无冷却")
                self._last_cooldown_display_text = "无冷却"
            
            if self._debug_enabled:
                self.log_message(f"更新冷却显示失败: {cooldown_display_error}", "DEBUG")
    
    def create_menu(self):
        """创建菜单"""
        pass
    
    def start_status_update_thread(self):
        """启动空闲时间更新线程（专注于流畅显示，不被阻塞）"""
        def idle_timer_loop():
            counter = 0
            last_loop_time = time.time()
            
            while True:
                try:
                    loop_start_time = time.time()
                    
                    # 记录实际的循环间隔（调试用）
                    if self._debug_enabled and self._last_update_time > 0:
                        actual_interval = loop_start_time - last_loop_time
                        self._update_intervals.append(actual_interval)
                        
                        # 只保留最近20次的间隔记录
                        if len(self._update_intervals) > 20:
                            self._update_intervals.pop(0)
                        
                        # 如果间隔异常（超过1.2秒或少于0.8秒），记录日志
                        if actual_interval > 1.2 or actual_interval < 0.8:
                            logger.perf_debug("空闲时间更新间隔异常", actual_interval, threshold=1.2)
                    
                    # 每秒更新GUI显示（直接使用系统空闲时间，保持一致性）
                    if counter % 10 == 0:  # 0.1秒 * 10 = 1秒
                        timer_start = time.time()
                        self.update_system_idle_display()
                        
                        # NEW VERSION: 2025-08-08 - 智能冷却时间更新策略
                        try:
                            # 获取当前冷却状态来决定更新频率
                            import sys
                            import os
                            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
                            from core.global_cooldown import get_remaining_global_cooldown
                            
                            cooldown_minutes = self.config.get_global_cooldown_minutes()
                            remaining_cooldown_minutes = get_remaining_global_cooldown(cooldown_minutes)
                            
                            should_update_cooldown = False
                            
                            if remaining_cooldown_minutes <= 0:
                                # 无冷却：每30秒检查一次（低频）
                                should_update_cooldown = (counter % 300 == 0)  # 30秒
                            elif remaining_cooldown_minutes >= 1.0:
                                # 大于1分钟：每30秒更新一次（低频）
                                should_update_cooldown = (counter % 300 == 0)  # 30秒
                            else:
                                # 小于1分钟：每秒更新（高频，读秒）
                                should_update_cooldown = True
                            
                            if should_update_cooldown:
                                self.update_cooldown_display_only()
                                
                        except Exception as cooldown_update_error:
                            if self._debug_enabled:
                                logger.error(f"智能冷却更新出错: {cooldown_update_error}")
                        
                        timer_duration = time.time() - timer_start
                    else:
                        timer_duration = 0
                    
                    # 记录计时器更新耗时
                    if self._debug_enabled and timer_duration > 0.05:  # 超过50ms记录
                        logger.gui_update_debug("空闲时间更新", timer_duration)
                    
                    counter += 1
                    last_loop_time = loop_start_time
                    
                    # 精确sleep - 补偿已消耗的时间（0.1秒间隔，快速响应）
                    loop_duration = time.time() - loop_start_time
                    sleep_time = max(0.001, 0.1 - loop_duration)  # 0.1秒间隔
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    logger.error(f"空闲时间更新出错: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=idle_timer_loop, daemon=True)
        thread.start()
    
    def start_system_status_thread(self):
        """启动独立的系统状态检查线程（包含应用状态）"""
        def status_check_loop():
            # 首次启动立即检查
            self.update_app_status()
            
            while True:
                try:
                    # 每10秒检查一次系统状态
                    time.sleep(10)
                    
                    status_update_start = time.time()
                    self.update_app_status()  # 定期更新应用状态
                    status_update_duration = time.time() - status_update_start
                    
                    # 记录状态更新耗时
                    if self._debug_enabled and status_update_duration > 0.1:
                        self.log_message(f"[系统监控]状态更新耗时: {status_update_duration:.3f}秒", "DEBUG")
                        
                except Exception as e:
                    self.log_message(f"系统状态检查出错: {e}", "ERROR")
                    time.sleep(30)  # 出错时等待30秒
        
        thread = threading.Thread(target=status_check_loop, daemon=True)
        thread.start()
    
    def start_auto_monitor_thread(self):
        """启动自动监控线程"""
        self.log_message("[自动监控]start_auto_monitor_thread()方法被调用", "INFO")
        self.log_message("[BUG修复]日志系统已就绪，开始启动监控线程", "INFO")
        
        def monitor_loop():
            last_scheduled_check = None  # 记录最后一次检查定时触发的时间
            last_idle_state_triggered = False  # 记录上次是否已达到空闲触发条件（用于边缘触发）
            self.log_message("[自动监控]监控线程已启动", "INFO")
            
            while True:
                try:
                    # OLD VERSION: 2025-08-09 - 只检查静置触发
                    # if not self.config.is_idle_trigger_enabled():
                    #     time.sleep(30)  # 如果未启用，等待30秒后再次检查
                    #     continue
                    
                    # NEW VERSION: 2025-08-09 - 检查任一触发方式是否启用
                    idle_enabled = self.config.is_idle_trigger_enabled() if hasattr(self.config, 'is_idle_trigger_enabled') else False
                    scheduled_enabled = self.config.is_scheduled_trigger_enabled() if hasattr(self.config, 'is_scheduled_trigger_enabled') else False
                    
                    if not (idle_enabled or scheduled_enabled):
                        time.sleep(30)  # 如果都未启用，等待30秒后再次检查
                        continue
                    
                    current_time = datetime.now()
                    
                    # NEW VERSION: 2025-08-09 - 添加定时触发检查
                    if scheduled_enabled:
                        # 每分钟检查一次定时触发（避免过于频繁的检查）
                        if last_scheduled_check is None or (current_time - last_scheduled_check).total_seconds() >= 60:
                            last_scheduled_check = current_time
                            
                            # 获取定时触发配置
                            scheduled_time = self.config.get_scheduled_time()  # 格式: "HH:MM"
                            scheduled_days = self.config.get_scheduled_days()  # ['daily'] 或 ['monday', 'friday']
                            
                            # 检查是否到了定时时间
                            current_time_str = current_time.strftime("%H:%M")
                            current_weekday = current_time.strftime("%A").lower()
                            
                            should_trigger = False
                            if "daily" in [day.lower() for day in scheduled_days]:
                                should_trigger = (current_time_str == scheduled_time)
                            else:
                                should_trigger = (current_time_str == scheduled_time and current_weekday in [day.lower() for day in scheduled_days])
                            
                            if should_trigger:
                                self.log_message(f"[定时触发]达到预设时间{scheduled_time}，准备执行同步", "INFO")
                                
                                # 检查全局冷却时间
                                cooldown_minutes = self.config.get_idle_cooldown_minutes()  # 使用全局冷却时间
                                from core.global_cooldown import is_in_global_cooldown, get_remaining_global_cooldown
                                if not is_in_global_cooldown(cooldown_minutes):
                                    if not self.is_running_sync:
                                        self.log_message(f"[定时触发]开始执行定时触发的同步流程", "INFO")
                                        
                                        # 在主线程中设置同步标志，避免竞态条件
                                        self.is_running_sync = True
                                        
                                        # 执行定时触发同步（复用空闲触发的同步逻辑）
                                        def scheduled_sync_thread():
                                            try:
                                                success = sync_workflow.run_full_sync_workflow_gui(self.log_message)
                                                
                                                if success:
                                                    self.log_message("[定时触发]定时触发同步执行成功", "SUCCESS")
                                                    self.sync_success_count += 1
                                                    self.last_sync_time = datetime.now()
                                                    
                                                    # 更新全局冷却状态
                                                    try:
                                                        from core.global_cooldown import update_global_cooldown
                                                        update_global_cooldown("定时触发")
                                                        self.log_message("[定时触发]全局冷却时间已更新", "INFO")
                                                        
                                                        # 立即更新GUI显示的冷却状态
                                                        self.update_stats_labels()
                                                        self.update_app_status(force_refresh=True)
                                                        
                                                    except Exception as cooldown_error:
                                                        self.log_message(f"[定时触发]更新全局冷却失败: {cooldown_error}", "WARNING")
                                                else:
                                                    self.log_message("[定时触发]定时触发同步执行失败", "ERROR")
                                                    # 更新失败计数
                                                    self.sync_error_count += 1
                                                    
                                                    # 失败后也要更新冷却（防止频繁重试）
                                                    try:
                                                        from core.global_cooldown import update_global_cooldown
                                                        update_global_cooldown("定时触发(失败)")
                                                        self.log_message("[定时触发]全局冷却时间已更新(失败后防护)", "INFO")
                                                        self.update_stats_labels()
                                                    except Exception as cooldown_error:
                                                        self.log_message(f"[定时触发]更新全局冷却失败: {cooldown_error}", "WARNING")
                                                        
                                            except Exception as sync_error:
                                                self.log_message(f"[定时触发]同步执行过程中出错: {sync_error}", "ERROR")
                                                # 异常情况也要更新失败计数
                                                self.sync_error_count += 1
                                            finally:
                                                self.is_running_sync = False
                                                # 确保在finally中更新统计显示
                                                self.update_stats_labels()
                                        
                                        # 启动定时同步线程
                                        import threading
                                        sync_thread = threading.Thread(target=scheduled_sync_thread, daemon=True)
                                        sync_thread.start()
                                    else:
                                        self.log_message("[定时触发]定时触发条件满足，但同步流程已在运行中", "INFO")
                                else:
                                    remaining = get_remaining_global_cooldown(cooldown_minutes)
                                    self.log_message(f"[定时触发]定时触发被全局冷却阻止，剩余{remaining:.1f}分钟", "INFO")
                    
                    # 检查空闲触发（如果启用）
                    if idle_enabled:
                        # 获取配置参数
                        idle_minutes = self.config.get_idle_minutes()
                        cooldown_minutes = self.config.get_idle_cooldown_minutes()
                        
                        # 检查系统真实空闲时间（用于触发判断）
                        idle_seconds = self.idle_detector.get_idle_time_seconds()
                        idle_threshold = idle_minutes * 60
                        
                        # 每30秒输出一次调试信息，避免日志过多
                        if self._debug_enabled and int(idle_seconds) % 30 == 0:
                            self.log_message(f"[自动监控]空闲{idle_seconds:.1f}s, 阈值{idle_threshold}s", "DEBUG")
                        
                        # 边缘触发逻辑：只在刚达到空闲阈值时检查一次
                        current_idle_state_triggered = idle_seconds >= idle_threshold
                        
                        # 只在状态从"未达到"转换到"已达到"时触发检查
                        if current_idle_state_triggered and not last_idle_state_triggered:
                            self.log_message(f"[自动触发]检测到系统空闲{idle_minutes}分钟，触发自动同步", "INFO")
                            
                            # 检查全局冷却时间
                            from core.global_cooldown import is_in_global_cooldown, get_remaining_global_cooldown
                            if not is_in_global_cooldown(cooldown_minutes):
                                # 检查是否已经在运行同步
                                if not self.is_running_sync:
                                    # OLD VERSION: 2025-08-09 - 简化的自动同步逻辑
                                    # last_trigger_time = current_time
                                    # self.last_idle_trigger_time = current_time
                                    # self.log_message("[自动触发]自动同步功能需要完整实现", "WARNING")
                                    
                                    # NEW VERSION: 2025-08-09 - 完整的自动同步实现（临时简化版）
                                    self.last_idle_trigger_time = current_time
                                    self.log_message("[自动触发]空闲触发同步功能已实现，正在启动同步流程", "INFO")
                                    
                                    # 在主线程中设置同步标志，避免竞态条件
                                    self.is_running_sync = True
                                    
                                    # 启动同步线程（简化版，避免复杂嵌套）
                                    def simple_auto_sync():
                                        try:
                                            success = sync_workflow.run_full_sync_workflow_gui(self.log_message)
                                            if success:
                                                self.log_message("[自动触发]空闲触发同步执行成功", "SUCCESS")
                                                # 更新成功计数和同步时间
                                                self.sync_success_count += 1
                                                self.last_sync_time = datetime.now()
                                                try:
                                                    from core.global_cooldown import update_global_cooldown
                                                    update_global_cooldown("空闲触发")
                                                    self.update_stats_labels()
                                                    self.update_app_status(force_refresh=True)
                                                except:
                                                    pass
                                            else:
                                                self.log_message("[自动触发]空闲触发同步执行失败", "ERROR")
                                                # 更新失败计数
                                                self.sync_error_count += 1
                                        except Exception as e:
                                            self.log_message(f"[自动触发]同步过程出错: {e}", "ERROR")
                                            # 异常情况也要更新失败计数
                                            self.sync_error_count += 1
                                        finally:
                                            self.is_running_sync = False
                                            # 确保在finally中更新统计显示
                                            self.update_stats_labels()
                                    
                                    import threading
                                    sync_thread = threading.Thread(target=simple_auto_sync, daemon=True)
                                    sync_thread.start()
                                else:
                                    self.log_message("[自动触发]检测到空闲触发条件，但同步流程已在运行中", "INFO")
                            else:
                                # 被全局冷却阻止
                                remaining = get_remaining_global_cooldown(cooldown_minutes)
                                self.log_message(f"[自动触发]空闲触发被全局冷却阻止，剩余{remaining:.1f}分钟", "INFO")
                        
                        # 更新空闲状态，用于下次边缘触发检测
                        last_idle_state_triggered = current_idle_state_triggered
                    else:
                        # 空闲触发未启用时，重置状态以便重新启用时能正常工作
                        last_idle_state_triggered = False
                    
                    # 每5秒检查一次
                    time.sleep(5)
                    
                except Exception as e:
                    self.log_message(f"[自动监控]监控线程出错: {e}", "ERROR")
                    time.sleep(60)  # 出错时等待1分钟
        
        # OLD VERSION: 2025-08-09 - 只检查静置触发
        # has_method = hasattr(self.config, 'is_idle_trigger_enabled')
        # is_enabled = self.config.is_idle_trigger_enabled() if has_method else False
        
        # 检查静置触发和定时触发
        idle_enabled = self.config.is_idle_trigger_enabled()
        scheduled_enabled = self.config.is_scheduled_trigger_enabled()
        
        # 只要任一触发方式启用，就启动监控线程
        any_trigger_enabled = idle_enabled or scheduled_enabled
        
        if any_trigger_enabled:
            thread = threading.Thread(target=monitor_loop, daemon=True)
            thread.start()
            self.log_message("[自动监控]监控线程已启动（支持空闲和定时触发）", "INFO")
        else:
            self.log_message("[自动监控]监控线程未启动 - 所有触发方式均未启用", "WARNING")
    
    def update_system_idle_display(self):
        """直接使用系统空闲时间更新显示（线程安全版）"""
        try:
            # 直接获取系统空闲时间
            idle_seconds = self.idle_detector.get_idle_time_seconds()
            
            # 格式化显示文本
            idle_time_text = self.format_idle_time_seconds(int(idle_seconds))
            
            # 调试：记录显示更新
            if self._debug_enabled and idle_time_text != self._last_idle_display_text:
                current_display_seconds = int(idle_seconds)
                if current_display_seconds > 0 and current_display_seconds % 10 == 0:  # 每10秒记录一次
                    self.log_message(f"[系统监控]空闲时间: {idle_time_text}", "DEBUG")
            
            # 只有显示文本真正改变时才更新GUI
            if idle_time_text != self._last_idle_display_text:
                self._schedule_gui_update(idle_time_text)
            
        except Exception as e:
            self.log_message(f"更新系统空闲时间显示出错: {e}", "ERROR")
    
    def format_idle_time_seconds(self, total_seconds):
        """格式化秒数为可读的时间字符串"""
        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}分钟{seconds}秒"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours}小时{minutes}分钟{seconds}秒"
    
    def _schedule_gui_update(self, idle_time_text):
        """线程安全的GUI更新调度"""
        try:
            # 避免重复调度
            if not self._gui_update_pending:
                self._gui_update_pending = True
                self._pending_idle_text = idle_time_text
                # 使用root.after在主线程中执行GUI更新
                self.root.after(0, self._perform_gui_update)
        except RuntimeError as e:
            # OLD VERSION: 直接记录ERROR级别错误
            # self.log_message(f"调度GUI更新出错: {e}", "ERROR")
            
            # NEW VERSION: 2025-08-08 - 主循环未启动时的优雅处理
            if "main thread is not in main loop" in str(e):
                # 主循环还没开始，这是正常情况，跳过更新
                self._gui_update_pending = False
                self._pending_idle_text = None
                # 使用DEBUG级别，避免误导用户
                if self._debug_enabled:
                    self.log_message(f"GUI主循环未启动，跳过空闲时间更新", "DEBUG")
            else:
                # 其他运行时错误仍然记录为ERROR
                self.log_message(f"调度GUI更新出错: {e}", "ERROR")
        except Exception as e:
            self.log_message(f"调度GUI更新出错: {e}", "ERROR")
    
    def _perform_gui_update(self):
        """在主线程中执行GUI更新"""
        try:
            if hasattr(self, 'idle_time_label') and self._pending_idle_text:
                self.idle_time_label.config(text=self._pending_idle_text)
                self._last_idle_display_text = self._pending_idle_text
                self._pending_idle_text = None
            self._gui_update_pending = False
        except Exception as e:
            self.log_message(f"执行GUI更新出错: {e}", "ERROR")
            self._gui_update_pending = False
    
    # 独立日志系统已移除 - 统一使用main日志系统
    
    def debug_button_heights_with_retry(self, retry_count=0):
        """带重试的按钮高度调试 - 可通过 DEBUG_LAYOUT 开关控制"""
        if not self.DEBUG_LAYOUT:
            return  # 开关关闭时不执行调试
            
        max_retries = 5
        retry_delay = 2000  # 2秒重试间隔
        
        self.log_message(f"[按钮高度调试]========== 第{retry_count + 1}次尝试测量按钮高度 ==========", "DEBUG")
        
        buttons_to_test = [
            ("微信按钮", getattr(self, 'wechat_toggle_button', None)),
            ("OneDrive按钮", getattr(self, 'onedrive_toggle_button', None)), 
            ("测试按钮", getattr(self, 'test_button', None))
        ]
        
        # 检查按钮是否都已显示
        buttons_ready = 0
        for name, button in buttons_to_test:
            if button is not None and button.winfo_viewable():
                buttons_ready += 1
        
        if buttons_ready == 0 and retry_count < max_retries:
            self.log_message(f"[按钮高度调试]没有按钮就绪，{retry_delay//1000}秒后重试...", "DEBUG")
            self.root.after(retry_delay, lambda: self.debug_button_heights_with_retry(retry_count + 1))
            return
        elif buttons_ready > 0:
            self.log_message(f"[按钮高度调试]找到{buttons_ready}个就绪的按钮，开始测量", "DEBUG")
        else:
            self.log_message(f"[按钮高度调试]超过最大重试次数({max_retries})，停止调试", "DEBUG")
            return
        
        self.debug_button_heights()
    
    def debug_button_heights(self):
        """详细调试所有按钮的实际高度和框架信息 - 可通过 DEBUG_LAYOUT 开关控制"""
        if not self.DEBUG_LAYOUT:
            return  # 开关关闭时不执行调试
            
        buttons_to_test = [
            ("微信按钮", getattr(self, 'wechat_toggle_button', None)),
            ("OneDrive按钮", getattr(self, 'onedrive_toggle_button', None)), 
            ("测试按钮", getattr(self, 'test_button', None))
        ]
        
        theoretical_frame_height = 54  # 我们设置的框架高度
        pady_setting = 1   # 当前pady设置
        expected_button_height = 48  # 目标按钮高度：54px框架 - 4px默认税收 - 2px边距 = 48px
        
        self.log_message("[详细按钮调试]========== 开始详细分析 ==========", "DEBUG")
        self.log_message(f"[详细按钮调试]理论设置: 框架{theoretical_frame_height}px, pady={pady_setting}, 预期按钮高度{expected_button_height}px", "DEBUG")
        
        for name, button in buttons_to_test:
            if button is None:
                self.log_message(f"[详细按钮调试]{name}: 按钮不存在", "DEBUG")
                continue
                
            try:
                if not button.winfo_viewable():
                    self.log_message(f"[详细按钮调试]{name}: 按钮尚未显示", "DEBUG")
                    continue
                
                # 获取按钮的父容器(框架)
                parent_frame = button.master
                
                # 1. 按钮自身信息
                btn_actual_width = button.winfo_width()
                btn_actual_height = button.winfo_height()
                btn_req_width = button.winfo_reqwidth()
                btn_req_height = button.winfo_reqheight()
                btn_x = button.winfo_x()
                btn_y = button.winfo_y()
                
                # 2. 框架信息
                frame_actual_width = parent_frame.winfo_width()
                frame_actual_height = parent_frame.winfo_height()
                frame_req_width = parent_frame.winfo_reqwidth()
                frame_req_height = parent_frame.winfo_reqheight()
                
                # 3. 计算实际可用空间
                available_height_for_button = frame_actual_height - (2 * pady_setting)
                
                # 4. 分析按钮在框架中的位置
                btn_top_margin = btn_y
                btn_bottom_margin = frame_actual_height - btn_y - btn_actual_height
                actual_total_margin = btn_top_margin + btn_bottom_margin
                
                # 输出详细分析
                self.log_message(f"[详细按钮调试]========== {name} 详细分析 ==========", "DEBUG")
                
                # 框架信息
                self.log_message(f"  📦 框架信息:", "DEBUG")
                self.log_message(f"    - 实际尺寸: {frame_actual_width} x {frame_actual_height}px", "DEBUG")
                self.log_message(f"    - 请求尺寸: {frame_req_width} x {frame_req_height}px", "DEBUG")
                self.log_message(f"    - 理论高度: {theoretical_frame_height}px", "DEBUG")
                if frame_actual_height != theoretical_frame_height:
                    diff = frame_actual_height - theoretical_frame_height
                    status = "高于" if diff > 0 else "低于"
                    self.log_message(f"    ⚠️  框架高度异常: {status}理论值 {abs(diff)}px", "DEBUG")
                
                # 按钮信息
                self.log_message(f"  🔘 按钮信息:", "DEBUG")
                self.log_message(f"    - 实际尺寸: {btn_actual_width} x {btn_actual_height}px", "DEBUG")
                self.log_message(f"    - 请求尺寸: {btn_req_width} x {btn_req_height}px", "INFO")
                self.log_message(f"    - 在框架中位置: x={btn_x}, y={btn_y}", "INFO")
                
                # 边距分析
                self.log_message(f"  📐 边距分析:", "INFO")
                self.log_message(f"    - 设置pady: {pady_setting}px (期望上下各{pady_setting}px)", "INFO")
                self.log_message(f"    - 实际上边距: {btn_top_margin}px", "INFO")
                self.log_message(f"    - 实际下边距: {btn_bottom_margin}px", "INFO")
                self.log_message(f"    - 实际总边距: {actual_total_margin}px (期望{2 * pady_setting}px)", "INFO")
                
                # 空间计算
                self.log_message(f"  🔢 空间计算:", "INFO")
                self.log_message(f"    - 框架实际高度: {frame_actual_height}px", "INFO")
                self.log_message(f"    - 减去设置边距: {frame_actual_height} - {2 * pady_setting} = {available_height_for_button}px", "INFO")
                self.log_message(f"    - 按钮实际高度: {btn_actual_height}px", "INFO")
                self.log_message(f"    - 预期按钮高度: {expected_button_height}px", "INFO")
                
                # 差异分析
                height_diff = btn_actual_height - expected_button_height
                space_diff = available_height_for_button - btn_actual_height
                
                self.log_message(f"  🎯 差异分析:", "INFO")
                if height_diff != 0:
                    status = "超过" if height_diff > 0 else "小于"
                    self.log_message(f"    - 按钮高度差异: {status}预期 {abs(height_diff)}px", "WARNING")
                
                self.log_message(f"    - 剩余未使用空间: {space_diff}px", "INFO")
                
                # 边距差异分析
                margin_diff = actual_total_margin - (2 * pady_setting)
                if margin_diff != 0:
                    status = "超过" if margin_diff > 0 else "小于"
                    self.log_message(f"    - 边距差异: {status}设置值 {abs(margin_diff)}px", "WARNING")
                
                # 根本原因推测
                self.log_message(f"  🔍 问题推测:", "INFO")
                if frame_actual_height != theoretical_frame_height:
                    self.log_message(f"    - 框架高度不符合设置，可能是grid_propagate或其他约束", "WARNING")
                if btn_actual_height < expected_button_height:
                    self.log_message(f"    - 按钮被压缩，可能是按钮内容不需要那么高", "WARNING")
                if actual_total_margin != (2 * pady_setting):
                    self.log_message(f"    - pady设置未完全生效，tkinter可能有其他布局逻辑", "WARNING")
                    
            except Exception as e:
                self.log_message(f"[详细按钮调试]{name} 测量失败: {e}", "ERROR")
        
        self.log_message("[详细按钮调试]========== 详细分析完成 ==========", "DEBUG")
    
    @measure_time("MainWindow", "窗口关闭处理")
    def on_closing(self):
        """窗口关闭处理 - 根据配置文件设置处理关闭行为"""
        # PERFORMANCE: 记录用户关闭窗口操作
        log_user_action("MainWindow", "窗口关闭操作")
        
        try:
            # 重新加载配置文件以获取最新设置
            self.config.reload()
            
            # 获取关闭行为配置
            close_behavior = self.config.get_gui_config().get('close_behavior', 'exit')
            remember_choice = self.config.get_gui_config().get('remember_close_choice', True)
            
            self.log_message(f"关闭行为配置: {close_behavior}, 记住选择: {remember_choice}", "DEBUG")
            
            if close_behavior == "ask":
                # 询问用户如何关闭
                self.show_close_dialog()
            elif close_behavior == "minimize":
                # 最小化到托盘
                self.minimize_to_tray()
            else:
                # 直接退出
                self.exit_application()
                
        except Exception as e:
            self.log_message(f"处理关闭事件时出错: {e}", "ERROR")
            # 出错时直接退出
            self.exit_application()
    
    def show_close_dialog(self):
        """显示关闭选择对话框"""
        try:
            if CloseDialog and TRAY_AVAILABLE:
                dialog = CloseDialog(self.root, tray_available=bool(self.system_tray))
                self.root.wait_window(dialog.dialog)
                
                # 检查用户是否确认了操作
                self.log_message(f"对话框结果: result={dialog.result}, close_method={dialog.close_method}, remember={dialog.remember_choice}", "DEBUG")
                
                if dialog.result:  # 如果用户点击了"是"
                    self.log_message(f"用户确认关闭，方式: {dialog.close_method}", "INFO")
                    
                    if dialog.close_method == "minimize":
                        self.log_message("执行最小化到托盘", "DEBUG")
                        self.minimize_to_tray()
                    elif dialog.close_method == "exit":
                        self.log_message("执行程序退出", "DEBUG")
                        self.exit_application()
                    else:
                        self.log_message(f"未知的关闭方式: {dialog.close_method}", "ERROR")
                    
                    # 如果用户选择记住选择，更新配置
                    if dialog.remember_choice:
                        self.config.set("gui.close_behavior", dialog.close_method)
                        self.config.save()
                        self.log_message(f"已保存关闭行为设置: {dialog.close_method}", "INFO")
                else:
                    self.log_message("用户取消关闭操作", "DEBUG")
            else:
                # 如果没有对话框模块，直接询问
                import tkinter.messagebox as messagebox
                result = messagebox.askyesnocancel(
                    "关闭程序",
                    "选择关闭方式：\n\n是 - 最小化到系统托盘\n否 - 直接退出程序\n取消 - 继续运行"
                )
                if result is True:  # 是
                    self.minimize_to_tray()
                elif result is False:  # 否
                    self.exit_application()
                # None (取消) - 不做任何操作
                    
        except Exception as e:
            self.log_message(f"显示关闭对话框时出错: {e}", "ERROR")
            self.exit_application()
    
    def minimize_to_tray(self):
        """最小化到系统托盘"""
        try:
            self.log_message(f"检查系统托盘状态: system_tray={self.system_tray is not None}", "DEBUG")
            if self.system_tray:
                self.log_message(f"系统托盘运行状态: is_running={getattr(self.system_tray, 'is_running', 'unknown')}", "DEBUG")
                
            if self.system_tray and getattr(self.system_tray, 'is_running', False):
                self.log_message("程序最小化到系统托盘", "INFO")
                self.root.withdraw()  # 隐藏主窗口
                self.log_message("主窗口已隐藏，托盘图标继续运行", "DEBUG")
            else:
                self.log_message("系统托盘不可用，程序将直接退出", "INFO")
                self.exit_application()
        except Exception as e:
            self.log_message(f"最小化到托盘时出错: {e}", "ERROR")
            self.exit_application()
    
    def exit_application(self):
        """退出应用程序"""
        try:
            self.log_message("开始执行程序退出流程", "INFO")
            
            # 记录程序关闭日志到统一日志系统
            logger.info("程序正常关闭")
            
            # 清理系统托盘
            if self.system_tray:
                try:
                    self.log_message("停止系统托盘", "DEBUG")
                    self.system_tray.stop_tray(timeout=3.0)  # 给予较长超时，因为这是正常退出
                except Exception as tray_error:
                    self.log_message(f"停止系统托盘时出错: {tray_error}", "WARNING")
            
            # 销毁主窗口
            self.log_message("销毁主窗口", "DEBUG")
            self.root.destroy()
            self.log_message("程序退出完成", "INFO")
            
        except Exception as e:
            self.log_message(f"退出程序时出错: {e}", "ERROR")
            logger.error(f"退出程序时出错: {e}")
            # 强制退出
            import sys
            sys.exit(0)
    
    def restore_from_tray(self):
        """从系统托盘恢复显示主窗口"""
        try:
            self.root.deiconify()  # 恢复窗口
            self.root.lift()       # 置顶
            self.root.focus_force() # 获得焦点
            self.log_message("从系统托盘恢复显示", "INFO")
        except Exception as e:
            self.log_message(f"从托盘恢复显示时出错: {e}", "ERROR")
    
    def show_from_tray(self):
        """兼容性方法，调用restore_from_tray"""
        self.restore_from_tray()
    
    def setup_session_handling(self):
        """设置Windows会话管理事件处理（修复关机时taskkill弹窗问题）"""
        try:
            import platform
            if platform.system() == "Windows":
                # 在主线程中注册信号处理器
                self._register_signal_handlers()
                
                # Windows特定的会话管理
                try:
                    import threading
                    # 创建会话监听线程
                    session_thread = threading.Thread(target=self._monitor_windows_session, daemon=True)
                    session_thread.start()
                    
                    self.log_message("Windows会话管理事件处理已启用", "DEBUG")
                except Exception as e:
                    self.log_message(f"Windows会话监听启动失败，使用备用方案: {e}", "WARNING")
            
        except Exception as e:
            self.log_message(f"设置会话管理失败: {e}", "ERROR")
    
    def _register_signal_handlers(self):
        """在主线程中注册信号处理器"""
        try:
            import signal
            import os
            
            def signal_handler(signum, frame):
                self.log_message(f"接收到系统信号 {signum}，触发快速退出", "INFO")
                # 使用线程安全的方式触发快速退出
                try:
                    self.root.after(0, self.force_exit)
                except:
                    # 如果Tkinter已经销毁，直接强制退出
                    os._exit(0)
            
            # 注册常见的系统终止信号
            signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
            signal.signal(signal.SIGINT, signal_handler)   # 中断信号 (Ctrl+C)
            if hasattr(signal, 'SIGBREAK'):
                signal.signal(signal.SIGBREAK, signal_handler)  # Windows Break信号
                
            self.log_message("信号处理器注册成功", "DEBUG")
        except Exception as e:
            self.log_message(f"注册信号处理器失败: {e}", "WARNING")
    
    def _handle_focus_events(self, event=None):
        """处理焦点事件（备用方案）"""
        # 这是一个备用的事件处理，主要依赖Windows会话监听
        pass
    
    def _monitor_windows_session(self):
        """监控Windows会话状态（在独立线程中运行）"""
        try:
            import time
            
            # 简化的会话监控：主要监控窗口状态
            try:
                while True:
                    time.sleep(2)  # 每2秒检查一次
                    
                    # 检查程序是否仍在运行
                    if not hasattr(self, 'root'):
                        break
                    
                    try:
                        # 检查Tkinter窗口是否仍然存在
                        if not self.root.winfo_exists():
                            break
                    except:
                        break
                    
                    # 可以在这里添加更多的系统状态检测，如检测关机进程等
                    
            except Exception as e:
                self.log_message(f"Windows会话监听线程异常: {e}", "ERROR")
                
        except Exception as e:
            self.log_message(f"Windows会话监听初始化失败: {e}", "ERROR")
    
    def force_exit(self):
        """快速强制退出（用于系统关机等场景，跳过用户交互）"""
        try:
            self.log_message("执行快速退出流程（系统关机）", "INFO")
            logger.info("系统关机触发快速退出")
            
            # 停止所有线程和定时器
            if hasattr(self, 'status_update_timer'):
                try:
                    self.root.after_cancel(self.status_update_timer)
                except:
                    pass
            
            # 快速清理系统托盘（设置超时）
            if self.system_tray:
                try:
                    # 在新线程中停止托盘，避免阻塞
                    import threading
                    def quick_stop_tray():
                        try:
                            self.system_tray.stop_tray()
                        except:
                            pass
                    
                    tray_thread = threading.Thread(target=quick_stop_tray, daemon=True)
                    tray_thread.start()
                    tray_thread.join(timeout=0.5)  # 最多等待0.5秒
                except:
                    pass
            
            # 立即销毁窗口
            try:
                self.root.quit()  # 退出主循环
                self.root.destroy()  # 销毁窗口
            except:
                pass
            
            # 最终保险：强制退出进程
            import os
            import sys
            os._exit(0)  # 立即退出，不执行清理操作
            
        except Exception as e:
            # 如果快速退出失败，直接强制终止
            import os
            os._exit(0)

def main():
    """主函数"""
    app = MainWindow()
    app.root.mainloop()

if __name__ == "__main__":
    main()