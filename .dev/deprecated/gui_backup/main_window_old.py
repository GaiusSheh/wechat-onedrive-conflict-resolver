#!/usr/bin/env python3
"""
微信OneDrive冲突解决工具 - 现代化GUI主窗口 v2.0
优化版本：上下布局 + 智能切换按钮
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

from wechat_controller import is_wechat_running, find_wechat_processes, start_wechat, stop_wechat
from onedrive_controller import is_onedrive_running, get_onedrive_status, start_onedrive, pause_onedrive_sync
from config_manager import ConfigManager
from idle_detector import IdleDetector
from core.performance_monitor import start_performance_monitoring, get_performance_summary
import sync_workflow

class MainWindow:
    """主GUI窗口类 - v2.0 优化版"""
    
    def __init__(self):
        # 使用ttkbootstrap创建现代化主题的窗口
        self.root = ttk.Window(themename="cosmo")  # 使用现代化的cosmo主题
        self.root.title("微信OneDrive冲突解决工具 v2.0")
        self.root.geometry("1000x1200")
        self.root.minsize(1000, 1200)  # 调整最小窗口尺寸，适应上下布局
        self.root.resizable(True, True)
        
        # 设置窗口图标和样式
        try:
            self.root.iconbitmap(default='gui/resources/icons/app.ico')
        except:
            pass  # 忽略图标文件不存在的错误
        
        # 初始化图标管理器
        self.icon_manager = IconManager()
        self.icons = self.icon_manager.get_all_icons()
        
        # 初始化组件
        self.config = ConfigManager()
        self.idle_detector = IdleDetector()
        
        # 状态变量
        self.is_running_sync = False
        self.last_sync_time = None
        self.sync_success_count = 0
        self.sync_error_count = 0
        
        # 静置触发冷却相关变量
        self.last_idle_trigger_time = None
        self.cooldown_remaining = 0
        
        # 应用状态缓存
        self._wechat_status = None  # None=检查中, True=运行, False=未运行
        self._onedrive_status = None  # None=检查中, True=运行, False=未运行
        self._status_check_in_progress = False
        
        # 智能空闲时间计时器（重新设计）
        self._local_idle_start_time = None
        self._last_system_idle_time = 0
        self._local_idle_seconds = 0
        self._last_system_check_time = 0
        self._idle_timer_stable = False  # 计时器是否已稳定
        
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
        
        # 调试时间戳（用于分析卡顿原因）
        self._debug_enabled = True  # 可以通过菜单控制
        self._last_update_time = 0
        self._update_intervals = []  # 记录最近的更新间隔
        
        # GUI更新队列（线程安全）
        self._gui_update_pending = False
        self._pending_idle_text = None
        
        # 系统托盘
        self.system_tray = None
        if TRAY_AVAILABLE and SystemTray:
            self.system_tray = SystemTray(self)
        
        # 创建界面
        self.create_widgets()
        self.create_menu()
        
        # 强制更新窗口布局
        self.root.update_idletasks()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动状态更新线程
        self.start_status_update_thread()
        
        # 启动独立的状态检查线程（避免阻塞空闲时间显示）
        self.start_system_status_thread()
        
        # 启动自动监控线程（如果启用）
        self.start_auto_monitor_thread()
        
        # 启动性能监控
        start_performance_monitoring(self.log_message)
        
    def create_widgets(self):
        """创建现代化主界面组件 - v2.0上下布局"""
        # 创建主容器，使用现代化的间距
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重，支持响应式布局
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)  # 状态面板
        main_frame.rowconfigure(2, weight=0)  # 控制面板
        main_frame.rowconfigure(3, weight=1)  # 日志区域可扩展
        
        # 创建响应式网格布局（上下排列）
        self.create_header_section(main_frame)     # 顶部标题
        self.create_status_section(main_frame)     # 状态监控区域（上）
        self.create_control_section(main_frame)    # 控制面板（中）
        self.create_log_section(main_frame)        # 日志区域（下）
        
    def create_header_section(self, parent):
        """创建现代化头部区域"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.columnconfigure(1, weight=1)
        
        # 应用标题
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
            text="v2.0 | 智能切换版",
            font=("Microsoft YaHei UI", 10),
            bootstyle="secondary"
        )
        version_label.grid(row=0, column=1, sticky=tk.E)
        
        # 分隔线
        separator = ttk.Separator(header_frame, orient="horizontal")
        separator.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    
    def create_status_section(self, parent):
        """创建现代化状态监控区域（包含智能切换按钮）"""
        status_card = ttk.LabelFrame(
            parent,
            text="  📊 系统状态监控",
            padding="20",
            bootstyle="success"
        )
        status_card.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        status_card.columnconfigure(0, weight=1)
        
        # 应用状态区域（微信和OneDrive + 切换按钮）
        app_status_frame = ttk.Frame(status_card)
        # OLD VERSION: 2025-08-07 - pady=(0, 15) 导致间距过大
        # app_status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        # NEW VERSION: 2025-08-07 - 统一间距为10px
        app_status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        app_status_frame.columnconfigure(1, weight=1)
        
        # 微信状态行
        wechat_frame = ttk.Frame(app_status_frame)
        wechat_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=5)
        wechat_frame.columnconfigure(1, weight=1)
        
        wechat_icon_label = ttk.Label(
            wechat_frame, 
            text="  微信状态:",
            image=self.icons.get('wechat'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=12
        )
        wechat_icon_label.grid(row=0, column=0, sticky=tk.W)
        
        self.wechat_status_label = ttk.Label(
            wechat_frame, 
            text="检查中...", 
            bootstyle="warning",
            font=("Microsoft YaHei UI", 10)
        )
        self.wechat_status_label.grid(row=0, column=1, sticky=tk.W, padx=(15, 15))
        
        # 微信智能切换按钮
        self.wechat_toggle_button = ttk.Button(
            wechat_frame,
            text="查询中...",
            state="disabled",
            command=self.toggle_wechat,
            bootstyle="outline-secondary",
            width=10
        )
        self.wechat_toggle_button.grid(row=0, column=2, sticky=tk.E)
        
        # OneDrive状态行
        onedrive_frame = ttk.Frame(app_status_frame)
        onedrive_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        onedrive_frame.columnconfigure(1, weight=1)
        
        onedrive_icon_label = ttk.Label(
            onedrive_frame, 
            text="  OneDrive:",
            image=self.icons.get('onedrive'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=12
        )
        onedrive_icon_label.grid(row=0, column=0, sticky=tk.W)
        
        self.onedrive_status_label = ttk.Label(
            onedrive_frame, 
            text="检查中...", 
            bootstyle="warning",
            font=("Microsoft YaHei UI", 10)
        )
        self.onedrive_status_label.grid(row=0, column=1, sticky=tk.W, padx=(15, 15))
        
        # OneDrive智能切换按钮
        self.onedrive_toggle_button = ttk.Button(
            onedrive_frame,
            text="查询中...",
            state="disabled",
            command=self.toggle_onedrive,
            bootstyle="outline-secondary",
            width=10
        )
        self.onedrive_toggle_button.grid(row=0, column=2, sticky=tk.E)
        
        # 系统空闲时间
        idle_frame = ttk.Frame(status_card)
        # OLD VERSION: 2025-08-07 - pady=(15, 0) 导致间距过大
        # idle_frame.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        # NEW VERSION: 2025-08-07 - 统一间距为10px
        idle_frame.grid(row=1, column=0, sticky="ew", pady=(5, 5))
        idle_frame.columnconfigure(1, weight=1)
        
        idle_icon_label = ttk.Label(
            idle_frame, 
            text="  空闲时间:",
            image=self.icons.get('idle'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=12
        )
        idle_icon_label.grid(row=0, column=0, sticky=tk.W)
        
        self.idle_time_label = ttk.Label(
            idle_frame, 
            text="计算中...",
            bootstyle="info",
            font=("Microsoft YaHei UI", 10, "bold")
        )
        self.idle_time_label.grid(row=0, column=1, sticky=tk.W, padx=(15, 0))
        
        # 分隔线
        # OLD VERSION: 2025-08-07 - pady=(15, 15) 导致间距过大
        # ttk.Separator(status_card, orient="horizontal").grid(
        #     row=2, column=0, sticky="ew", pady=(15, 15)
        # )
        # NEW VERSION: 2025-08-07 - 统一间距为10px
        ttk.Separator(status_card, orient="horizontal").grid(
            row=2, column=0, sticky="ew", pady=(5, 5)
        )
        
        # 统计信息区域
        stats_frame = ttk.Frame(status_card)
        stats_frame.grid(row=3, column=0, sticky="ew")
        stats_frame.columnconfigure(1, weight=1)
        # 彻底解决间距不一致问题 - 设置更大的统一行高并添加行间分隔
        # 设置足够大的行高确保视觉一致性，不依赖pady
        for i in range(3):  # 3行：测试标签1、测试标签2、测试标签3
            stats_frame.rowconfigure(i, minsize=40, weight=0, pad=2)
        
        # 上次同步时间
        sync_icon_label = ttk.Label(
            stats_frame, 
            # OLD VERSION: 原始图标和文字
            # text="  上次同步:",
            # image=self.icons.get('sync'),
            # compound="left",
            # NEW VERSION: 测试用统一文字和图标
            text="  测试标签1:",
            # image=None,  # 暂时移除图标
            font=("Microsoft YaHei UI", 9),
            width=13
        )
        # 添加明确的pady确保间距一致
        sync_icon_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.last_sync_label = ttk.Label(
            stats_frame, 
            # OLD VERSION: text="未执行",
            # NEW VERSION: 测试用统一文字
            text="测试值1",
            font=("Microsoft YaHei UI", 9),
            bootstyle="secondary"
        )
        # 添加明确的pady确保间距一致
        self.last_sync_label.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 5))
        
        # 成功/失败统计
        stats_icon_label = ttk.Label(
            stats_frame, 
            # OLD VERSION: 原始图标和文字
            # text="  成功/失败:",
            # image=self.icons.get('stats'),
            # compound="left",
            # NEW VERSION: 测试用统一文字和图标
            text="  测试标签2:",
            # image=None,  # 暂时移除图标
            font=("Microsoft YaHei UI", 9),
            width=13
        )
        # 添加明确的pady确保间距一致
        stats_icon_label.grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.stats_label = ttk.Label(
            stats_frame, 
            # OLD VERSION: text="0 / 0",
            # NEW VERSION: 测试用统一文字
            text="测试值2",
            font=("Microsoft YaHei UI", 9),
            bootstyle="secondary"
        )
        # 添加明确的pady确保间距一致
        self.stats_label.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(0, 5))
        
        # 冷却状态
        cooldown_icon_label = ttk.Label(
            stats_frame, 
            # OLD VERSION: 原始图标和文字
            # text="  触发冷却:",
            # image=self.icons.get('cooldown'),
            # compound="left",
            # NEW VERSION: 测试用统一文字和图标
            text="  测试标签3:",
            # image=None,  # 暂时移除图标
            font=("Microsoft YaHei UI", 9),
            width=13
        )
        # 不添加pady，让最后一行自然结束
        cooldown_icon_label.grid(row=2, column=0, sticky="w")
        self.cooldown_label = ttk.Label(
            stats_frame, 
            # OLD VERSION: text="无冷却",
            # NEW VERSION: 测试用统一文字
            text="测试值3",
            font=("Microsoft YaHei UI", 9),
            bootstyle="secondary"
        )
        # 不添加pady，让最后一行自然结束
        self.cooldown_label.grid(row=2, column=1, sticky="w", padx=(10, 0))
        
        # 重置冷却按钮
        self.reset_cooldown_button = ttk.Button(
            stats_frame,
            # OLD VERSION: text="重置",
            # NEW VERSION: 测试用统一按钮文字
            text="测试按钮",
            command=self.reset_global_cooldown,
            bootstyle="outline-warning",
            width=8,
            state="disabled"
        )
        # 移除pady依赖，依靠行配置控制间距
        self.reset_cooldown_button.grid(row=2, column=2, sticky="w", padx=(10, 0))
    
    def create_control_section(self, parent):
        """创建简化的控制面板（只包含立即同步和配置）"""
        control_card = ttk.LabelFrame(
            parent,
            text="  🎮 控制面板",
            padding="20",
            bootstyle="primary"
        )
        control_card.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        control_card.columnconfigure(0, weight=1)
        control_card.columnconfigure(1, weight=1)
        
        # 左侧：立即同步按钮
        self.sync_button = ttk.Button(
            control_card, 
            text="🚀 立即执行同步流程", 
            command=self.run_sync_workflow,
            bootstyle="success",
            width=30
        )
        self.sync_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # 右侧：配置按钮
        config_button = ttk.Button(
            control_card, 
            text="⚙️ 打开配置面板", 
            command=self.show_config_dialog,
            bootstyle="info",
            width=30
        )
        config_button.grid(row=0, column=1, sticky="ew", padx=(10, 0))
    
    def create_log_section(self, parent):
        """创建现代化日志区域"""
        log_card = ttk.LabelFrame(
            parent, 
            text="  📋 操作日志",
            padding="15",
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
        
        # 现代化日志文本框
        self.log_text = tk.Text(
            log_container, 
            height=12, 
            wrap=tk.WORD, 
            font=("Consolas", 10),
            bg="#f8f9fa",
            relief="flat",
            borderwidth=0
        )
        
        # 现代化滚动条
        scrollbar = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 配置日志颜色标签
        self.log_text.tag_configure("INFO", foreground="#495057")
        self.log_text.tag_configure("SUCCESS", foreground="#28a745", font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("WARNING", foreground="#fd7e14")
        self.log_text.tag_configure("ERROR", foreground="#dc3545", font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("TITLE", foreground="#007bff", font=("Consolas", 10, "bold"))
        
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 日志控制按钮区域
        log_buttons_frame = ttk.Frame(log_card)
        log_buttons_frame.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        
        # 现代化按钮
        ttk.Button(
            log_buttons_frame, 
            text="清空日志", 
            command=self.clear_log,
            bootstyle="outline-secondary",
            width=12
        ).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(
            log_buttons_frame, 
            text="导出日志", 
            command=self.export_log,
            bootstyle="outline-info",
            width=12
        ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 添加初始日志
        self.log_message("🚀 现代化GUI界面v2.0已启动")
    
    # 智能切换按钮功能
    def toggle_wechat(self):
        """切换微信状态"""
        if self._wechat_status is None:
            self.log_message("微信状态检查中，请稍候...", "WARNING")
            return
        
        def toggle_thread():
            try:
                if self._wechat_status:  # 当前运行中，需要停止
                    self.log_message("正在停止微信...")
                    self.wechat_toggle_button.config(text="停止中...", state="disabled")
                    success = stop_wechat()
                    if success:
                        self.log_message("微信已停止", "SUCCESS")
                    else:
                        self.log_message("停止微信失败", "ERROR")
                else:  # 当前未运行，需要启动
                    self.log_message("正在启动微信...")
                    self.wechat_toggle_button.config(text="启动中...", state="disabled")
                    success = start_wechat()
                    if success:
                        self.log_message("微信启动成功", "SUCCESS")
                    else:
                        self.log_message("微信启动失败", "ERROR")
                
                # 立即检查状态更新
                self.update_app_status()
                        
            except Exception as e:
                self.log_message(f"切换微信状态时出错: {e}", "ERROR")
        
        # 在新线程中运行避免阻塞GUI
        thread = threading.Thread(target=toggle_thread, daemon=True)
        thread.start()
    
    def toggle_onedrive(self):
        """切换OneDrive状态"""
        if self._onedrive_status is None:
            self.log_message("OneDrive状态检查中，请稍候...", "WARNING")
            return
        
        def toggle_thread():
            try:
                if self._onedrive_status:  # 当前运行中，需要暂停
                    self.log_message("正在暂停OneDrive...")
                    self.onedrive_toggle_button.config(text="暂停中...", state="disabled")
                    success = pause_onedrive_sync()
                    if success:
                        self.log_message("OneDrive已暂停", "SUCCESS")
                    else:
                        self.log_message("暂停OneDrive失败", "ERROR")
                else:  # 当前未运行，需要启动
                    self.log_message("正在启动OneDrive...")
                    self.onedrive_toggle_button.config(text="启动中...", state="disabled")
                    success = start_onedrive()
                    if success:
                        self.log_message("OneDrive启动成功", "SUCCESS")
                    else:
                        self.log_message("OneDrive启动失败", "ERROR")
                
                # 立即检查状态更新
                self.update_app_status()
                        
            except Exception as e:
                self.log_message(f"切换OneDrive状态时出错: {e}", "ERROR")
        
        # 在新线程中运行避免阻塞GUI
        thread = threading.Thread(target=toggle_thread, daemon=True)
        thread.start()
    
    def update_app_status(self):
        """更新应用状态（立即检查）"""
        def check_status():
            try:
                # 检查微信状态
                wechat_running = is_wechat_running()
                self._wechat_status = wechat_running
                
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
                
                # 更新微信状态UI
                self.root.after(0, lambda: self.wechat_status_label.config(text=wechat_text, bootstyle=wechat_bootstyle))
                self.root.after(0, lambda: self.wechat_toggle_button.config(text=button_text, bootstyle=button_bootstyle, state="normal"))
                
                # 检查OneDrive状态
                onedrive_running = is_onedrive_running()
                self._onedrive_status = onedrive_running
                
                if onedrive_running:
                    onedrive_text = "运行中"
                    onedrive_bootstyle = "success"
                    button_text = "暂停同步"
                    button_bootstyle = "outline-warning"
                else:
                    onedrive_text = "未运行"
                    onedrive_bootstyle = "danger"
                    button_text = "启动OneDrive"
                    button_bootstyle = "outline-info"
                
                # 更新OneDrive状态UI
                self.root.after(0, lambda: self.onedrive_status_label.config(text=onedrive_text, bootstyle=onedrive_bootstyle))
                self.root.after(0, lambda: self.onedrive_toggle_button.config(text=button_text, bootstyle=button_bootstyle, state="normal"))
                
            except Exception as e:
                self.log_message(f"检查应用状态时出错: {e}", "ERROR")
        
        # 在新线程中检查状态
        thread = threading.Thread(target=check_status, daemon=True)
        thread.start()
    
    def show_config_dialog(self):
        """显示完整5标签页配置对话框（带性能监控）"""
        import time
        start_time = time.time()
        self.log_message("🔍 [性能分析] 配置对话框开始创建", "DEBUG")
        
        # 立即创建配置窗口框架
        config_window = ttk.Toplevel(self.root)
        config_window.title("配置设置")
        config_window.geometry("800x600")
        config_window.resizable(True, True)
        config_window.transient(self.root)
        config_window.grab_set()
        
        # 配置网格权重
        config_window.columnconfigure(0, weight=1)
        config_window.rowconfigure(0, weight=1)
        
        # 加载配置数据
        config_load_time = time.time()
        config_data = self.config.config.copy()
        self.log_message(f"🔍 [性能分析] 配置加载完成: {(config_load_time - start_time)*1000:.1f}ms", "DEBUG")
        
        # 创建主框架
        main_frame = ttk.Frame(config_window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        window_time = time.time()
        self.log_message(f"🔍 [性能分析] 配置窗口创建完成: {(window_time - start_time)*1000:.1f}ms", "DEBUG")
        
        # 创建标签页控件
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # 性能监控变量
        self._click_start_time = None
        
        def on_button_press(event):
            """鼠标按下时记录开始时间"""
            self._click_start_time = time.time()
        
        def on_tab_change(event):
            """标签页切换事件 - 测量从点击到完成的总响应时间"""
            try:
                selected_tab = notebook.index(notebook.select())
                tab_names = ["触发设置", "同步设置", "日志设置", "界面设置", "启动设置"]
                tab_name = tab_names[selected_tab] if selected_tab < len(tab_names) else f"标签页{selected_tab}"
                
                def measure_total_response():
                    response_end = time.time()
                    if self._click_start_time:
                        total_time = (response_end - self._click_start_time) * 1000
                        self.log_message(f"🔍 [性能分析] 点击到{tab_name}完成: {total_time:.1f}ms", "DEBUG")
                    else:
                        self.log_message(f"🔍 [性能分析] {tab_name}切换完成 (无点击时间)", "DEBUG")
                    self._click_start_time = None
                
                config_window.after_idle(measure_total_response)
            except Exception as e:
                self.log_message(f"🔍 [性能分析] 标签页切换错误: {e}", "DEBUG")
        
        # 绑定事件
        notebook.bind("<Button-1>", on_button_press)
        notebook.bind("<<NotebookTabChanged>>", on_tab_change)
        
        # === 触发设置标签页 ===
        trigger_frame = ttk.Frame(notebook, padding="20")
        notebook.add(trigger_frame, text="触发设置")
        trigger_frame.columnconfigure(0, weight=1)
        
        # 静置触发设置
        idle_labelframe = ttk.LabelFrame(trigger_frame, text="静置触发设置", padding="15")
        idle_labelframe.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        idle_labelframe.columnconfigure(2, weight=1)
        
        idle_enabled_var = tk.BooleanVar(value=config_data.get('idle_trigger', {}).get('enabled', True))
        ttk.Checkbutton(idle_labelframe, text="启用静置触发", variable=idle_enabled_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(idle_labelframe, text="静置时间(分钟):").grid(row=1, column=0, sticky=tk.W, pady=5)
        idle_minutes_var = tk.StringVar(value=str(config_data.get('idle_trigger', {}).get('idle_minutes', 5)))
        ttk.Spinbox(idle_labelframe, from_=1, to=120, width=10, textvariable=idle_minutes_var, bootstyle="info").grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(idle_labelframe, text="冷却时间(分钟):").grid(row=2, column=0, sticky=tk.W, pady=5)
        cooldown_minutes_var = tk.StringVar(value=str(config_data.get('idle_trigger', {}).get('cooldown_minutes', 20)))
        ttk.Spinbox(idle_labelframe, from_=1, to=120, width=10, textvariable=cooldown_minutes_var, bootstyle="info").grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 定时触发设置
        scheduled_labelframe = ttk.LabelFrame(trigger_frame, text="定时触发设置", padding="15")
        scheduled_labelframe.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        scheduled_labelframe.columnconfigure(2, weight=1)
        
        scheduled_enabled_var = tk.BooleanVar(value=config_data.get('scheduled_trigger', {}).get('enabled', True))
        ttk.Checkbutton(scheduled_labelframe, text="启用定时触发", variable=scheduled_enabled_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(scheduled_labelframe, text="触发时间:").grid(row=1, column=0, sticky=tk.W, pady=5)
        scheduled_time_var = tk.StringVar(value=config_data.get('scheduled_trigger', {}).get('time', '16:30'))
        ttk.Entry(scheduled_labelframe, width=15, textvariable=scheduled_time_var, bootstyle="info").grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(scheduled_labelframe, text="(格式: HH:MM)").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 执行日期
        ttk.Label(scheduled_labelframe, text="执行日期:").grid(row=2, column=0, sticky=tk.W, pady=5)
        days_var = tk.StringVar(value="daily" if config_data.get('scheduled_trigger', {}).get('days', ["daily"])[0] == "daily" else "weekdays")
        days_combobox = ttk.Combobox(scheduled_labelframe, width=12, textvariable=days_var, state="readonly", bootstyle="info")
        days_combobox['values'] = ("daily", "weekdays", "weekends")
        days_combobox.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # === 同步设置标签页 ===
        sync_frame = ttk.Frame(notebook, padding="20")
        notebook.add(sync_frame, text="同步设置")
        sync_frame.columnconfigure(0, weight=1)
        
        sync_labelframe = ttk.LabelFrame(sync_frame, text="同步行为设置", padding="15")
        sync_labelframe.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        sync_labelframe.columnconfigure(1, weight=1)
        
        ttk.Label(sync_labelframe, text="同步后等待时间(分钟):").grid(row=0, column=0, sticky=tk.W, pady=5)
        wait_minutes_var = tk.StringVar(value=str(config_data.get('sync_settings', {}).get('wait_after_sync_minutes', 2)))
        ttk.Spinbox(sync_labelframe, from_=1, to=30, width=10, textvariable=wait_minutes_var, bootstyle="info").grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(sync_labelframe, text="最大重试次数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        retry_var = tk.StringVar(value=str(config_data.get('sync_settings', {}).get('max_retry_attempts', 3)))
        ttk.Spinbox(sync_labelframe, from_=1, to=10, width=10, textvariable=retry_var, bootstyle="info").grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # === 日志设置标签页 ===
        log_frame = ttk.Frame(notebook, padding="20")
        notebook.add(log_frame, text="日志设置")
        log_frame.columnconfigure(0, weight=1)
        
        log_labelframe = ttk.LabelFrame(log_frame, text="日志记录设置", padding="15")
        log_labelframe.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        log_labelframe.columnconfigure(1, weight=1)
        
        logging_enabled_var = tk.BooleanVar(value=config_data.get('logging', {}).get('enabled', True))
        ttk.Checkbutton(log_labelframe, text="启用日志记录", variable=logging_enabled_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(log_labelframe, text="日志级别:").grid(row=1, column=0, sticky=tk.W, pady=5)
        log_level_var = tk.StringVar(value=config_data.get('logging', {}).get('level', 'info'))
        log_level_combo = ttk.Combobox(log_labelframe, width=12, textvariable=log_level_var, state="readonly", bootstyle="info")
        log_level_combo['values'] = ("debug", "info", "warning", "error")
        log_level_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(log_labelframe, text="最大日志文件数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        max_files_var = tk.StringVar(value=str(config_data.get('logging', {}).get('max_log_files', 5)))
        ttk.Spinbox(log_labelframe, from_=1, to=30, width=10, textvariable=max_files_var, bootstyle="info").grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # === 界面设置标签页 ===
        gui_frame = ttk.Frame(notebook, padding="20")
        notebook.add(gui_frame, text="界面设置")
        gui_frame.columnconfigure(0, weight=1)
        
        gui_labelframe = ttk.LabelFrame(gui_frame, text="界面行为设置", padding="15")
        gui_labelframe.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        gui_labelframe.columnconfigure(1, weight=1)
        
        ttk.Label(gui_labelframe, text="关闭行为:").grid(row=0, column=0, sticky=tk.W, pady=5)
        close_behavior_var = tk.StringVar(value=config_data.get('gui', {}).get('close_behavior', 'ask'))
        close_combo = ttk.Combobox(gui_labelframe, width=12, textvariable=close_behavior_var, state="readonly", bootstyle="info")
        close_combo['values'] = ("ask", "minimize", "exit")
        close_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        remember_choice_var = tk.BooleanVar(value=config_data.get('gui', {}).get('remember_close_choice', True))
        ttk.Checkbutton(gui_labelframe, text="记住关闭方式选择", variable=remember_choice_var, bootstyle="round-toggle").grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # === 启动设置标签页 ===
        startup_frame = ttk.Frame(notebook, padding="20")
        notebook.add(startup_frame, text="启动设置")
        startup_frame.columnconfigure(0, weight=1)
        
        startup_labelframe = ttk.LabelFrame(startup_frame, text="启动行为设置", padding="15")
        startup_labelframe.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        startup_labelframe.columnconfigure(1, weight=1)
        
        auto_start_var = tk.BooleanVar(value=config_data.get('startup', {}).get('auto_start_service', False))
        ttk.Checkbutton(startup_labelframe, text="开机自动启动监控服务", variable=auto_start_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        minimize_tray_var = tk.BooleanVar(value=config_data.get('startup', {}).get('minimize_to_tray', True))
        ttk.Checkbutton(startup_labelframe, text="启动时最小化到系统托盘", variable=minimize_tray_var, bootstyle="round-toggle").grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        notebook_time = time.time()
        self.log_message(f"🔍 [性能分析] 标签页框架创建完成: {(notebook_time - start_time)*1000:.1f}ms", "DEBUG")
        
        # === 按钮区域 ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        def save_config():
            try:
                # 保存所有配置
                config_data['idle_trigger']['enabled'] = idle_enabled_var.get()
                config_data['idle_trigger']['idle_minutes'] = int(idle_minutes_var.get())
                config_data['idle_trigger']['cooldown_minutes'] = int(cooldown_minutes_var.get())
                
                config_data['scheduled_trigger']['enabled'] = scheduled_enabled_var.get()
                config_data['scheduled_trigger']['time'] = scheduled_time_var.get()
                config_data['scheduled_trigger']['days'] = [days_var.get()]
                
                config_data['sync_settings']['wait_after_sync_minutes'] = int(wait_minutes_var.get())
                config_data['sync_settings']['max_retry_attempts'] = int(retry_var.get())
                
                config_data['logging']['enabled'] = logging_enabled_var.get()
                config_data['logging']['level'] = log_level_var.get()
                config_data['logging']['max_log_files'] = int(max_files_var.get())
                
                config_data['gui']['close_behavior'] = close_behavior_var.get()
                config_data['gui']['remember_close_choice'] = remember_choice_var.get()
                
                config_data['startup']['auto_start_service'] = auto_start_var.get()
                config_data['startup']['minimize_to_tray'] = minimize_tray_var.get()
                
                success = self.config.save_config(config_data)
                if success:
                    self.log_message("配置已保存成功", "SUCCESS")
                    messagebox.showinfo("成功", "配置已保存成功！")
                    config_window.destroy()
                else:
                    messagebox.showerror("错误", "保存配置失败！")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字！")
            except Exception as e:
                messagebox.showerror("错误", f"保存配置时出错: {e}")
        
        ttk.Button(button_frame, text="保存配置", command=save_config, bootstyle="success", width=15).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=config_window.destroy, bootstyle="outline-secondary", width=15).grid(row=0, column=1)
        
        # 居中显示配置窗口
        config_window.update_idletasks()
        x = (config_window.winfo_screenwidth() // 2) - (config_window.winfo_width() // 2)
        y = (config_window.winfo_screenheight() // 2) - (config_window.winfo_height() // 2)
        config_window.geometry(f"+{x}+{y}")
        
        # 最终性能统计
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        self.log_message(f"🔍 [性能分析] 配置对话框完全创建完成: 总耗时 {total_time:.1f}ms", "DEBUG")

    # 以下方法保持与原版本相同的功能...
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出配置", command=self.export_config)
        file_menu.add_command(label="导入配置", command=self.import_config)
        file_menu.add_separator()
        if TRAY_AVAILABLE:
            file_menu.add_command(label="最小化到托盘", command=self.minimize_to_tray)
            file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit_application)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="打开配置文件", command=self.open_config_file)
        tools_menu.add_command(label="打开日志目录", command=self.open_log_directory)
        tools_menu.add_separator()
        tools_menu.add_command(label="性能统计", command=self.show_performance_stats)
        tools_menu.add_command(label="空闲计时器调试", command=self.show_idle_timer_debug)
        tools_menu.add_command(label="切换调试模式", command=self.toggle_debug_mode)
        tools_menu.add_command(label="重置关闭方式", command=self.reset_close_behavior)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
    
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
                            print(f"[调试] 异常空闲时间更新间隔: {actual_interval:.3f}秒 (预期1.0秒)")
                    
                    # 每秒更新GUI显示（直接使用系统空闲时间，保持一致性）
                    if counter % 10 == 0:  # 0.1秒 * 10 = 1秒
                        timer_start = time.time()
                        self.update_system_idle_display()
                        timer_duration = time.time() - timer_start
                    else:
                        timer_duration = 0
                    
                    # 记录计时器更新耗时
                    if self._debug_enabled and timer_duration > 0.05:  # 超过50ms记录
                        print(f"[调试] 空闲时间更新耗时: {timer_duration:.3f}秒")
                    
                    counter += 1
                    last_loop_time = loop_start_time
                    
                    # 精确sleep - 补偿已消耗的时间（0.1秒间隔，快速响应）
                    loop_duration = time.time() - loop_start_time
                    sleep_time = max(0.001, 0.1 - loop_duration)  # 0.1秒间隔
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    print(f"空闲时间更新出错: {e}")
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
                    self.update_other_status()
                    self.update_app_status()  # 定期更新应用状态
                    status_update_duration = time.time() - status_update_start
                    
                    # 记录状态更新耗时
                    if self._debug_enabled and status_update_duration > 0.1:
                        print(f"[调试] 独立状态更新耗时: {status_update_duration:.3f}秒")
                        
                except Exception as e:
                    print(f"系统状态检查出错: {e}")
                    time.sleep(30)  # 出错时等待30秒
        
        thread = threading.Thread(target=status_check_loop, daemon=True)
        thread.start()
    
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
                    print(f"[调试] 系统空闲时间更新: {idle_time_text}")
            
            # 只有显示文本真正改变时才更新GUI
            if idle_time_text != self._last_idle_display_text:
                self._schedule_gui_update(idle_time_text)
            
        except Exception as e:
            print(f"更新系统空闲时间显示出错: {e}")
    
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
        except Exception as e:
            print(f"调度GUI更新出错: {e}")
    
    def _perform_gui_update(self):
        """在主线程中执行GUI更新"""
        try:
            if hasattr(self, 'idle_time_label') and self._pending_idle_text:
                gui_update_start = time.time()
                
                self.idle_time_label.config(text=self._pending_idle_text)
                self._last_idle_display_text = self._pending_idle_text
                
                gui_update_duration = time.time() - gui_update_start
                
                # 调试：记录GUI更新耗时
                if self._debug_enabled and gui_update_duration > 0.01:  # 超过10ms记录
                    print(f"[调试] GUI更新耗时: {gui_update_duration:.3f}秒")
            
            self._gui_update_pending = False
            self._pending_idle_text = None
            
        except Exception as e:
            print(f"执行GUI更新出错: {e}")
            self._gui_update_pending = False
            self._pending_idle_text = None
    
    def update_other_status(self):
        """更新其他状态信息（低频率，优化版）"""
        try:
            # 更新同步时间（仅在时间变化时更新GUI）
            if self.last_sync_time:
                new_time_str = self.last_sync_time.strftime("%Y-%m-%d %H:%M:%S")
                if new_time_str != self._last_sync_time_str:
                    self.last_sync_label.config(text=new_time_str)
                    self._last_sync_time_str = new_time_str
            
            # 更新统计（仅在数值变化时更新GUI）
            new_stats_text = f"{self.sync_success_count} / {self.sync_error_count}"
            if new_stats_text != self._last_stats_text:
                self.stats_label.config(text=new_stats_text)
                self._last_stats_text = new_stats_text
            
            # 更新冷却时间显示
            self.update_cooldown_display_optimized()
            
        except Exception as e:
            print(f"更新其他状态出错: {e}")
    
    def update_cooldown_display_optimized(self):
        """优化的冷却时间显示更新（全局冷却版本）"""
        try:
            if not hasattr(self, 'cooldown_label'):
                return
            
            # OLD VERSION: 2025-08-07 - 仅显示静置触发冷却时间
            # if not self.config.is_idle_trigger_enabled():
            #     new_text = "静置触发未启用"
            #     if new_text != self._last_cooldown_display_text:
            #         self.cooldown_label.config(text=new_text, bootstyle="secondary")
            #         self._last_cooldown_display_text = new_text
            #     return
            # 
            # if self.last_idle_trigger_time is None:
            #     new_text = "无冷却（未进行过静置触发）"
            #     if new_text != self._last_cooldown_display_text:
            #         self.cooldown_label.config(text=new_text, bootstyle="success")
            #         self._last_cooldown_display_text = new_text
            #     return
            # 
            # # 计算剩余冷却时间
            # current_time = datetime.now()
            # time_since_last_sync = (current_time - self.last_idle_trigger_time).total_seconds()
            # cooldown_seconds = self.config.get_idle_cooldown_minutes() * 60
            # remaining_seconds = max(0, cooldown_seconds - time_since_last_sync)
            # 
            # if remaining_seconds <= 0:
            #     new_text = "无冷却（可以触发静置同步）"
            #     new_bootstyle = "success"
            # else:
            #     # 格式化剩余冷却时间显示
            #     remaining_minutes = int(remaining_seconds // 60)
            #     remaining_sec = int(remaining_seconds % 60)
            #     
            #     if remaining_minutes > 0:
            #         new_text = f"冷却中：{remaining_minutes}分{remaining_sec}秒"
            #     else:
            #         new_text = f"冷却中：{remaining_sec}秒"
            #     
            #     new_bootstyle = "warning"
            # 
            # # 只有当文本真正改变时才更新GUI
            # if new_text != self._last_cooldown_display_text:
            #     self.cooldown_label.config(text=new_text, bootstyle=new_bootstyle)
            #     self._last_cooldown_display_text = new_text
            # 
            # # 更新冷却剩余时间（用于重置按钮状态）
            # self.cooldown_remaining = remaining_seconds / 60  # 转换为分钟
            
            # NEW VERSION: 2025-08-07 - 使用全局冷却管理器
            from core.global_cooldown import get_remaining_global_cooldown, is_in_global_cooldown
            cooldown_minutes = self.config.get_global_cooldown_minutes()
            
            if not is_in_global_cooldown(cooldown_minutes):
                new_text = "无冷却"
                new_bootstyle = "secondary"
                self.cooldown_remaining = 0
            else:
                # 获取剩余全局冷却时间
                remaining_time = get_remaining_global_cooldown(cooldown_minutes)
                
                # 优化显示逻辑：减少高频更新
                if remaining_time >= 1.5:
                    # 大于1.5分钟：只显示分钟数
                    remaining_minutes = int(remaining_time)
                    new_text = f"冷却中：{remaining_minutes}分钟"
                elif remaining_time >= 1.0:
                    # 1.0-1.5分钟：显示1分钟
                    new_text = f"冷却中：1分钟"
                else:
                    # 小于1分钟：显示秒数
                    remaining_sec = int(remaining_time * 60)
                    new_text = f"冷却中：{remaining_sec}秒"
                
                new_bootstyle = "secondary"
                self.cooldown_remaining = remaining_time
            
            # 只有当文本真正改变时才更新GUI
            if new_text != self._last_cooldown_display_text:
                self.cooldown_label.config(text=new_text, bootstyle=new_bootstyle)
                self._last_cooldown_display_text = new_text
            
            # 更新重置冷却按钮状态
            self.update_reset_cooldown_button_state()
                
        except Exception as e:
            print(f"更新冷却时间显示出错: {e}")
    
    def start_auto_monitor_thread(self):
        """启动自动监控线程"""
        def monitor_loop():
            last_trigger_time = None
            print("[调试] 自动监控线程已启动，每秒检查静置状态...")
            
            while True:
                try:
                    # 检查静置触发是否启用
                    if not self.config.is_idle_trigger_enabled():
                        print("[调试] 静置触发未启用，等待30秒...")
                        time.sleep(30)  # 如果未启用，等待30秒后再次检查
                        continue
                    
                    # 获取配置参数
                    idle_minutes = self.config.get_idle_minutes()
                    cooldown_minutes = self.config.get_idle_cooldown_minutes()
                    
                    # 检查系统真实空闲时间（用于触发判断）
                    idle_seconds = self.idle_detector.get_idle_time_seconds()
                    idle_threshold = idle_minutes * 60
                    
                    # 每10秒输出一次调试信息，避免日志过多
                    if self._debug_enabled and int(idle_seconds) % 10 == 0:
                        print(f"[调试] 监控检查: 空闲{idle_seconds:.1f}s, 阈值{idle_threshold}s")
                    
                    # 检查是否达到空闲时间阈值
                    if idle_seconds >= idle_threshold:
                        print(f"[调试] 达到触发条件！空闲时间{idle_seconds:.1f}s >= 阈值{idle_threshold}s")
                        # 检查冷却时间
                        current_time = datetime.now()
                        if last_trigger_time is None or (current_time - last_trigger_time).total_seconds() >= (cooldown_minutes * 60):
                            # 触发自动同步
                            self.log_message(f"检测到系统空闲{idle_minutes}分钟，触发自动同步", "INFO")
                            
                            # 检查是否已经在运行同步
                            if not self.is_running_sync:
                                # 在新线程中执行同步，避免阻塞监控线程
                                def auto_sync():
                                    try:
                                        self.is_running_sync = True
                                        self.root.after(0, lambda: self.sync_button.config(text="自动同步中...", state="disabled"))
                                        self.log_message("开始执行自动同步流程", "INFO")
                                        
                                        # 更新托盘图标状态
                                        if self.system_tray:
                                            self.system_tray.update_icon_status("running")
                                        
                                        # 执行同步流程
                                        success = sync_workflow.run_full_sync_workflow_gui(self.log_message)
                                        
                                        self.last_sync_time = datetime.now()
                                        if success:
                                            self.sync_success_count += 1
                                            self.log_message("自动同步流程执行成功", "SUCCESS")
                                            
                                            # 更新托盘图标和通知
                                            if self.system_tray:
                                                self.system_tray.update_icon_status("success")
                                                self.system_tray.show_notification("自动同步完成", "微信OneDrive冲突已自动解决")
                                        else:
                                            self.sync_error_count += 1
                                            self.log_message("自动同步流程执行失败", "ERROR")
                                            
                                            # 更新托盘图标和通知
                                            if self.system_tray:
                                                self.system_tray.update_icon_status("error")
                                                self.system_tray.show_notification("自动同步失败", "自动同步流程执行失败，请查看日志")
                                                
                                    except Exception as e:
                                        self.sync_error_count += 1
                                        self.log_message(f"自动同步流程异常: {e}", "ERROR")
                                        
                                        # 更新托盘图标状态
                                        if self.system_tray:
                                            self.system_tray.update_icon_status("error")
                                            self.system_tray.show_notification("自动同步异常", f"自动同步流程发生异常: {e}")
                                    finally:
                                        self.is_running_sync = False
                                        self.root.after(0, lambda: self.sync_button.config(text="🚀 立即执行同步流程", state="normal"))
                                        
                                        # 恢复托盘图标到正常状态
                                        if self.system_tray:
                                            self.system_tray.update_icon_status("normal")
                                
                                # 启动自动同步线程
                                sync_thread = threading.Thread(target=auto_sync, daemon=True)
                                sync_thread.start()
                                
                                # 更新最后触发时间和静置触发时间
                                last_trigger_time = current_time
                                self.last_idle_trigger_time = current_time
                            else:
                                self.log_message("检测到空闲触发条件，但同步流程已在运行中", "INFO")
                    
                    # 每1秒检查一次（接近实时响应，资源消耗极小~0.06ms/秒）
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"自动监控线程出错: {e}")
                    time.sleep(60)  # 出错时等待1分钟
        
        # 只有在静置触发启用时才启动监控线程
        if self.config.is_idle_trigger_enabled():
            thread = threading.Thread(target=monitor_loop, daemon=True)
            thread.start()
            self.log_message("自动监控线程已启动", "INFO")
        else:
            self.log_message("静置触发未启用，自动监控线程未启动", "INFO")
    
    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        # 在主线程中更新UI
        self.root.after(0, lambda: self._append_log(formatted_message, level))
    
    def _append_log(self, message, level):
        """在主线程中添加日志"""
        # 特殊处理分隔符
        if "=" in message and len(message.strip()) > 20 and message.strip().replace("=", "") == "":
            level = "TITLE"
        elif message.startswith("[OK]") or message.startswith("✅"):
            level = "SUCCESS"
        elif message.startswith("[X]") or message.startswith("❌"):
            level = "ERROR"
        elif message.startswith("[!]") or message.startswith("⚠️"):
            level = "WARNING"
        elif "步骤" in message and "/" in message:
            level = "TITLE"
        
        # 获取当前插入位置
        start_pos = self.log_text.index(tk.END + "-1c")
        
        # 插入消息
        self.log_text.insert(tk.END, message)
        
        # 获取插入后的位置
        end_pos = self.log_text.index(tk.END + "-1c")
        
        # 应用颜色标签
        self.log_text.tag_add(level, start_pos, end_pos)
        
        # 自动滚动到底部
        self.log_text.see(tk.END)
        
        # 限制日志长度（优化内存管理）
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 500:  # 从1000行降低到500行，减少内存占用
            # 删除前200行，保留最新的300行
            self.log_text.delete('1.0', '200.0')
            # 添加清理提示
            self.log_text.insert('1.0', "[系统] 日志已自动清理，保留最新300行\n")
            self.log_text.tag_add("INFO", '1.0', '2.0')
    
    def run_sync_workflow(self):
        """执行同步流程"""
        if self.is_running_sync:
            messagebox.showwarning("警告", "同步流程正在运行中，请等待完成。")
            return
        
        def run_sync():
            try:
                self.is_running_sync = True
                self.sync_button.config(text="同步运行中...", state="disabled")
                self.log_message("开始执行同步流程（手动触发，无冷却限制）", "INFO")
                
                # 更新托盘图标状态
                if self.system_tray:
                    self.system_tray.update_icon_status("running")
                
                # NEW VERSION: 2025-08-07 - 手动触发无冷却限制，但会更新全局冷却时间
                # 手动执行可以突破冷却限制，但执行后会重置冷却时间
                from core.global_cooldown import update_global_cooldown
                
                # OLD VERSION: 手动同步受冷却限制
                # cooldown_minutes = self.config.get_global_cooldown_minutes()
                # from core.global_cooldown import is_in_global_cooldown, get_remaining_global_cooldown, update_global_cooldown
                # 
                # if is_in_global_cooldown(cooldown_minutes):
                #     remaining = get_remaining_global_cooldown(cooldown_minutes)
                #     
                #     # 使用与显示一致的格式化逻辑
                #     if remaining >= 1.5:
                #         remaining_minutes = int(remaining)
                #         time_str = f"{remaining_minutes}分钟"
                #     elif remaining >= 1.0:
                #         time_str = "1分钟"
                #     else:
                #         remaining_seconds = int(remaining * 60)
                #         time_str = f"{remaining_seconds}秒"
                #     
                #     self.log_message(f"手动同步被全局冷却阻止，剩余 {time_str}", "WARNING")
                #     messagebox.showwarning("冷却期内", f"距离上次同步还不到 {cooldown_minutes} 分钟\n\n剩余冷却时间：{time_str}\n\n如需立即执行，可点击\"重置冷却\"按钮")
                #     return
                
                # 执行同步流程（GUI版本）
                success = sync_workflow.run_full_sync_workflow_gui(self.log_message)
                
                self.last_sync_time = datetime.now()
                # 更新全局冷却时间
                update_global_cooldown("手动触发")
                
                if success:
                    self.sync_success_count += 1
                    self.log_message("同步流程执行成功", "SUCCESS")
                    
                    # 更新托盘图标和通知
                    if self.system_tray:
                        self.system_tray.update_icon_status("success")
                        self.system_tray.show_notification("同步完成", "微信OneDrive冲突已成功解决")
                    
                    messagebox.showinfo("成功", "同步流程执行完成！")
                else:
                    self.sync_error_count += 1
                    self.log_message("同步流程执行失败", "ERROR")
                    
                    # 更新托盘图标和通知
                    if self.system_tray:
                        self.system_tray.update_icon_status("error")
                        self.system_tray.show_notification("同步失败", "同步流程执行失败，请查看日志")
                    
                    messagebox.showerror("错误", "同步流程执行失败，请查看日志。")
                    
            except Exception as e:
                self.sync_error_count += 1
                self.log_message(f"同步流程异常: {e}", "ERROR")
                
                # 更新托盘图标状态
                if self.system_tray:
                    self.system_tray.update_icon_status("error")
                    self.system_tray.show_notification("同步异常", f"同步流程发生异常: {e}")
                
                messagebox.showerror("错误", f"同步流程发生异常: {e}")
            finally:
                self.is_running_sync = False
                self.sync_button.config(text="🚀 立即执行同步流程", state="normal")
                
                # 恢复托盘图标到正常状态
                if self.system_tray:
                    self.system_tray.update_icon_status("normal")
        
        # 在新线程中运行
        thread = threading.Thread(target=run_sync, daemon=True)
        thread.start()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete('1.0', tk.END)
        self.log_message("日志已清空")
    
    def export_log(self):
        """导出日志"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if filename:
                content = self.log_text.get('1.0', tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log_message(f"日志已导出到: {filename}")
        except Exception as e:
            self.log_message(f"导出日志时出错: {e}", "ERROR")
    
    def export_config(self):
        """导出配置"""
        messagebox.showinfo("提示", "配置导出功能待实现")
    
    def import_config(self):
        """导入配置"""
        messagebox.showinfo("提示", "配置导入功能待实现")
    
    def open_config_file(self):
        """打开配置文件"""
        try:
            import subprocess
            config_path = "configs/sync_config.json"
            subprocess.run(["notepad", config_path])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开配置文件: {e}")
    
    def open_log_directory(self):
        """打开日志目录"""
        try:
            import subprocess
            subprocess.run(["explorer", "logs"])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开日志目录: {e}")
    
    def show_performance_stats(self):
        """显示性能统计"""
        try:
            summary = get_performance_summary()
            self.log_message(f"[性能] {summary}", "INFO")
            messagebox.showinfo("性能统计", f"当前性能状态：\n\n{summary}")
        except Exception as e:
            messagebox.showerror("错误", f"获取性能统计失败: {e}")
    
    def show_idle_timer_debug(self):
        """显示空闲计时器调试信息"""
        try:
            current_time = time.time()
            
            # 获取系统真实空闲时间
            system_idle = self.idle_detector.get_idle_time_seconds()
            
            debug_info = f"""空闲计时器调试信息：

系统状态：
- 系统空闲时间: {system_idle:.1f}秒
- 显示文本缓存: "{self._last_idle_display_text}"

应用状态：
- 微信状态: {self._wechat_status}
- OneDrive状态: {self._onedrive_status}

提示：
- 切换按钮根据实时状态自动调整
- 如果显示卡顿，可能是GUI更新频率问题"""
            
            self.log_message("[调试] 空闲计时器状态已记录", "INFO")
            messagebox.showinfo("空闲计时器调试", debug_info)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取调试信息失败: {e}")
    
    def toggle_debug_mode(self):
        """切换调试模式"""
        self._debug_enabled = not self._debug_enabled
        status = "启用" if self._debug_enabled else "禁用"
        self.log_message(f"[调试] 调试模式已{status}", "INFO")
        
        if self._debug_enabled:
            # 显示更新间隔统计
            if self._update_intervals:
                avg_interval = sum(self._update_intervals) / len(self._update_intervals)
                min_interval = min(self._update_intervals)
                max_interval = max(self._update_intervals)
                
                stats_text = (f"更新间隔统计（最近{len(self._update_intervals)}次）:\n"
                             f"平均: {avg_interval:.3f}秒\n"
                             f"最小: {min_interval:.3f}秒\n" 
                             f"最大: {max_interval:.3f}秒")
                messagebox.showinfo("调试统计", stats_text)
            else:
                messagebox.showinfo("调试模式", "调试模式已启用，将显示详细性能信息")
        else:
            messagebox.showinfo("调试模式", "调试模式已禁用")
    
    def show_about(self):
        """显示关于对话框"""
        try:
            # 获取性能摘要
            performance_summary = get_performance_summary()
            
            about_text = f"""微信OneDrive冲突解决工具 v2.0
            
这是一个自动化工具，用于解决微信Windows端与OneDrive同步冲突的问题。

主要功能：
• 自动检测并解决文件冲突
• 支持定时和空闲触发
• 提供友好的图形界面
• 详细的操作日志
• 实时性能监控
• 智能应用切换按钮

v2.0 新特性：
• 上下布局，更加紧凑
• 智能切换按钮（三种状态）
• 简化的控制面板
• 改进的用户体验

当前性能状态：
{performance_summary}

开发：Python + tkinter + ttkbootstrap
版本：v2.0 (智能切换版)"""
        except Exception:
            about_text = """微信OneDrive冲突解决工具 v2.0

这是一个自动化工具，用于解决微信Windows端与OneDrive同步冲突的问题。

主要功能：
• 自动检测并解决文件冲突
• 支持定时和空闲触发
• 提供友好的图形界面
• 详细的操作日志
• 实时性能监控
• 智能应用切换按钮

v2.0 新特性：
• 上下布局，更加紧凑
• 智能切换按钮（三种状态）
• 简化的控制面板
• 改进的用户体验

开发：Python + tkinter + ttkbootstrap
版本：v2.0 (智能切换版)"""
        
        messagebox.showinfo("关于", about_text)
    
    def reset_close_behavior(self):
        """重置关闭行为设置"""
        try:
            self.config.set_close_behavior("ask")
            self.config.set_remember_close_choice(False)
            self.log_message("关闭方式已重置，下次关闭时将重新询问")
            messagebox.showinfo("设置重置", "关闭方式设置已重置。\n下次关闭程序时将重新询问您的选择。")
        except Exception as e:
            self.log_message(f"重置关闭方式失败: {e}", "ERROR")
            messagebox.showerror("错误", f"重置设置失败: {e}")
    
    def on_closing(self):
        """窗口关闭事件处理"""
        # 检查是否记住了关闭方式
        close_behavior = self.config.get_close_behavior()
        
        if close_behavior == "ask":
            # 显示自定义关闭对话框
            try:
                # 确保导入自定义对话框
                if CloseDialog is None:
                    # 尝试重新导入
                    try:
                        from .close_dialog import CloseDialog as CustomCloseDialog
                    except ImportError:
                        try:
                            from close_dialog import CloseDialog as CustomCloseDialog
                        except ImportError:
                            CustomCloseDialog = None
                else:
                    CustomCloseDialog = CloseDialog
                
                if CustomCloseDialog:
                    self.log_message("显示自定义关闭对话框")
                    dialog = CustomCloseDialog(self.root, tray_available=(TRAY_AVAILABLE and self.system_tray))
                    result = dialog.show()
                    
                    if result['confirmed']:
                        # 用户确认关闭
                        if result['remember']:
                            # 记住选择
                            self.config.set_close_behavior(result['close_method'])
                            self.config.set_remember_close_choice(True)
                            self.log_message(f"已记住关闭方式: {result['close_method']}")
                        
                        # 执行相应的关闭操作
                        if result['close_method'] == "minimize":
                            self.minimize_to_tray()
                        else:  # exit
                            self.quit_application()
                    # 如果用户取消（confirmed=False），不做任何操作
                else:
                    # 对话框不可用，使用简单确认
                    self.log_message("自定义对话框不可用，使用默认确认框", "WARNING")
                    if messagebox.askyesno("确认退出", "是否确认退出程序？"):
                        self.quit_application()
                        
            except Exception as e:
                self.log_message(f"关闭对话框出错: {e}", "ERROR")
                # 出错时使用默认确认
                if messagebox.askyesno("确认退出", "是否确认退出程序？"):
                    self.quit_application()
                    
        elif close_behavior == "minimize":
            # 直接最小化到托盘
            if TRAY_AVAILABLE and self.system_tray:
                self.minimize_to_tray()
            else:
                # 托盘不可用，询问是否退出
                if messagebox.askyesno("托盘不可用", "系统托盘功能不可用，是否直接退出程序？"):
                    self.quit_application()
                    
        elif close_behavior == "exit":
            # 直接退出
            self.quit_application()
    
    def minimize_to_tray(self):
        """最小化到系统托盘"""
        if not TRAY_AVAILABLE:
            messagebox.showwarning("提示", "系统托盘功能不可用，需要安装: pip install pystray Pillow")
            return
            
        if not self.system_tray:
            messagebox.showerror("错误", "系统托盘对象未初始化")
            return
            
        try:
            # 确保托盘已启动
            if not self.system_tray.is_running:
                self.log_message("正在启动系统托盘...")
                success = self.system_tray.start_tray()
                if not success:
                    messagebox.showerror("错误", "无法启动系统托盘")
                    return
                # 等待托盘启动
                time.sleep(1)
            
            if self.system_tray.is_running:
                self.root.withdraw()  # 隐藏主窗口
                self.log_message("程序已最小化到系统托盘")
                
                # 延迟显示通知，确保托盘已经完全启动
                def show_delayed_notification():
                    import time
                    time.sleep(0.5)
                    if self.system_tray and self.system_tray.icon:
                        self.system_tray.show_notification(
                            "最小化到托盘", 
                            "程序继续在后台运行\n双击托盘图标可恢复窗口"
                        )
                
                import threading
                threading.Thread(target=show_delayed_notification, daemon=True).start()
            else:
                messagebox.showerror("错误", "无法启动系统托盘")
                
        except Exception as e:
            self.log_message(f"最小化到托盘失败: {e}", "ERROR")
            messagebox.showerror("错误", f"无法最小化到托盘: {e}")
    
    def restore_from_tray(self):
        """从托盘恢复窗口"""
        try:
            self.root.deiconify()  # 显示窗口
            self.root.lift()       # 提升到前台
            self.root.focus_force() # 强制焦点
            self.log_message("程序已从托盘恢复")
        except Exception as e:
            print(f"恢复窗口时出错: {e}")
    
    def quit_application(self):
        """退出应用程序"""
        try:
            # 停止托盘
            if self.system_tray:
                self.system_tray.stop_tray()
            
            # 退出主程序
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"退出程序时出错: {e}")
    
    def run(self):
        """运行GUI应用"""
        try:
            # 启动托盘（如果可用）- 在后台异步启动
            if TRAY_AVAILABLE and self.system_tray:
                def start_tray_async():
                    import time
                    time.sleep(1)  # 等待GUI完全启动
                    try:
                        tray_started = self.system_tray.start_tray()
                        if tray_started:
                            self.log_message("系统托盘已启动，可最小化到托盘运行")
                        else:
                            self.log_message("系统托盘启动失败，仅窗口模式可用", "WARNING")
                    except Exception as e:
                        self.log_message(f"托盘启动异常: {e}", "ERROR")
                
                import threading
                tray_thread = threading.Thread(target=start_tray_async, daemon=True)
                tray_thread.start()
                self.log_message("正在后台启动系统托盘...")
            else:
                self.log_message("系统托盘不可用，仅窗口模式可用", "INFO")
            
            self.root.mainloop()
        except Exception as e:
            print(f"运行GUI时出错: {e}")
        finally:
            # 确保托盘被清理
            if self.system_tray:
                self.system_tray.stop_tray()

    def reset_global_cooldown(self):
        """重置全局冷却时间"""
        from tkinter import messagebox
        
        # NEW VERSION: 2025-08-07 - 使用全局冷却管理器
        from core.global_cooldown import is_in_global_cooldown, get_remaining_global_cooldown, reset_global_cooldown
        cooldown_minutes = self.config.get_global_cooldown_minutes()
        
        # 检查是否有冷却时间需要重置
        if not is_in_global_cooldown(cooldown_minutes):
            messagebox.showinfo("提示", "当前没有全局冷却时间，无需重置。")
            return
        
        # 显示剩余冷却时间并确认重置
        remaining_time = get_remaining_global_cooldown(cooldown_minutes)
        
        # 使用与显示一致的格式化逻辑
        if remaining_time >= 1.5:
            remaining_minutes = int(remaining_time)
            time_str = f"{remaining_minutes}分钟"
        elif remaining_time >= 1.0:
            time_str = "1分钟"
        else:
            remaining_seconds = int(remaining_time * 60)
            time_str = f"{remaining_seconds}秒"
        
        result = messagebox.askyesno(
            "确认重置冷却时间",
            f"当前剩余冷却时间：{time_str}\n\n重置后将立即允许触发同步。\n注意：手动触发无冷却限制，可随时执行。\n\n确定要重置吗？",
            icon='question'
        )
        
        if result:
            # 使用全局冷却管理器重置
            reset_global_cooldown()
            
            # 重置本地显示变量
            self.last_idle_trigger_time = None
            self.cooldown_remaining = 0
            
            self.log_message("触发冷却时间已手动重置", "INFO")
            
            # 立即更新GUI显示
            self.update_system_idle_display()
            
            messagebox.showinfo("重置完成", "触发冷却时间已重置。")
        
        # OLD VERSION: 2025-08-07 - 仅重置静置触发冷却
        # # 检查是否有冷却时间需要重置
        # if self.cooldown_remaining <= 0:
        #     messagebox.showinfo("提示", "当前没有全局冷却时间，无需重置。")
        #     return
        # 
        # # 显示剩余冷却时间并确认重置
        # remaining_minutes = int(self.cooldown_remaining)
        # remaining_seconds = int((self.cooldown_remaining - remaining_minutes) * 60)
        # 
        # if remaining_minutes > 0:
        #     time_str = f"{remaining_minutes}分{remaining_seconds}秒"
        # else:
        #     time_str = f"{remaining_seconds}秒"
        # 
        # result = messagebox.askyesno(
        #     "确认重置冷却时间",
        #     f"当前剩余冷却时间：{time_str}\n\n重置后将立即允许自动触发同步。\n\n确定要重置吗？",
        #     icon='question'
        # )
        # 
        # if result:
        #     # 重置全局冷却时间
        #     self.last_idle_trigger_time = None
        #     self.cooldown_remaining = 0
        #     
        #     self.log_message("全局冷却时间已手动重置，自动触发恢复正常", "INFO")
        #     
        #     # 立即更新GUI显示
        #     self.update_system_idle_display()
        #     
        #     messagebox.showinfo("重置完成", "全局冷却时间已重置，自动触发功能已恢复。")

    def update_reset_cooldown_button_state(self):
        """更新重置冷却按钮的状态"""
        if hasattr(self, 'reset_cooldown_button'):
            try:
                if self.cooldown_remaining > 0:
                    # 有冷却时间时启用按钮
                    self.reset_cooldown_button.configure(state='normal')
                else:
                    # 没有冷却时间时禁用按钮
                    self.reset_cooldown_button.configure(state='disabled')
            except Exception as e:
                self.log_message(f"更新重置冷却按钮状态出错: {e}", "ERROR")

def main():
    """主函数"""
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"启动GUI时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()