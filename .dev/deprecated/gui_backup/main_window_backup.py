#!/usr/bin/env python3
"""
微信OneDrive冲突解决工具 - 现代化GUI主窗口
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

from wechat_controller import is_wechat_running, find_wechat_processes
from onedrive_controller import is_onedrive_running, get_onedrive_status
from config_manager import ConfigManager
from idle_detector import IdleDetector
from core.performance_monitor import start_performance_monitoring, get_performance_summary
import sync_workflow

class MainWindow:
    """主GUI窗口类"""
    
    def __init__(self):
        # 使用ttkbootstrap创建现代化主题的窗口
        self.root = ttk.Window(themename="cosmo")  # 使用现代化的cosmo主题
        self.root.title("微信OneDrive冲突解决工具")
        self.root.geometry("1000x1500")
        self.root.minsize(1000, 1500)  # 设置最小窗口尺寸
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
        
        # 配置更改跟踪
        self.config_changed = False
        self.original_config_values = {}
        
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
        """创建现代化主界面组件"""
        # 创建主容器，使用现代化的间距
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重，支持响应式布局
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)  # 日志区域可扩展
        
        # 创建响应式网格布局
        self.create_header_section(main_frame)  # 顶部标题
        self.create_dashboard_grid(main_frame)  # 主要仪表盘网格
        self.create_log_section(main_frame)     # 底部日志区域
        
    def create_header_section(self, parent):
        """创建现代化头部区域"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
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
            text="v2.1 | 性能优化版",
            font=("Microsoft YaHei UI", 10),
            bootstyle="secondary"
        )
        version_label.grid(row=0, column=1, sticky=tk.E)
        
        # 分隔线
        separator = ttk.Separator(header_frame, orient="horizontal")
        separator.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    
    def create_dashboard_grid(self, parent):
        """创建现代化仪表盘网格布局"""
        dashboard_frame = ttk.Frame(parent)
        dashboard_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 20))
        dashboard_frame.columnconfigure(0, weight=1)
        dashboard_frame.columnconfigure(1, weight=1)
        dashboard_frame.rowconfigure(0, weight=1)
        
        # 左侧：状态监控卡片
        self.create_status_card(dashboard_frame)
        
        # 右侧：控制和配置卡片
        self.create_control_config_card(dashboard_frame)
    
    def create_log_section(self, parent):
        """创建现代化日志区域"""
        log_card = ttk.LabelFrame(
            parent, 
            text="  📋 操作日志",
            padding="15",
            bootstyle="info"
        )
        log_card.grid(row=2, column=0, columnspan=2, sticky="nsew")
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
        self.log_message("🚀 现代化GUI界面已启动")
    
    def create_status_card(self, parent):
        """创建现代化状态监控卡片"""
        status_card = ttk.LabelFrame(
            parent,
            text="  📊 系统状态监控",
            padding="20",
            bootstyle="success"
        )
        status_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        status_card.columnconfigure(0, weight=1)
        
        # 状态网格容器
        status_grid = ttk.Frame(status_card)
        status_grid.grid(row=0, column=0, sticky="ew")
        status_grid.columnconfigure(1, weight=1)
        
        # 微信状态
        wechat_icon_label = ttk.Label(
            status_grid, 
            text="  微信状态:",
            image=self.icons.get('wechat'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=12
        )
        wechat_icon_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.wechat_status_label = ttk.Label(
            status_grid, 
            text="检查中...", 
            bootstyle="warning",
            font=("Microsoft YaHei UI", 10)
        )
        self.wechat_status_label.grid(row=0, column=1, sticky=tk.W, padx=(15, 0), pady=5)
        
        # OneDrive状态
        onedrive_icon_label = ttk.Label(
            status_grid, 
            text="  OneDrive:",
            image=self.icons.get('onedrive'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=12
        )
        onedrive_icon_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.onedrive_status_label = ttk.Label(
            status_grid, 
            text="检查中...", 
            bootstyle="warning",
            font=("Microsoft YaHei UI", 10)
        )
        self.onedrive_status_label.grid(row=1, column=1, sticky=tk.W, padx=(15, 0), pady=5)
        
        # 系统空闲时间
        idle_icon_label = ttk.Label(
            status_grid, 
            text="  空闲时间:",
            image=self.icons.get('idle'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=12
        )
        idle_icon_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.idle_time_label = ttk.Label(
            status_grid, 
            text="计算中...",
            bootstyle="info",
            font=("Microsoft YaHei UI", 10, "bold")
        )
        self.idle_time_label.grid(row=2, column=1, sticky=tk.W, padx=(15, 0), pady=5)
        
        # 分隔线
        ttk.Separator(status_card, orient="horizontal").grid(
            row=1, column=0, sticky="ew", pady=(15, 15)
        )
        
        # 统计信息区域
        stats_frame = ttk.Frame(status_card)
        stats_frame.grid(row=2, column=0, sticky="ew")
        stats_frame.columnconfigure(1, weight=1)
        
        # 上次同步时间
        sync_icon_label = ttk.Label(
            stats_frame, 
            text="  上次同步:",
            image=self.icons.get('sync'),
            compound="left",
            font=("Microsoft YaHei UI", 9),
            width=13
        )
        sync_icon_label.grid(row=0, column=0, sticky=tk.W, pady=3)
        self.last_sync_label = ttk.Label(
            stats_frame, 
            text="未执行",
            font=("Microsoft YaHei UI", 9),
            bootstyle="secondary"
        )
        self.last_sync_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # 成功/失败统计
        stats_icon_label = ttk.Label(
            stats_frame, 
            text="  成功/失败:",
            image=self.icons.get('stats'),
            compound="left",
            font=("Microsoft YaHei UI", 9),
            width=13
        )
        stats_icon_label.grid(row=1, column=0, sticky=tk.W, pady=3)
        self.stats_label = ttk.Label(
            stats_frame, 
            text="0 / 0",
            font=("Microsoft YaHei UI", 9),
            bootstyle="secondary"
        )
        self.stats_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # 冷却状态
        cooldown_icon_label = ttk.Label(
            stats_frame, 
            text="  触发冷却:",
            image=self.icons.get('cooldown'),
            compound="left",
            font=("Microsoft YaHei UI", 9),
            width=13
        )
        cooldown_icon_label.grid(row=2, column=0, sticky=tk.W, pady=3)
        self.cooldown_label = ttk.Label(
            stats_frame, 
            text="无冷却",
            font=("Microsoft YaHei UI", 9),
            bootstyle="success"
        )
        self.cooldown_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    def create_control_config_card(self, parent):
        """创建现代化控制和配置卡片"""
        control_card = ttk.LabelFrame(
            parent,
            text="  🎮 控制面板",
            padding="20",
            bootstyle="primary"
        )
        control_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        control_card.columnconfigure(0, weight=1)
        
        # 主要操作按钮
        self.sync_button = ttk.Button(
            control_card, 
            text="🚀 立即执行同步流程", 
            command=self.run_sync_workflow,
            bootstyle="success",
            width=25
        )
        self.sync_button.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        # 应用控制区域
        app_control_frame = ttk.LabelFrame(control_card, text="应用控制", padding="10")
        app_control_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        app_control_frame.columnconfigure(0, weight=1)
        app_control_frame.columnconfigure(1, weight=1)
        
        # 微信控制按钮
        ttk.Button(
            app_control_frame, 
            text="启动微信", 
            command=self.start_wechat,
            bootstyle="outline-success",
            width=12
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=3)
        
        ttk.Button(
            app_control_frame, 
            text="停止微信", 
            command=self.stop_wechat,
            bootstyle="outline-danger",
            width=12
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=3)
        
        # OneDrive控制按钮
        ttk.Button(
            app_control_frame, 
            text="启动OneDrive", 
            command=self.start_onedrive,
            bootstyle="outline-info",
            width=12
        ).grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=3)
        
        ttk.Button(
            app_control_frame, 
            text="暂停OneDrive", 
            command=self.pause_onedrive,
            bootstyle="outline-warning",
            width=12
        ).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=3)
        
        # 快速配置区域
        config_frame = ttk.LabelFrame(control_card, text="快速配置", padding="15")
        config_frame.grid(row=2, column=0, sticky="ew")
        config_frame.columnconfigure(0, weight=1)
        
        # 静置触发配置
        idle_frame = ttk.Frame(config_frame)
        idle_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        idle_frame.columnconfigure(2, weight=1)
        
        self.idle_enabled_var = tk.BooleanVar(value=self.config.is_idle_trigger_enabled())
        idle_check = ttk.Checkbutton(
            idle_frame, 
            text="⏰ 静置触发", 
            variable=self.idle_enabled_var,
            command=self.on_config_change,
            bootstyle="round-toggle"
        )
        idle_check.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(idle_frame, text="分钟:").grid(row=0, column=1, sticky=tk.W, padx=(15, 5))
        
        self.idle_minutes_var = tk.StringVar(value=str(self.config.get_idle_minutes()))
        idle_spinbox = ttk.Spinbox(
            idle_frame, 
            from_=1, 
            to=120, 
            width=8, 
            textvariable=self.idle_minutes_var,
            command=self.on_config_change,
            bootstyle="info"
        )
        idle_spinbox.grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        idle_spinbox.bind('<KeyRelease>', lambda e: self.on_config_change())
        
        # 定时触发配置
        scheduled_frame = ttk.Frame(config_frame)
        scheduled_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        scheduled_frame.columnconfigure(2, weight=1)
        
        self.scheduled_enabled_var = tk.BooleanVar(value=self.config.is_scheduled_trigger_enabled())
        scheduled_check = ttk.Checkbutton(
            scheduled_frame, 
            text="📅 定时触发", 
            variable=self.scheduled_enabled_var,
            command=self.on_config_change,
            bootstyle="round-toggle"
        )
        scheduled_check.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(scheduled_frame, text="时间:").grid(row=0, column=1, sticky=tk.W, padx=(15, 5))
        
        self.scheduled_time_var = tk.StringVar(value=self.config.get_scheduled_time())
        time_entry = ttk.Entry(
            scheduled_frame, 
            width=10, 
            textvariable=self.scheduled_time_var,
            bootstyle="info"
        )
        time_entry.grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        time_entry.bind('<KeyRelease>', lambda e: self.on_config_change())
        
        # 关闭行为配置
        close_frame = ttk.Frame(config_frame)
        close_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        close_frame.columnconfigure(1, weight=1)
        
        ttk.Label(close_frame, text="🚪 关闭行为:").grid(row=0, column=0, sticky=tk.W)
        
        self.close_behavior_var = tk.StringVar(value=self.config.get_close_behavior())
        close_options = [
            ("询问我", "ask"),
            ("最小化到托盘", "minimize"),
            ("直接退出", "exit")
        ]
        
        self.close_display_to_value = {text: value for text, value in close_options}
        self.close_value_to_display = {value: text for text, value in close_options}
        
        self.close_combobox = ttk.Combobox(
            close_frame,
            values=[text for text, value in close_options],
            state="readonly",
            width=15,
            bootstyle="info"
        )
        self.close_combobox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        current_behavior = self.config.get_close_behavior()
        if current_behavior in self.close_value_to_display:
            self.close_combobox.set(self.close_value_to_display[current_behavior])
        
        def on_close_behavior_change(event):
            selected_text = self.close_combobox.get()
            if selected_text in self.close_display_to_value:
                new_value = self.close_display_to_value[selected_text]
                self.close_behavior_var.set(new_value)
                self.on_config_change()
        
        self.close_combobox.bind('<<ComboboxSelected>>', on_close_behavior_change)
        
        # 配置状态和按钮
        self.config_status_label = ttk.Label(
            config_frame, 
            text="", 
            font=("Microsoft YaHei UI", 9),
            bootstyle="warning"
        )
        self.config_status_label.grid(row=3, column=0, sticky=tk.W, pady=(5, 10))
        
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=4, column=0, sticky="ew")
        
        self.apply_config_button = ttk.Button(
            button_frame, 
            text="应用更改", 
            command=self.apply_config_changes,
            state="disabled",
            bootstyle="success",
            width=12
        )
        self.apply_config_button.grid(row=0, column=0, padx=(0, 5))
        
        self.reset_config_button = ttk.Button(
            button_frame, 
            text="重置", 
            command=self.reset_config_changes,
            state="disabled",
            bootstyle="outline-secondary",
            width=12
        )
        self.reset_config_button.grid(row=0, column=1)
        
        # 保存原始配置值
        self.save_original_config_values()

        
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
                    
                    # 不再需要用户活动检查，直接使用系统空闲时间
                    
                    # 不再需要系统空闲时间校准，直接使用实时API调用
                    
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
        """启动独立的系统状态检查线程（避免阻塞空闲时间显示）"""
        def status_check_loop():
            while True:
                try:
                    # 每10秒检查一次系统状态（而不是每5秒）
                    time.sleep(10)
                    
                    status_update_start = time.time()
                    self.update_other_status()
                    status_update_duration = time.time() - status_update_start
                    
                    # 记录状态更新耗时
                    if self._debug_enabled and status_update_duration > 0.1:
                        print(f"[调试] 独立状态更新耗时: {status_update_duration:.3f}秒")
                        
                except Exception as e:
                    print(f"系统状态检查出错: {e}")
                    time.sleep(30)  # 出错时等待30秒
        
        thread = threading.Thread(target=status_check_loop, daemon=True)
        thread.start()
    
    def check_user_activity_quick(self):
        """快速检查用户活动（每0.1秒调用，API很快~0.05ms）"""
        try:
            current_time = time.time()
            
            # API调用很快，每0.1秒调用，提供0.1秒内的快速响应
            if current_time - self._last_activity_check_time < 0.05:
                return
            
            # 获取当前系统空闲时间
            current_idle = self.idle_detector.get_idle_time_seconds()
            
            # 如果系统空闲时间明显减少，说明用户有活动
            if self._cached_system_idle > 0 and current_idle < self._cached_system_idle - 1:
                # 用户活动detected！立即重置计时器
                self._local_idle_start_time = current_time
                self._local_idle_seconds = 0
                self._idle_timer_stable = True
                # 清空显示缓存，确保立即显示"0秒"
                self._last_idle_display_text = ""
                
                if self._debug_enabled:
                    print(f"[快速检测] 用户活动！重置计时器 (系统空闲: {current_idle:.1f}s)")
            
            # 更新缓存的系统空闲时间
            self._cached_system_idle = current_idle
            self._last_activity_check_time = current_time
            
        except Exception as e:
            if self._debug_enabled:
                print(f"快速用户活动检查出错: {e}")
            # 出错时避免无限重试
            self._last_activity_check_time = current_time
    
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
    
    def format_local_idle_time_fast(self, total_seconds):
        """快速格式化空闲时间显示（优化字符串操作）"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"
    
    def update_cooldown_display_optimized(self):
        """优化的冷却时间显示更新"""
        try:
            if not hasattr(self, 'cooldown_label'):
                return
                
            if not self.config.is_idle_trigger_enabled():
                new_text = "静置触发未启用"
                if new_text != self._last_cooldown_display_text:
                    self.cooldown_label.config(text=new_text, bootstyle="secondary")
                    self._last_cooldown_display_text = new_text
                return
            
            if self.last_idle_trigger_time is None:
                new_text = "无冷却（未进行过静置触发）"
                if new_text != self._last_cooldown_display_text:
                    self.cooldown_label.config(text=new_text, bootstyle="success")
                    self._last_cooldown_display_text = new_text
                return
            
            # 计算剩余冷却时间
            current_time = datetime.now()
            time_since_last_sync = (current_time - self.last_idle_trigger_time).total_seconds()
            cooldown_seconds = self.config.get_idle_cooldown_minutes() * 60
            remaining_seconds = max(0, cooldown_seconds - time_since_last_sync)
            
            if remaining_seconds <= 0:
                new_text = "无冷却（可以触发静置同步）"
                new_bootstyle = "success"
            else:
                # 格式化剩余冷却时间显示
                remaining_minutes = int(remaining_seconds // 60)
                remaining_sec = int(remaining_seconds % 60)
                
                if remaining_minutes > 0:
                    new_text = f"冷却中：{remaining_minutes}分{remaining_sec}秒"
                else:
                    new_text = f"冷却中：{remaining_sec}秒"
                
                new_bootstyle = "warning"
            
            # 只有当文本真正改变时才更新GUI
            if new_text != self._last_cooldown_display_text:
                self.cooldown_label.config(text=new_text, bootstyle=new_bootstyle)
                self._last_cooldown_display_text = new_text
                
        except Exception as e:
            print(f"更新冷却时间显示出错: {e}")
    
    def check_system_idle_time(self):
        """检查系统空闲时间（低频率校准，配合快速检测）"""
        try:
            current_time = time.time()
            self._last_system_check_time = current_time
            
            # 监控系统API调用性能
            api_start_time = time.time()
            system_idle_seconds = self.idle_detector.get_idle_time_seconds()
            api_duration = time.time() - api_start_time
            
            # 记录API调用耗时
            if self._debug_enabled and api_duration > 0.05:  # 超过50ms记录
                print(f"[调试] 系统API调用耗时: {api_duration:.3f}秒")
            
            # 记录极端情况
            if api_duration > 0.5:  # 超过500ms是极端情况
                print(f"[警告] 系统API调用极慢: {api_duration:.3f}秒，可能导致卡顿")
            
            # 首次启动时初始化计时器
            if self._local_idle_start_time is None:
                self._local_idle_start_time = current_time - system_idle_seconds
                self._local_idle_seconds = system_idle_seconds
                self._idle_timer_stable = True
                self._cached_system_idle = system_idle_seconds  # 初始化缓存
                if self._debug_enabled:
                    print(f"[计时器] 初始化计时器，系统空闲: {system_idle_seconds:.1f}秒")
                
            elif self._idle_timer_stable:
                # 仅用于大幅校准，用户活动检测已移到快速检测中
                local_idle = current_time - self._local_idle_start_time
                time_diff = abs(local_idle - system_idle_seconds)
                
                # 记录时间差异用于分析
                if self._debug_enabled and time_diff > 8:
                    print(f"[调试] 时间差异: 本地{local_idle:.1f}s vs 系统{system_idle_seconds:.1f}s (差异{time_diff:.1f}s)")
                
                # 只有在差异超过15秒时才重新校准（减少干扰快速检测）
                if time_diff > 15:
                    self._local_idle_start_time = current_time - system_idle_seconds
                    self._cached_system_idle = system_idle_seconds  # 更新缓存
                    print(f"[计时器] 大幅校准计时器，差异: {time_diff:.1f}秒")
                    # 重置显示缓存
                    self._last_idle_display_text = ""
            
            # 保存当前系统空闲时间用于下次比较
            self._last_system_idle_time = system_idle_seconds
            
        except Exception as e:
            print(f"检查系统空闲时间出错: {e}")
            # 出错时保持计时器稳定运行
            if self._local_idle_start_time is not None:
                self._idle_timer_stable = True
    
    def format_local_idle_time(self, total_seconds):
        """格式化本地计时器的空闲时间显示"""
        total_seconds = int(total_seconds)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"
    
    def update_other_status(self):
        """更新其他状态信息（低频率，优化版）"""
        try:
            # 更新微信状态（仅在状态变化时更新GUI）
            wechat_running = is_wechat_running()
            if wechat_running:
                processes = find_wechat_processes()
                new_wechat_status = f"运行中 ({len(processes)}个进程)"
            else:
                new_wechat_status = "未运行"
            
            if new_wechat_status != self._last_wechat_status:
                bootstyle = "success" if wechat_running else "danger"
                self.wechat_status_label.config(text=new_wechat_status, bootstyle=bootstyle)
                self._last_wechat_status = new_wechat_status
            
            # 更新OneDrive状态（仅在状态变化时更新GUI）
            onedrive_running = is_onedrive_running()
            new_onedrive_status = "运行中" if onedrive_running else "未运行"
            
            if new_onedrive_status != self._last_onedrive_status:
                bootstyle = "success" if onedrive_running else "danger"
                self.onedrive_status_label.config(text=new_onedrive_status, bootstyle=bootstyle)
                self._last_onedrive_status = new_onedrive_status
            
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
            
        except Exception as e:
            print(f"更新其他状态出错: {e}")
        
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
                                        self.root.after(0, lambda: self.sync_button.config(text="立即执行同步流程", state="normal"))
                                        
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
        
    
    def update_cooldown_display(self):
        """更新冷却时间显示"""
        try:
            if not hasattr(self, 'cooldown_label'):
                return
                
            if not self.config.is_idle_trigger_enabled():
                self.cooldown_label.config(text="静置触发未启用", foreground="gray")
                return
            
            if self.last_idle_trigger_time is None:
                self.cooldown_label.config(text="无冷却（未进行过静置触发）", foreground="green")
                return
            
            # 计算距离上次静置触发的时间
            current_time = datetime.now()
            time_since_last_sync = (current_time - self.last_idle_trigger_time).total_seconds()
            
            # 获取冷却时间设置（分钟转秒）
            cooldown_minutes = self.config.get_idle_cooldown_minutes()
            cooldown_seconds = cooldown_minutes * 60
            
            # 计算剩余冷却时间
            remaining_seconds = max(0, cooldown_seconds - time_since_last_sync)
            
            if remaining_seconds <= 0:
                new_text = "无冷却（可以触发静置同步）"
                new_color = "green"
            else:
                # 格式化剩余冷却时间显示
                remaining_minutes = int(remaining_seconds // 60)
                remaining_sec = int(remaining_seconds % 60)
                
                if remaining_minutes > 0:
                    new_text = f"冷却中：{remaining_minutes}分{remaining_sec}秒"
                else:
                    new_text = f"冷却中：{remaining_sec}秒"
                
                new_color = "orange"
            
            # 只有当文本真正改变时才更新GUI（减少不必要的更新）
            if not hasattr(self, '_last_cooldown_text') or self._last_cooldown_text != new_text:
                self.cooldown_label.config(text=new_text, foreground=new_color)
                self._last_cooldown_text = new_text
                
        except Exception as e:
            print(f"更新冷却时间显示出错: {e}")
            if hasattr(self, 'cooldown_label'):
                self.cooldown_label.config(text="冷却状态未知", foreground="red")
    
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
                self.log_message("开始执行同步流程", "INFO")
                
                # 更新托盘图标状态
                if self.system_tray:
                    self.system_tray.update_icon_status("running")
                
                # 执行同步流程（GUI版本）
                success = sync_workflow.run_full_sync_workflow_gui(self.log_message)
                
                self.last_sync_time = datetime.now()
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
                self.sync_button.config(text="立即执行同步流程", state="normal")
                
                # 恢复托盘图标到正常状态
                if self.system_tray:
                    self.system_tray.update_icon_status("normal")
        
        # 在新线程中运行
        thread = threading.Thread(target=run_sync, daemon=True)
        thread.start()
    
    def start_wechat(self):
        """启动微信"""
        def start_wechat_thread():
            try:
                from wechat_controller import start_wechat
                self.log_message("正在启动微信...")
                success = start_wechat()
                if success:
                    self.log_message("微信启动成功", "SUCCESS")
                    messagebox.showinfo("成功", "微信已启动")
                else:
                    self.log_message("微信启动失败", "ERROR")
                    error_msg = ("微信启动失败，可能的原因：\n\n"
                               "1. 微信未安装或安装路径异常\n"
                               "2. 微信程序被防病毒软件阻止\n"
                               "3. 需要管理员权限\n\n"
                               "建议解决方案：\n"
                               "• 尝试手动启动微信确认是否正常\n"
                               "• 以管理员身份运行此程序\n"
                               "• 检查微信安装目录是否存在")
                    messagebox.showerror("微信启动失败", error_msg)
            except Exception as e:
                self.log_message(f"启动微信时出错: {e}", "ERROR")
                messagebox.showerror("错误", f"启动微信时出错: {e}")
        
        # 在新线程中运行避免阻塞GUI
        thread = threading.Thread(target=start_wechat_thread, daemon=True)
        thread.start()
    
    def stop_wechat(self):
        """停止微信"""
        try:
            from wechat_controller import stop_wechat
            self.log_message("正在停止微信...")
            success = stop_wechat()
            if success:
                self.log_message("微信已停止", "SUCCESS")
            else:
                self.log_message("停止微信失败", "ERROR")
        except Exception as e:
            self.log_message(f"停止微信时出错: {e}", "ERROR")
    
    def start_onedrive(self):
        """启动OneDrive"""
        def start_onedrive_thread():
            try:
                from onedrive_controller import start_onedrive
                self.log_message("正在启动OneDrive...")
                success = start_onedrive()
                if success:
                    self.log_message("OneDrive启动成功", "SUCCESS")
                    messagebox.showinfo("成功", "OneDrive已启动")
                else:
                    self.log_message("OneDrive启动失败", "ERROR")
                    messagebox.showerror("错误", "OneDrive启动失败，可能是未找到安装路径")
            except Exception as e:
                self.log_message(f"启动OneDrive时出错: {e}", "ERROR")
                messagebox.showerror("错误", f"启动OneDrive时出错: {e}")
        
        # 在新线程中运行避免阻塞GUI
        thread = threading.Thread(target=start_onedrive_thread, daemon=True)
        thread.start()
    
    def pause_onedrive(self):
        """暂停OneDrive"""
        try:
            from onedrive_controller import pause_onedrive_sync
            self.log_message("正在暂停OneDrive...")
            success = pause_onedrive_sync()
            if success:
                self.log_message("OneDrive已暂停", "SUCCESS")
            else:
                self.log_message("暂停OneDrive失败", "ERROR")
        except Exception as e:
            self.log_message(f"暂停OneDrive时出错: {e}", "ERROR")
    
    def save_original_config_values(self):
        """保存原始配置值"""
        try:
            self.original_config_values = {
                'idle_enabled': self.config.is_idle_trigger_enabled(),
                'idle_minutes': str(self.config.get_idle_minutes()),
                'scheduled_enabled': self.config.is_scheduled_trigger_enabled(),
                'scheduled_time': self.config.get_scheduled_time(),
                'close_behavior': self.config.get_close_behavior()
            }
        except Exception as e:
            print(f"保存原始配置值出错: {e}")
    
    def on_config_change(self):
        """检测配置更改"""
        try:
            # 检查是否有配置更改
            current_values = {
                'idle_enabled': self.idle_enabled_var.get(),
                'idle_minutes': self.idle_minutes_var.get(),
                'scheduled_enabled': self.scheduled_enabled_var.get(),
                'scheduled_time': self.scheduled_time_var.get(),
                'close_behavior': self.close_behavior_var.get() if hasattr(self, 'close_behavior_var') else self.original_config_values.get('close_behavior', 'ask')
            }
            
            # 比较当前值与原始值
            self.config_changed = current_values != self.original_config_values
            
            # 更新UI状态
            if self.config_changed:
                self.config_status_label.config(text="配置已修改，点击'应用更改'保存", foreground="orange")
                self.apply_config_button.config(state="normal")
                self.reset_config_button.config(state="normal")
            else:
                self.config_status_label.config(text="", foreground="blue")
                self.apply_config_button.config(state="disabled")
                self.reset_config_button.config(state="disabled")
                
        except Exception as e:
            print(f"检测配置更改出错: {e}")
    
    def apply_config_changes(self):
        """应用配置更改"""
        try:
            # 记录之前的静置触发状态
            old_idle_enabled = self.config.is_idle_trigger_enabled()
            
            # 更新配置对象
            config_data = self.config.config.copy()
            
            # 更新静置触发设置
            config_data['idle_trigger']['enabled'] = self.idle_enabled_var.get()
            try:
                config_data['idle_trigger']['idle_minutes'] = int(self.idle_minutes_var.get())
            except ValueError:
                self.log_message("空闲时间必须是有效数字，使用原始值", "WARNING")
                pass
            
            # 更新定时触发设置
            config_data['scheduled_trigger']['enabled'] = self.scheduled_enabled_var.get()
            config_data['scheduled_trigger']['time'] = self.scheduled_time_var.get()
            
            # 更新关闭行为设置
            if hasattr(self, 'close_behavior_var'):
                config_data['gui']['close_behavior'] = self.close_behavior_var.get()
                # 如果修改了关闭行为，重置记住选择状态
                config_data['gui']['remember_close_choice'] = False
            
            # 保存配置
            success = self.config.save_config(config_data)
            if success:
                self.log_message("✅ 配置已成功应用并保存", "SUCCESS")
                
                # 更新原始配置值
                self.save_original_config_values()
                
                # 重置更改状态
                self.config_changed = False
                self.config_status_label.config(text="配置已保存", foreground="green")
                self.apply_config_button.config(state="disabled")
                self.reset_config_button.config(state="disabled")
                
                # 检查静置触发状态是否改变，如果改变则重启监控线程
                new_idle_enabled = self.config.is_idle_trigger_enabled()
                if old_idle_enabled != new_idle_enabled:
                    if new_idle_enabled:
                        self.log_message("静置触发已启用，正在启动自动监控线程")
                        # 重新启动监控线程
                        self.start_auto_monitor_thread()
                    else:
                        self.log_message("静置触发已禁用，自动监控线程将在下次检查时停止")
            else:
                self.log_message("❌ 保存配置失败", "ERROR")
            
        except Exception as e:
            self.log_message(f"应用配置更改时出错: {e}", "ERROR")
    
    def reset_config_changes(self):
        """重置配置更改"""
        try:
            # 恢复原始值
            self.idle_enabled_var.set(self.original_config_values['idle_enabled'])
            self.idle_minutes_var.set(self.original_config_values['idle_minutes'])
            self.scheduled_enabled_var.set(self.original_config_values['scheduled_enabled'])
            self.scheduled_time_var.set(self.original_config_values['scheduled_time'])
            self.close_behavior_var.set(self.original_config_values['close_behavior'])
            
            # 更新下拉框显示
            if hasattr(self, 'close_combobox'):
                behavior = self.original_config_values['close_behavior']
                if behavior in self.close_value_to_display:
                    self.close_combobox.set(self.close_value_to_display[behavior])
            
            # 重置状态
            self.config_changed = False
            self.config_status_label.config(text="配置已重置", foreground="blue")
            self.apply_config_button.config(state="disabled")
            self.reset_config_button.config(state="disabled")
            
            self.log_message("配置已重置为原始值")
            
        except Exception as e:
            self.log_message(f"重置配置时出错: {e}", "ERROR")
    
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
            
            # 计算本地计时器时间
            if self._local_idle_start_time:
                local_idle = current_time - self._local_idle_start_time
            else:
                local_idle = 0
            
            debug_info = f"""空闲计时器调试信息：

本地计时器状态：
- 是否稳定: {self._idle_timer_stable}
- 启动时间: {self._local_idle_start_time}
- 本地空闲时间: {local_idle:.1f}秒
- 显示文本缓存: "{self._last_idle_display_text}"

系统检查状态：
- 系统空闲时间: {system_idle:.1f}秒
- 上次系统空闲: {self._last_system_idle_time:.1f}秒
- 上次检查时间: {self._last_system_check_time}

时间差异：
- 本地vs系统: {abs(local_idle - system_idle):.1f}秒

提示：
- 如果时间差异过大（>10秒），计时器会自动校准
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

当前性能状态：
{performance_summary}

开发：Python + tkinter
版本：v2.0 (性能优化版)"""
        except Exception:
            about_text = """微信OneDrive冲突解决工具 v2.0

这是一个自动化工具，用于解决微信Windows端与OneDrive同步冲突的问题。

主要功能：
• 自动检测并解决文件冲突
• 支持定时和空闲触发
• 提供友好的图形界面
• 详细的操作日志
• 实时性能监控

开发：Python + tkinter
版本：v2.0 (性能优化版)"""
        
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