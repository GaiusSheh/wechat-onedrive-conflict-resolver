#!/usr/bin/env python3
"""
微信OneDrive冲突解决工具 - 现代化GUI主窗口 v2.1
性能优化版本：解决卡顿问题
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
    """主GUI窗口类 - v2.1 性能优化版"""
    
    def __init__(self):
        # 使用ttkbootstrap创建现代化主题的窗口
        self.root = ttk.Window(themename="cosmo")  # 使用现代化的cosmo主题
        self.root.title("微信OneDrive冲突解决工具 v2.1")
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
        
        # 全局冷却机制
        self.last_global_trigger_time = None
        
        # === 性能优化：应用状态缓存和控制 ===
        self._wechat_status = None  # None=检查中, True=运行, False=未运行
        self._onedrive_status = None  # None=检查中, True=运行, False=未运行
        self._last_wechat_check_time = 0
        self._last_onedrive_check_time = 0
        self._app_status_check_interval = 15  # 增加到15秒，减少API调用频率
        self._status_check_lock = threading.Lock()  # 防止并发检查
        self._status_check_in_progress = False
        
        # 空闲时间显示优化
        self._last_idle_display_text = ""
        self._last_idle_update_time = 0
        self._idle_update_interval = 1.0  # 1秒更新一次
        
        # 冷却时间显示优化（模仿静置时间）
        self._last_cooldown_display_text = ""
        self._last_cooldown_update_time = 0
        self._cooldown_update_interval = 1.0  # 1秒更新一次，和静置时间一致
        
        # GUI更新队列优化
        self._gui_update_pending = False
        self._pending_updates = {}  # 批量处理GUI更新
        
        # 调试控制
        self._debug_enabled = False  # 默认关闭调试，减少打印开销
        
        # 统计显示缓存
        self._last_sync_time_str = None
        self._last_stats_text = None
        self._last_cooldown_display_text = ""
        
        # 冷却计时器优化
        self._cooldown_timer_thread = None
        self._cooldown_timer_running = False
        self._last_cooldown_update_time = 0
        self._cooldown_update_interval = 1.0  # 1秒更新一次，像空闲时间一样
        
        # 文件日志管理
        self._setup_file_logging()
        
        # 系统托盘
        self.system_tray = None
        if TRAY_AVAILABLE and SystemTray:
            self.system_tray = SystemTray(self)
        
        # 创建界面
        self.create_widgets()
        # self.create_menu()  # 移除顶部菜单栏
        
        # 替换占位符为真实内容
        self.replace_placeholders_with_real_content()
        
        # 启动系统托盘（界面创建后）
        if self.system_tray:
            try:
                success = self.system_tray.start_tray()
                if success:
                    self.log_message("系统托盘已启动", "INFO")
                else:
                    self.log_message("系统托盘启动失败", "WARNING")
            except Exception as e:
                self.log_message(f"系统托盘启动异常: {e}", "ERROR")
                self.system_tray = None
        
        # 强制更新窗口布局
        self.root.update_idletasks()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # === 优化的线程启动 ===
        # 1. 空闲时间显示线程（轻量级，高频）
        self.start_idle_display_thread()
        
        # 2. 应用状态检查线程（重量级，低频）
        self.start_app_status_thread()
        
        # 3. 自动监控线程（如果启用）
        self.start_auto_monitor_thread()
        
        # 4. 性能监控
        start_performance_monitoring(self.log_message)
        
        # 5. 启动独立的冷却计时器
        self.start_cooldown_timer()
        
        # 测试日志级别过滤
        self.log_message("测试DEBUG级别日志 - 如果配置为info，此条不应显示", "DEBUG")
        self.log_message("测试INFO级别日志 - 此条应该显示", "INFO")
        
    def create_widgets(self):
        """创建现代化主界面组件 - v2.1上下布局"""
        # 创建主容器，使用现代化的间距
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重，支持响应式布局
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=2)  # 状态面板 - 增加权重
        main_frame.rowconfigure(2, weight=0)  # 控制面板 - 保持固定高度
        main_frame.rowconfigure(3, weight=2)  # 日志区域 - 减少相对权重
        
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
            text="v2.1 | 性能优化版",
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
        
        # 所有状态行的统一容器
        all_status_frame = ttk.Frame(status_card)
        all_status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 0))
        all_status_frame.columnconfigure(1, weight=1)
        
        # 微信状态行
        wechat_frame = ttk.Frame(all_status_frame)
        wechat_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(5, 8))
        wechat_frame.columnconfigure(1, weight=1)
        
        wechat_icon_label = ttk.Label(
            wechat_frame, 
            text="  微信状态:",
            image=self.icons.get('wechat'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=12,
            anchor="w"
        )
        wechat_icon_label.grid(row=0, column=0, sticky="ew", ipady=3)
        
        self.wechat_status_label = ttk.Label(
            wechat_frame, 
            text="检查中...", 
            bootstyle="warning",
            font=("Microsoft YaHei UI", 10),
            anchor="w"
        )
        self.wechat_status_label.grid(row=0, column=1, sticky="ew", padx=(15, 15), ipady=3)
        
        # 微信智能切换按钮
        self.wechat_toggle_button = ttk.Button(
            wechat_frame,
            text="查询中...",
            state="disabled",
            command=self.toggle_wechat,
            bootstyle="outline-secondary",
            width=12
        )
        self.wechat_toggle_button.grid(row=0, column=2, sticky="e", ipady=2)
        
        # OneDrive状态行
        onedrive_frame = ttk.Frame(all_status_frame)
        onedrive_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        onedrive_frame.columnconfigure(1, weight=1)
        
        onedrive_icon_label = ttk.Label(
            onedrive_frame, 
            text="  OneDrive:",
            image=self.icons.get('onedrive'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=12,
            anchor="w"
        )
        onedrive_icon_label.grid(row=0, column=0, sticky="ew", ipady=3)
        
        self.onedrive_status_label = ttk.Label(
            onedrive_frame, 
            text="检查中...", 
            bootstyle="warning",
            font=("Microsoft YaHei UI", 10),
            anchor="w"
        )
        self.onedrive_status_label.grid(row=0, column=1, sticky="ew", padx=(15, 15), ipady=3)
        
        # OneDrive智能切换按钮
        self.onedrive_toggle_button = ttk.Button(
            onedrive_frame,
            text="查询中...",
            state="disabled",
            command=self.toggle_onedrive,
            bootstyle="outline-secondary",
            width=12
        )
        self.onedrive_toggle_button.grid(row=0, column=2, sticky="e", ipady=2)
        
        # 系统空闲时间
        idle_frame = ttk.Frame(all_status_frame)
        idle_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        idle_frame.columnconfigure(1, weight=1)
        
        idle_icon_label = ttk.Label(
            idle_frame, 
            text="  空闲时间:",
            image=self.icons.get('idle'),
            compound="left",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=12,
            anchor="w"
        )
        idle_icon_label.grid(row=0, column=0, sticky="ew", ipady=3)
        
        self.idle_time_label = ttk.Label(
            idle_frame, 
            text="计算中...",
            bootstyle="info",
            anchor="w",
            font=("Microsoft YaHei UI", 10, "bold")
        )
        self.idle_time_label.grid(row=0, column=1, sticky="ew", padx=(15, 15), ipady=3)
        
        # 分隔线
        ttk.Separator(status_card, orient="horizontal").grid(
            row=1, column=0, sticky="ew", pady=(15, 15)
        )
        
        # 统计信息区域
        stats_frame = ttk.Frame(status_card)
        stats_frame.grid(row=2, column=0, sticky="ew")
        stats_frame.columnconfigure(1, weight=1)
        
        # 统一的行高和对齐设置 - 与上面系统状态区域保持一致
        label_width = 14
        uniform_pady = 4   # 与上面区域的8px行间距相比，稍小一些
        uniform_ipady = 3  # 与上面区域保持一致的ipady=3
        
        # 使用占位符确保三行固定位置和间距
        
        # === 第0行：上次同步时间 ===
        # 占位符1 - 标签
        placeholder1 = ttk.Label(
            stats_frame, 
            text="  [行1标签]",
            font=("Microsoft YaHei UI", 9),
            width=label_width,
            anchor="w"
        )
        placeholder1.grid(row=0, column=0, sticky="ew", pady=uniform_pady, ipady=uniform_ipady)
        # 占位符1 - 内容
        placeholder1_content = ttk.Label(
            stats_frame, 
            text="[行1内容]",
            font=("Microsoft YaHei UI", 9),
            bootstyle="secondary",
            anchor="w"
        )
        placeholder1_content.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=uniform_pady, ipady=uniform_ipady)
        
        # === 第1行：成功/失败统计 ===
        # 占位符2 - 标签
        placeholder2 = ttk.Label(
            stats_frame, 
            text="  [行2标签]",
            font=("Microsoft YaHei UI", 9),
            width=label_width,
            anchor="w"
        )
        placeholder2.grid(row=1, column=0, sticky="ew", pady=uniform_pady, ipady=uniform_ipady)
        # 占位符2 - 内容
        placeholder2_content = ttk.Label(
            stats_frame, 
            text="[行2内容]",
            font=("Microsoft YaHei UI", 9),
            bootstyle="secondary",
            anchor="w"
        )
        placeholder2_content.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=uniform_pady, ipady=uniform_ipady)
        
        # === 第2行：触发冷却 ===
        # 占位符3 - 标签
        placeholder3 = ttk.Label(
            stats_frame, 
            text="  [行3标签]",
            font=("Microsoft YaHei UI", 9),
            width=label_width,
            anchor="w"
        )
        placeholder3.grid(row=2, column=0, sticky="ew", pady=uniform_pady, ipady=uniform_ipady)
        # 占位符3 - 内容
        placeholder3_content = ttk.Label(
            stats_frame, 
            text="[行3内容]",
            font=("Microsoft YaHei UI", 9),
            bootstyle="success",
            anchor="w"
        )
        placeholder3_content.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=uniform_pady, ipady=uniform_ipady)
        
        # 占位符3 - 按钮（保持统一的间距参数，限制高度避免撑开行）
        placeholder3_button = ttk.Button(
            stats_frame, 
            text="[按钮]", 
            bootstyle="warning-outline",
            width=12
        )
        placeholder3_button.grid(row=2, column=2, sticky="w", padx=(15, 0), pady=uniform_pady, ipady=0)  # 按钮不使用ipady避免撑高
        
        # 保存引用以便后续替换
        self.placeholder_elements = {
            'sync_label': placeholder1,
            'sync_content': placeholder1_content,
            'stats_label': placeholder2, 
            'stats_content': placeholder2_content,
            'cooldown_label': placeholder3,
            'cooldown_content': placeholder3_content,
            'reset_button': placeholder3_button
        }
    
    def replace_placeholders_with_real_content(self):
        """将占位符替换为真实内容"""
        # 替换第0行：上次同步时间
        self.placeholder_elements['sync_label'].configure(
            text="  上次同步:",
            image=self.icons.get('sync'),
            compound="left"
        )
        self.placeholder_elements['sync_content'].configure(text="未执行")
        self.last_sync_label = self.placeholder_elements['sync_content']
        
        # 替换第1行：成功/失败统计
        self.placeholder_elements['stats_label'].configure(
            text="  成功/失败:",
            image=self.icons.get('stats'),
            compound="left"
        )
        self.placeholder_elements['stats_content'].configure(text="0 / 0")
        self.stats_label = self.placeholder_elements['stats_content']
        
        # 替换第2行：触发冷却
        self.placeholder_elements['cooldown_label'].configure(
            text="  触发冷却:",
            image=self.icons.get('cooldown'),
            compound="left"
        )
        self.placeholder_elements['cooldown_content'].configure(text="无冷却")
        self.cooldown_label = self.placeholder_elements['cooldown_content']
        
        # 替换按钮
        self.placeholder_elements['reset_button'].configure(
            text="重置",
            command=self.reset_global_cooldown
        )
        self.reset_cooldown_button = self.placeholder_elements['reset_button']

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
        
        # 现代化日志文本框 - 减少高度让界面更平衡
        self.log_text = tk.Text(
            log_container, 
            height=10,  
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
        self.log_message("🚀 现代化GUI界面v2.1已启动（性能优化版 - 完整功能）")
    
    # === 性能优化的线程管理 ===
    
    def start_idle_display_thread(self):
        """启动轻量级空闲时间显示线程"""
        def idle_display_loop():
            while True:
                try:
                    current_time = time.time()
                    
                    # 只有当需要更新时才执行
                    if current_time - self._last_idle_update_time >= self._idle_update_interval:
                        # 获取空闲时间（这个API很快，~1ms）
                        idle_seconds = self.idle_detector.get_idle_time_seconds()
                        idle_time_text = self.format_idle_time_seconds(int(idle_seconds))
                        
                        # 只有显示文本真正改变时才更新GUI
                        if idle_time_text != self._last_idle_display_text:
                            self.schedule_gui_update('idle_time', idle_time_text)
                            self._last_idle_display_text = idle_time_text
                        
                        self._last_idle_update_time = current_time
                    
                    # 较长的sleep间隔，减少CPU占用
                    time.sleep(0.5)  # 从0.1秒增加到0.5秒
                    
                except Exception as e:
                    if self._debug_enabled:
                        print(f"空闲时间显示出错: {e}")
                    time.sleep(2)
        
        thread = threading.Thread(target=idle_display_loop, daemon=True)
        thread.start()
    
    def start_app_status_thread(self):
        """启动优化的应用状态检查线程"""
        def app_status_loop():
            # 首次启动稍微延迟，让GUI完全加载
            time.sleep(2)
            
            while True:
                try:
                    current_time = time.time()
                    
                    # 检查是否需要更新状态（避免频繁API调用）
                    should_check_wechat = (current_time - self._last_wechat_check_time) >= self._app_status_check_interval
                    should_check_onedrive = (current_time - self._last_onedrive_check_time) >= self._app_status_check_interval
                    
                    if should_check_wechat or should_check_onedrive:
                        # 使用锁避免并发检查
                        with self._status_check_lock:
                            if self._status_check_in_progress:
                                continue
                            self._status_check_in_progress = True
                        
                        try:
                            if should_check_wechat:
                                self.check_wechat_status_optimized()
                                self._last_wechat_check_time = current_time
                            
                            if should_check_onedrive:
                                self.check_onedrive_status_optimized()
                                self._last_onedrive_check_time = current_time
                        finally:
                            self._status_check_in_progress = False
                    
                    # 更新其他状态信息
                    self.update_other_status_optimized()
                    
                    # 较长的sleep间隔
                    time.sleep(5)  # 从1秒增加到5秒
                    
                except Exception as e:
                    if self._debug_enabled:
                        print(f"应用状态检查出错: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=app_status_loop, daemon=True)
        thread.start()
    
    def check_wechat_status_optimized(self):
        """优化的微信状态检查"""
        try:
            # 执行检查（这可能比较慢）
            wechat_running = is_wechat_running()
            
            # 更新内部状态
            old_status = self._wechat_status
            self._wechat_status = wechat_running
            
            # 只有状态变化时才更新GUI
            if old_status != wechat_running:
                if wechat_running:
                    # 只有在状态改变为运行时才获取进程数（避免不必要的API调用）
                    try:
                        processes = find_wechat_processes()
                        wechat_text = f"运行中 ({len(processes)}个进程)"
                    except:
                        wechat_text = "运行中"
                    wechat_bootstyle = "success"
                    button_text = "停止微信"
                    button_bootstyle = "outline-danger"
                else:
                    wechat_text = "未运行"
                    wechat_bootstyle = "danger"
                    button_text = "启动微信"
                    button_bootstyle = "outline-success"
                
                # 批量调度GUI更新
                self.schedule_gui_update('wechat_status', {
                    'text': wechat_text,
                    'bootstyle': wechat_bootstyle
                })
                self.schedule_gui_update('wechat_button', {
                    'text': button_text,
                    'bootstyle': button_bootstyle,
                    'state': 'normal'
                })
                
        except Exception as e:
            if self._debug_enabled:
                print(f"检查微信状态出错: {e}")
    
    def check_onedrive_status_optimized(self):
        """优化的OneDrive状态检查"""
        try:
            # 执行检查（这可能比较慢）
            onedrive_running = is_onedrive_running()
            
            # 更新内部状态
            old_status = self._onedrive_status
            self._onedrive_status = onedrive_running
            
            # 只有状态变化时才更新GUI
            if old_status != onedrive_running:
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
                
                # 批量调度GUI更新
                self.schedule_gui_update('onedrive_status', {
                    'text': onedrive_text,
                    'bootstyle': onedrive_bootstyle
                })
                self.schedule_gui_update('onedrive_button', {
                    'text': button_text,
                    'bootstyle': button_bootstyle,
                    'state': 'normal'
                })
                
        except Exception as e:
            if self._debug_enabled:
                print(f"检查OneDrive状态出错: {e}")
    
    def schedule_gui_update(self, update_type, update_data):
        """优化的GUI更新调度（批量处理）"""
        try:
            # 将更新加入队列
            self._pending_updates[update_type] = update_data
            
            # 避免重复调度
            if not self._gui_update_pending:
                self._gui_update_pending = True
                # 稍微延迟批量处理（减少GUI更新频率）
                self.root.after(100, self.process_gui_updates)
        except Exception as e:
            if self._debug_enabled:
                print(f"调度GUI更新出错: {e}")
    
    def process_gui_updates(self):
        """批量处理GUI更新"""
        try:
            if not self._pending_updates:
                self._gui_update_pending = False
                return
            
            # 处理所有挂起的更新
            updates_to_process = self._pending_updates.copy()
            self._pending_updates.clear()
            
            for update_type, update_data in updates_to_process.items():
                try:
                    if update_type == 'idle_time':
                        self.idle_time_label.config(text=update_data)
                    elif update_type == 'wechat_status':
                        self.wechat_status_label.config(text=update_data['text'], bootstyle=update_data['bootstyle'])
                    elif update_type == 'wechat_button':
                        self.wechat_toggle_button.config(text=update_data['text'], bootstyle=update_data['bootstyle'], state=update_data['state'])
                    elif update_type == 'onedrive_status':
                        self.onedrive_status_label.config(text=update_data['text'], bootstyle=update_data['bootstyle'])
                    elif update_type == 'onedrive_button':
                        self.onedrive_toggle_button.config(text=update_data['text'], bootstyle=update_data['bootstyle'], state=update_data['state'])
                    elif update_type == 'sync_time':
                        self.last_sync_label.config(text=update_data)
                    elif update_type == 'stats':
                        self.stats_label.config(text=update_data)
                    elif update_type == 'cooldown':
                        self.cooldown_label.config(text=update_data['text'], bootstyle=update_data['bootstyle'])
                except Exception as e:
                    if self._debug_enabled:
                        print(f"处理{update_type}更新出错: {e}")
            
            self._gui_update_pending = False
            
        except Exception as e:
            if self._debug_enabled:
                print(f"批量处理GUI更新出错: {e}")
            self._gui_update_pending = False
    
    def update_other_status_optimized(self):
        """优化的其他状态更新"""
        try:
            # 更新同步时间（仅在时间变化时更新GUI）
            if self.last_sync_time:
                new_time_str = self.last_sync_time.strftime("%Y-%m-%d %H:%M:%S")
                if new_time_str != self._last_sync_time_str:
                    self.schedule_gui_update('sync_time', new_time_str)
                    self._last_sync_time_str = new_time_str
                    self.log_message(f"更新同步时间显示: {new_time_str}", "DEBUG")
            else:
                # 如果没有同步时间，显示未执行
                if self._last_sync_time_str != "未执行":
                    self.schedule_gui_update('sync_time', "未执行")
                    self._last_sync_time_str = "未执行"
            
            # 更新统计（仅在数值变化时更新GUI）
            new_stats_text = f"{self.sync_success_count} / {self.sync_error_count}"
            if new_stats_text != self._last_stats_text:
                self.schedule_gui_update('stats', new_stats_text)
                self._last_stats_text = new_stats_text
                self.log_message(f"更新统计显示: {new_stats_text}", "DEBUG")
            
            # 更新重置冷却按钮状态
            self.update_reset_cooldown_button_state()
            
        except Exception as e:
            if self._debug_enabled:
                print(f"更新其他状态出错: {e}")
    
    def update_cooldown_display_optimized(self):
        """简化的冷却时间显示更新（已弃用 - 现在由独立线程处理）"""
        # 这个函数现在基本不再被调用，因为冷却显示已经移到独立线程
        # 保留它只是为了兼容性，避免其他地方的调用出错
        pass
    
    def get_cooldown_display_text(self):
        """获取冷却显示文本（简化版，模仿静置时间格式化）"""
        # 检查是否有任何触发器启用
        idle_enabled = self.config.is_idle_trigger_enabled()
        scheduled_enabled = self.config.is_scheduled_trigger_enabled()
        
        if not idle_enabled and not scheduled_enabled:
            return "所有自动触发均未启用"
        
        # 检查全局冷却时间
        if not self.is_global_cooldown_active():
            triggers = []
            if idle_enabled:
                triggers.append("静置")
            if scheduled_enabled:
                triggers.append("定时")
            
            return f"无冷却（可以{'/'.join(triggers)}触发）"
        else:
            # 显示剩余全局冷却时间
            remaining_time = self.get_remaining_cooldown_minutes()
            remaining_minutes = int(remaining_time)
            
            if remaining_minutes > 0:
                # 只显示分钟，像静置时间一样简洁
                return f"全局冷却：{remaining_minutes}分钟"
            else:
                # 最后1分钟显示秒数（精确到秒）
                remaining_seconds = int((remaining_time - remaining_minutes) * 60)
                return f"全局冷却：{max(1, remaining_seconds)}秒"
    
    def get_cooldown_bootstyle(self):
        """获取冷却显示样式（缓存优化）"""
        if not self.is_global_cooldown_active():
            return "success"
        else:
            return "warning"

    def start_cooldown_timer(self):
        """启动轻量级冷却计时器线程（完全模仿静置时间显示）"""
        if self._cooldown_timer_running:
            return  # 已经在运行
        
        self._cooldown_timer_running = True
        
        def cooldown_timer_loop():
            """冷却计时器循环 - 完全模仿静置时间显示的简单结构"""
            while self._cooldown_timer_running:
                try:
                    current_time = time.time()
                    
                    # 只有当需要更新时才执行（和静置时间一样）
                    if current_time - self._last_cooldown_update_time >= self._cooldown_update_interval:
                        # 获取冷却显示文本（这个操作很快）
                        cooldown_text = self.get_cooldown_display_text()
                        
                        # 只有显示文本真正改变时才更新GUI（和静置时间一样）
                        if cooldown_text != self._last_cooldown_display_text:
                            # 获取对应的样式
                            bootstyle = self.get_cooldown_bootstyle()
                            self.schedule_gui_update('cooldown', {'text': cooldown_text, 'bootstyle': bootstyle})
                            self._last_cooldown_display_text = cooldown_text
                        
                        self._last_cooldown_update_time = current_time
                    
                    # 固定的sleep，和静置时间一样（没有复杂计算）
                    time.sleep(0.5)
                    
                except Exception as e:
                    if self._debug_enabled:
                        print(f"冷却时间显示出错: {e}")
                    time.sleep(2)
        
        self._cooldown_timer_thread = threading.Thread(target=cooldown_timer_loop, daemon=True)
        self._cooldown_timer_thread.start()
    
    def stop_cooldown_timer(self):
        """停止冷却计时器"""
        self._cooldown_timer_running = False
        self.log_message("[冷却计时器] 独立冷却计时器已停止", "DEBUG")
    
    # === 智能切换按钮功能（优化版） ===
    
    def toggle_wechat(self):
        """切换微信状态（优化版）"""
        if self._wechat_status is None:
            self.log_message("微信状态检查中，请稍候...", "WARNING")
            return
        
        # 立即禁用按钮，防止重复点击
        self.wechat_toggle_button.config(state="disabled", text="处理中...")
        
        def toggle_thread():
            try:
                if self._wechat_status:  # 当前运行中，需要停止
                    self.log_message("正在停止微信...")
                    success = stop_wechat()
                    if success:
                        self.log_message("微信已停止", "SUCCESS")
                    else:
                        self.log_message("停止微信失败", "ERROR")
                else:  # 当前未运行，需要启动
                    self.log_message("正在启动微信...")
                    success = start_wechat()
                    if success:
                        self.log_message("微信启动成功", "SUCCESS")
                    else:
                        self.log_message("微信启动失败", "ERROR")
                
                # 立即检查状态更新（但不频繁）
                time.sleep(1)  # 等待应用响应
                self.check_wechat_status_optimized()
                        
            except Exception as e:
                self.log_message(f"切换微信状态时出错: {e}", "ERROR")
                # 恢复按钮状态
                self.root.after(0, lambda: self.wechat_toggle_button.config(state="normal", text="查询中..."))
        
        # 在新线程中运行避免阻塞GUI
        thread = threading.Thread(target=toggle_thread, daemon=True)
        thread.start()
    
    def toggle_onedrive(self):
        """切换OneDrive状态（优化版）"""
        if self._onedrive_status is None:
            self.log_message("OneDrive状态检查中，请稍候...", "WARNING")
            return
        
        # 立即禁用按钮，防止重复点击
        self.onedrive_toggle_button.config(state="disabled", text="处理中...")
        
        def toggle_thread():
            try:
                if self._onedrive_status:  # 当前运行中，需要暂停
                    self.log_message("正在暂停OneDrive...")
                    success = pause_onedrive_sync()
                    if success:
                        self.log_message("OneDrive已暂停", "SUCCESS")
                    else:
                        self.log_message("暂停OneDrive失败", "ERROR")
                else:  # 当前未运行，需要启动
                    self.log_message("正在启动OneDrive...")
                    success = start_onedrive()
                    if success:
                        self.log_message("OneDrive启动成功", "SUCCESS")
                    else:
                        self.log_message("OneDrive启动失败", "ERROR")
                
                # 立即检查状态更新（但不频繁）
                time.sleep(1)  # 等待应用响应
                self.check_onedrive_status_optimized()
                        
            except Exception as e:
                self.log_message(f"切换OneDrive状态时出错: {e}", "ERROR")
                # 恢复按钮状态
                self.root.after(0, lambda: self.onedrive_toggle_button.config(state="normal", text="查询中..."))
        
        # 在新线程中运行避免阻塞GUI
        thread = threading.Thread(target=toggle_thread, daemon=True)
        thread.start()
    
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
    
    # === 其他功能保持不变（简化版本以避免过长） ===
    
    def show_config_dialog(self):
        """显示完整配置对话框"""
        import time
        start_time = time.time()
        self.log_message("🔍 [性能分析] 配置对话框开始创建", "DEBUG")
        # ⚡ 性能优化：一次性批量读取所有配置值，避免多次I/O操作
        try:
            current_config = self.config.config.copy()
            idle_config = current_config.get('idle_trigger', {})
            scheduled_config = current_config.get('scheduled_trigger', {})
            sync_config = current_config.get('sync_settings', {})
            logging_config = current_config.get('logging', {})
            gui_config = current_config.get('gui', {})
            config_load_time = time.time()
            self.log_message(f"🔍 [性能分析] 配置加载完成: {(config_load_time - start_time)*1000:.1f}ms", "DEBUG")
        except Exception as e:
            self.log_message(f"读取配置失败，使用默认值: {e}", "WARNING")
            # 使用默认配置
            idle_config = {'enabled': True, 'idle_minutes': 5, 'cooldown_minutes': 20}
            scheduled_config = {'enabled': False, 'time': '16:30', 'days': ['daily']}
            sync_config = {'wait_after_sync_minutes': 5, 'max_retry_attempts': 3}
            logging_config = {'enabled': True, 'level': 'info', 'max_log_files': 5}
            gui_config = {'close_behavior': 'exit', 'remember_close_choice': True}
            config_load_time = time.time()
        
        # 创建配置窗口
        config_window = ttk.Toplevel(self.root)
        config_window.title("完整配置设置")
        config_window.geometry("900x700")
        config_window.resizable(True, True)
        config_window.minsize(800, 650)
        
        # ⚡ 性能优化：延迟设置模态和grab_set到窗口完全创建后
        config_window.transient(self.root)
        
        window_create_time = time.time()
        self.log_message(f"🔍 [性能分析] 配置窗口创建完成: {(window_create_time - config_load_time)*1000:.1f}ms", "DEBUG")
        
        # ⚡ 性能优化：先显示窗口骨架，再填充内容
        # 主框架
        main_frame = ttk.Frame(config_window, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        config_window.columnconfigure(0, weight=1)
        config_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 创建标签页容器
        notebook = ttk.Notebook(main_frame, bootstyle="info")
        notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        
        # ⚡ 性能优化：完全延迟加载 - 先显示空窗口，然后异步创建内容
        def create_all_content_async():
            """异步创建所有配置内容"""
        
        # ⚡ 性能优化：先显示空的标签页，用户体验更好
        # 创建空白标签页
        trigger_frame = ttk.Frame(notebook, padding="20")
        notebook.add(trigger_frame, text="触发设置")
        
        sync_frame = ttk.Frame(notebook, padding="20") 
        notebook.add(sync_frame, text="同步设置")
        
        log_frame = ttk.Frame(notebook, padding="20")
        notebook.add(log_frame, text="日志设置")
        
        gui_frame = ttk.Frame(notebook, padding="20")
        notebook.add(gui_frame, text="界面设置")
        
        startup_frame = ttk.Frame(notebook, padding="20")
        notebook.add(startup_frame, text="启动设置")
        
        tabs_create_time = time.time()
        self.log_message(f"🔍 [性能分析] 标签页框架创建完成: {(tabs_create_time - window_create_time)*1000:.1f}ms", "DEBUG")
        
        # ⚡ 性能分析：使用类变量避免作用域问题
        self._click_start_time = None
        
        def on_button_press(event):
            """鼠标按下时记录开始时间"""
            self._click_start_time = time.time()
            # self.log_message(f"🔍 [性能分析] 检测到标签页点击", "DEBUG")
        
        def on_tab_change(event):
            """标签页切换事件 - 测量从点击到完成的总响应时间"""
            try:
                selected_tab = notebook.index(notebook.select())
                tab_names = ["触发设置", "同步设置", "日志设置", "界面设置", "启动设置"]
                tab_name = tab_names[selected_tab] if selected_tab < len(tab_names) else f"标签页{selected_tab}"
                
                # ⚡ 关键：等待界面完全更新后测量总时间
                def measure_total_response():
                    response_end = time.time()
                    if self._click_start_time:
                        # 从鼠标点击到界面更新完成的总时间
                        total_time = (response_end - self._click_start_time) * 1000
                        self.log_message(f"🔍 [性能分析] 点击到{tab_name}完成: {total_time:.1f}ms", "DEBUG")
                    else:
                        # 如果没有捕获到点击时间，只测量事件处理时间
                        self.log_message(f"🔍 [性能分析] {tab_name}切换完成 (无点击时间)", "DEBUG")
                    
                    self._click_start_time = None  # 重置
                
                # 在GUI空闲时测量（确保所有更新完成）
                config_window.after_idle(measure_total_response)
                
            except Exception as e:
                self.log_message(f"🔍 [性能分析] 标签页切换错误: {e}", "DEBUG")
        
        # 绑定鼠标点击和标签页切换事件
        notebook.bind('<Button-1>', on_button_press)  # 鼠标左键按下
        notebook.bind('<<NotebookTabChanged>>', on_tab_change)
        
        # 配置变量字典
        config_vars = {}
        
        # ⚡ 性能优化：先显示窗口，然后分步创建内容
        # 按钮区域（先创建按钮，让用户能够立即看到可操作界面）
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure(1, weight=1)
        
        # ⚡ 性能优化：先显示加载提示（使用grid与后面保持一致）
        loading_label = ttk.Label(trigger_frame, text="⏳ 正在加载配置选项...", 
                                 font=("Microsoft YaHei UI", 12), foreground="gray")
        loading_label.grid(row=0, column=0, pady=50, sticky="ew")
        
        # ⚡ 性能优化：移除立即布局计算，减少阻塞
        # config_window.update_idletasks()  # 注释掉以减少阻塞
        
        # ⚡ 关键优化：立即显示窗口，然后分批异步加载内容
        def create_content_progressively():
            """分批创建内容，避免UI阻塞"""
            try:
                content_start_time = time.time()
                loading_label.destroy()
                
                # 分批创建：第一批 - 触发设置页面
                def create_trigger_tab():
                    tab1_start = time.time()
                    self.create_trigger_tab_content(trigger_frame, config_vars, current_config)
                    tab1_time = (time.time() - tab1_start) * 1000
                    self.log_message(f"🔍 [性能分析] 触发设置页创建完成: {tab1_time:.1f}ms", "DEBUG")
                    
                    # 继续创建下一个标签页
                    config_window.after(10, create_sync_tab)
                
                def create_sync_tab():
                    tab2_start = time.time()
                    self.create_sync_tab_content(sync_frame, config_vars, current_config)
                    tab2_time = (time.time() - tab2_start) * 1000
                    self.log_message(f"🔍 [性能分析] 同步设置页创建完成: {tab2_time:.1f}ms", "DEBUG")
                    
                    config_window.after(10, create_log_tab)
                
                def create_log_tab():
                    tab3_start = time.time()
                    self.create_log_tab_content(log_frame, config_vars, current_config)
                    tab3_time = (time.time() - tab3_start) * 1000
                    self.log_message(f"🔍 [性能分析] 日志设置页创建完成: {tab3_time:.1f}ms", "DEBUG")
                    
                    config_window.after(10, create_gui_tab)
                
                def create_gui_tab():
                    tab4_start = time.time()
                    self.create_gui_tab_content(gui_frame, config_vars, current_config)
                    tab4_time = (time.time() - tab4_start) * 1000
                    self.log_message(f"🔍 [性能分析] 界面设置页创建完成: {tab4_time:.1f}ms", "DEBUG")
                    
                    config_window.after(10, create_startup_tab)
                
                def create_startup_tab():
                    tab5_start = time.time()
                    self.create_startup_tab_content(startup_frame, config_vars, current_config)
                    tab5_time = (time.time() - tab5_start) * 1000
                    self.log_message(f"🔍 [性能分析] 启动设置页创建完成: {tab5_time:.1f}ms", "DEBUG")
                    
                    config_window.after(10, lambda: create_buttons(config_vars))
                
                def create_buttons(config_vars):
                    button_start = time.time()
                    self.create_config_buttons(button_frame, config_window, config_vars, current_config)
                    button_time = (time.time() - button_start) * 1000
                    self.log_message(f"🔍 [性能分析] 按钮创建完成: {button_time:.1f}ms", "DEBUG")
                    
                    # 最终完成统计
                    total_content_time = (time.time() - content_start_time) * 1000
                    self.log_message(f"🔍 [性能分析] 所有内容异步创建完成: {total_content_time:.1f}ms", "DEBUG")
                
                # 开始创建第一个标签页
                create_trigger_tab()
                
            except Exception as e:
                self.log_message(f"🔍 [性能分析] 内容创建错误: {e}", "DEBUG")
        
        # 立即显示窗口框架，50ms后开始异步创建内容
        config_window.update()  # 立即显示窗口和加载提示
        config_window.after(50, create_content_progressively)
        
        # ⚡ 性能统计：窗口框架已经显示，剩余内容将异步加载
        framework_time = time.time()
        total_framework_time = (framework_time - start_time) * 1000
        self.log_message(f"🔍 [性能分析] 对话框框架完全就绪: {total_framework_time:.1f}ms", "DEBUG")
    
    def create_trigger_tab_content(self, trigger_frame, config_vars, current_config):
        """创建触发设置标签页内容"""
        trigger_frame.columnconfigure(0, weight=1)
        idle_config = current_config.get('idle_trigger', {})
        scheduled_config = current_config.get('scheduled_trigger', {})
        
        # 静置触发配置
        idle_frame = ttk.LabelFrame(trigger_frame, text="静置触发设置", padding="15")
        idle_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        idle_frame.columnconfigure(2, weight=1)
        
        config_vars['idle_enabled'] = tk.BooleanVar(value=idle_config.get('enabled', True))
        idle_check = ttk.Checkbutton(
            idle_frame, 
            text="启用静置触发", 
            variable=config_vars['idle_enabled'],
            bootstyle="round-toggle"
        )
        idle_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(idle_frame, text="静置时间(分钟):").grid(row=1, column=0, sticky=tk.W, pady=5)
        config_vars['idle_minutes'] = tk.StringVar(value=str(idle_config.get('idle_minutes', 5)))
        idle_spinbox = ttk.Spinbox(
            idle_frame, from_=1, to=120, width=10, 
            textvariable=config_vars['idle_minutes'], bootstyle="info"
        )
        idle_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(idle_frame, text="建议5-30分钟").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 定时触发配置
        scheduled_frame = ttk.LabelFrame(trigger_frame, text="定时触发设置", padding="15")
        scheduled_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        scheduled_frame.columnconfigure(2, weight=1)
        
        config_vars['scheduled_enabled'] = tk.BooleanVar(value=scheduled_config.get('enabled', False))
        scheduled_check = ttk.Checkbutton(
            scheduled_frame, 
            text="启用定时触发", 
            variable=config_vars['scheduled_enabled'],
            bootstyle="round-toggle"
        )
        scheduled_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(scheduled_frame, text="触发时间:").grid(row=1, column=0, sticky=tk.W, pady=5)
        config_vars['scheduled_time'] = tk.StringVar(value=scheduled_config.get('time', '13:05'))
        time_entry = ttk.Entry(
            scheduled_frame, width=15,
            textvariable=config_vars['scheduled_time']
        )
        time_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(scheduled_frame, text="格式: HH:MM (如 13:30)").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(scheduled_frame, text="执行日期:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # 星期几选择映射
        days_display_map = {
            'daily': '每天',
            'monday': '每周一',
            'tuesday': '每周二',
            'wednesday': '每周三',
            'thursday': '每周四',
            'friday': '每周五',
            'saturday': '每周六',
            'sunday': '每周日'
        }
        
        current_days = scheduled_config.get('days', ['daily'])
        current_day_value = current_days[0] if current_days else 'daily'
        current_day_display = days_display_map.get(current_day_value, '每天')
        
        config_vars['scheduled_days'] = tk.StringVar(value=current_day_display)
        days_combobox = ttk.Combobox(
            scheduled_frame, width=20,
            textvariable=config_vars['scheduled_days'],
            values=list(days_display_map.values()),
            state="readonly", bootstyle="info"
        )
        days_combobox.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(scheduled_frame, text="每天或指定星期").grid(row=2, column=2, sticky=tk.W, padx=(10, 0), pady=5)

    def create_sync_tab_content(self, sync_frame, config_vars, current_config):
        """创建同步设置标签页内容"""  
        sync_frame.columnconfigure(0, weight=1)
        sync_settings = current_config.get('sync_settings', {})
        idle_config = current_config.get('idle_trigger', {})
        
        sync_settings_frame = ttk.LabelFrame(sync_frame, text="同步行为设置", padding="15")
        sync_settings_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        sync_settings_frame.columnconfigure(2, weight=1)
        
        ttk.Label(sync_settings_frame, text="同步完成后等待时间(分钟):").grid(row=0, column=0, sticky=tk.W, pady=5)
        config_vars['wait_after_sync'] = tk.StringVar(value=str(sync_settings.get('wait_after_sync_minutes', 2)))
        wait_spinbox = ttk.Spinbox(
            sync_settings_frame, from_=1, to=60, width=10, 
            textvariable=config_vars['wait_after_sync'], bootstyle="info"
        )
        wait_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(sync_settings_frame, text="确保数据完整同步").grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(sync_settings_frame, text="最大重试次数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        config_vars['max_retry'] = tk.StringVar(value=str(sync_settings.get('max_retry_attempts', 3)))
        retry_spinbox = ttk.Spinbox(
            sync_settings_frame, from_=1, to=10, width=10, 
            textvariable=config_vars['max_retry'], bootstyle="info"
        )
        retry_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(sync_settings_frame, text="失败时重试次数").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 全局冷却时间设置
        cooldown_settings_frame = ttk.LabelFrame(sync_frame, text="全局冷却时间设置", padding="15")
        cooldown_settings_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        cooldown_settings_frame.columnconfigure(2, weight=1)
        
        ttk.Label(cooldown_settings_frame, text="冷却时间(分钟):").grid(row=0, column=0, sticky=tk.W, pady=5)
        config_vars['cooldown_minutes'] = tk.StringVar(value=str(idle_config.get('cooldown_minutes', 60)))
        cooldown_spinbox = ttk.Spinbox(
            cooldown_settings_frame, from_=1, to=480, width=10, 
            textvariable=config_vars['cooldown_minutes'], bootstyle="warning"
        )
        cooldown_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(cooldown_settings_frame, text="防止过于频繁同步").grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=5)

    def create_log_tab_content(self, log_frame, config_vars, current_config):
        """创建日志设置标签页内容"""
        log_frame.columnconfigure(0, weight=1)
        logging_config = current_config.get('logging', {})
        
        logging_frame = ttk.LabelFrame(log_frame, text="日志记录设置", padding="15")
        logging_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        logging_frame.columnconfigure(2, weight=1)
        
        config_vars['logging_enabled'] = tk.BooleanVar(value=logging_config.get('enabled', True))
        logging_check = ttk.Checkbutton(
            logging_frame, 
            text="启用日志记录", 
            variable=config_vars['logging_enabled'],
            bootstyle="round-toggle"
        )
        logging_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(logging_frame, text="日志级别:").grid(row=1, column=0, sticky=tk.W, pady=5)
        config_vars['log_level'] = tk.StringVar(value=logging_config.get('level', 'debug'))
        level_combobox = ttk.Combobox(
            logging_frame, width=15,
            textvariable=config_vars['log_level'],
            values=['debug', 'info', 'warning', 'error'],
            state="readonly", bootstyle="info"
        )
        level_combobox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(logging_frame, text="debug=详细信息, info=重要信息").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(logging_frame, text="保留日志文件数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        config_vars['max_log_files'] = tk.StringVar(value=str(logging_config.get('max_log_files', 5)))
        files_spinbox = ttk.Spinbox(
            logging_frame, from_=1, to=30, width=10, 
            textvariable=config_vars['max_log_files'], bootstyle="info"
        )
        files_spinbox.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(logging_frame, text="自动删除旧日志").grid(row=2, column=2, sticky=tk.W, padx=(10, 0), pady=5)

    def create_gui_tab_content(self, gui_frame, config_vars, current_config):
        """创建界面设置标签页内容"""
        gui_frame.columnconfigure(0, weight=1)
        gui_config = current_config.get('gui', {})
        
        gui_settings_frame = ttk.LabelFrame(gui_frame, text="图形界面设置", padding="15")
        gui_settings_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        gui_settings_frame.columnconfigure(2, weight=1)
        
        ttk.Label(gui_settings_frame, text="关闭行为:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 关闭行为选择映射
        close_behavior_display_map = {
            'ask': '询问用户',
            'minimize': '最小化到托盘',
            'exit': '直接退出'
        }
        
        current_close_behavior = gui_config.get('close_behavior', 'exit')
        current_close_display = close_behavior_display_map.get(current_close_behavior, '直接退出')
        
        config_vars['close_behavior'] = tk.StringVar(value=current_close_display)
        close_combobox = ttk.Combobox(
            gui_settings_frame, width=15,
            textvariable=config_vars['close_behavior'],
            values=list(close_behavior_display_map.values()),
            state="readonly", bootstyle="info"
        )
        close_combobox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(gui_settings_frame, text="点击X按钮时的行为").grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        config_vars['remember_close'] = tk.BooleanVar(value=gui_config.get('remember_close_choice', False))
        remember_check = ttk.Checkbutton(
            gui_settings_frame, 
            text="记住关闭方式选择", 
            variable=config_vars['remember_close'],
            bootstyle="round-toggle"
        )
        remember_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)

    def create_startup_tab_content(self, startup_frame, config_vars, current_config):
        """创建启动设置标签页内容"""
        startup_frame.columnconfigure(0, weight=1)
        startup_config = current_config.get('startup', {})
        
        startup_settings_frame = ttk.LabelFrame(startup_frame, text="程序启动设置", padding="15")
        startup_settings_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        startup_settings_frame.columnconfigure(2, weight=1)
        
        config_vars['auto_start'] = tk.BooleanVar(value=startup_config.get('auto_start_service', False))
        auto_start_check = ttk.Checkbutton(
            startup_settings_frame, 
            text="开机自动启动监控服务", 
            variable=config_vars['auto_start'],
            bootstyle="round-toggle"
        )
        auto_start_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        config_vars['minimize_tray'] = tk.BooleanVar(value=startup_config.get('minimize_to_tray', True))
        minimize_check = ttk.Checkbutton(
            startup_settings_frame, 
            text="启动时最小化到系统托盘", 
            variable=config_vars['minimize_tray'],
            bootstyle="round-toggle"
        )
        minimize_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)

    def create_config_buttons(self, button_frame, config_window, config_vars, current_config):
        """创建配置按钮"""
        def save_all_config():
            try:
                # 映射显示值回英文值
                days_value_map = {
                    '每天': 'daily', '每周一': 'monday', '每周二': 'tuesday', '每周三': 'wednesday',
                    '每周四': 'thursday', '每周五': 'friday', '每周六': 'saturday', '每周日': 'sunday'
                }
                close_behavior_value_map = {
                    '询问用户': 'ask', '最小化到托盘': 'minimize', '直接退出': 'exit'
                }
                
                # 配置更新字典
                config_updates = {
                    'idle_trigger': {
                        'enabled': config_vars['idle_enabled'].get(),
                        'idle_minutes': int(config_vars['idle_minutes'].get()),
                        'cooldown_minutes': int(config_vars['cooldown_minutes'].get())
                    },
                    'scheduled_trigger': {
                        'enabled': config_vars['scheduled_enabled'].get(),
                        'time': config_vars['scheduled_time'].get(),
                        'days': [days_value_map.get(config_vars['scheduled_days'].get(), 'daily')]
                    },
                    'sync_settings': {
                        'wait_after_sync_minutes': int(config_vars['wait_after_sync'].get()),
                        'max_retry_attempts': int(config_vars['max_retry'].get())
                    },
                    'logging': {
                        'enabled': config_vars['logging_enabled'].get(),
                        'level': config_vars['log_level'].get(),
                        'max_log_files': int(config_vars['max_log_files'].get())
                    },
                    'gui': {
                        'close_behavior': close_behavior_value_map.get(config_vars['close_behavior'].get(), 'exit'),
                        'remember_close_choice': config_vars['remember_close'].get()
                    },
                    'startup': {
                        'auto_start_service': config_vars['auto_start'].get(),
                        'minimize_to_tray': config_vars['minimize_tray'].get()
                    }
                }
                
                # 立即关闭窗口，提供即时反馈
                config_window.destroy()
                self.log_message("正在保存配置...", "INFO")
                
                # 后台保存操作
                def save_in_background():
                    try:
                        # 高效配置更新
                        for section, updates in config_updates.items():
                            if section not in self.config.config:
                                self.config.config[section] = {}
                            self.config.config[section].update(updates)
                        
                        success = self.config.save_config(self.config.config)
                        
                        if success:
                            self.log_message("完整配置已保存成功", "SUCCESS")
                        else:
                            self.log_message("保存配置失败", "ERROR")
                            
                    except Exception as e:
                        self.log_message(f"保存配置时出错: {e}", "ERROR")
                
                import threading
                threading.Thread(target=save_in_background, daemon=True).start()
                
            except ValueError as e:
                self.log_message(f"请输入有效的数字：{e}", "ERROR")
            except Exception as e:
                self.log_message(f"配置验证失败: {e}", "ERROR")
        
        def reset_to_defaults():
            import tkinter.messagebox as messagebox
            result = messagebox.askyesno("确认重置", "确定要重置所有设置为默认值吗？")
            if result:
                try:
                    # 重置为默认值
                    config_vars['idle_enabled'].set(True)
                    config_vars['idle_minutes'].set('1')
                    config_vars['cooldown_minutes'].set('60')
                    config_vars['scheduled_enabled'].set(False)
                    config_vars['scheduled_time'].set('13:05')
                    config_vars['scheduled_days'].set('每天')
                    config_vars['wait_after_sync'].set('1')
                    config_vars['max_retry'].set('3')
                    config_vars['logging_enabled'].set(True)
                    config_vars['log_level'].set('debug')
                    config_vars['max_log_files'].set('5')
                    config_vars['close_behavior'].set('直接退出')
                    config_vars['remember_close'].set(False)
                    config_vars['auto_start'].set(False)
                    config_vars['minimize_tray'].set(True)
                    
                    messagebox.showinfo("重置完成", "所有设置已重置为默认值，请点击保存配置使更改生效。")
                except Exception as e:
                    messagebox.showerror("错误", f"重置配置时出错: {e}")
        
        ttk.Button(
            button_frame, 
            text="重置为默认值", 
            command=reset_to_defaults,
            bootstyle="outline-warning",
            width=15
        ).grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="保存配置", 
            command=save_all_config,
            bootstyle="success",
            width=15
        ).grid(row=0, column=2, padx=(10, 10))
        
        ttk.Button(
            button_frame, 
            text="取消", 
            command=config_window.destroy,
            bootstyle="outline-secondary",
            width=15
        ).grid(row=0, column=3)

    # === 其他必需方法的简化版本 ===
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        pass  # 菜单功能暂时禁用
        
    def apply_gui_updates(self):
            scheduled_frame, 
            text="启用定时触发", 
            variable=config_vars['scheduled_enabled'],
            bootstyle="round-toggle"
        )
        scheduled_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(scheduled_frame, text="触发时间:").grid(row=1, column=0, sticky=tk.W, pady=5)
        config_vars['scheduled_time'] = tk.StringVar(value=scheduled_config.get('time', '16:30'))
        time_entry = ttk.Entry(
            scheduled_frame, width=15, 
            textvariable=config_vars['scheduled_time'], bootstyle="info"
        )
        time_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(scheduled_frame, text="格式: HH:MM (如 13:30)").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(scheduled_frame, text="执行日期:").grid(row=2, column=0, sticky=tk.W, pady=5)
        # 星期几显示映射（中文显示，英文保存）
        days_display_map = {
            'daily': '每天',
            'monday': '每周一',
            'tuesday': '每周二', 
            'wednesday': '每周三',
            'thursday': '每周四',
            'friday': '每周五',
            'saturday': '每周六',
            'sunday': '每周日'
        }
        days_value_map = {v: k for k, v in days_display_map.items()}  # 反向映射
        
        days_config = self.config.config.get('scheduled_trigger', {}).get('days', ['daily'])
        current_day_value = 'daily' if 'daily' in days_config else ','.join(days_config)
        current_day_display = days_display_map.get(current_day_value, '每天')
        
        config_vars['scheduled_days'] = tk.StringVar(value=current_day_display)
        days_combobox = ttk.Combobox(
            scheduled_frame, width=20,
            textvariable=config_vars['scheduled_days'],
            values=list(days_display_map.values()),
            bootstyle="info", state="readonly"
        )
        days_combobox.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(scheduled_frame, text="每天或指定星期").grid(row=2, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # === 标签页2: 同步设置 ===
        sync_frame.columnconfigure(0, weight=1)
        
        sync_settings_frame = ttk.LabelFrame(sync_frame, text="同步行为设置", padding="15")
        sync_settings_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        sync_settings_frame.columnconfigure(2, weight=1)
        
        ttk.Label(sync_settings_frame, text="OneDrive同步后等待时间(分钟):").grid(row=0, column=0, sticky=tk.W, pady=5)
        config_vars['wait_after_sync'] = tk.StringVar(value=str(self.config.config.get('sync_settings', {}).get('wait_after_sync_minutes', 1)))
        wait_spinbox = ttk.Spinbox(
            sync_settings_frame, from_=1, to=60, width=10,
            textvariable=config_vars['wait_after_sync'], bootstyle="info"
        )
        wait_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(sync_settings_frame, text="确保同步完成").grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(sync_settings_frame, text="最大重试次数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        config_vars['max_retry'] = tk.StringVar(value=str(self.config.config.get('sync_settings', {}).get('max_retry_attempts', 3)))
        retry_spinbox = ttk.Spinbox(
            sync_settings_frame, from_=1, to=10, width=10,
            textvariable=config_vars['max_retry'], bootstyle="info"
        )
        retry_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(sync_settings_frame, text="失败时重试次数").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 全局冷却时间设置
        cooldown_settings_frame = ttk.LabelFrame(sync_frame, text="全局冷却时间设置", padding="15")
        cooldown_settings_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        cooldown_settings_frame.columnconfigure(2, weight=1)
        
        ttk.Label(cooldown_settings_frame, text="全局冷却时间(分钟):").grid(row=0, column=0, sticky=tk.W, pady=5)
        config_vars['cooldown_minutes'] = tk.StringVar(value=str(self.config.config.get('idle_trigger', {}).get('cooldown_minutes', 60)))
        cooldown_spinbox = ttk.Spinbox(
            cooldown_settings_frame, from_=5, to=300, width=10,
            textvariable=config_vars['cooldown_minutes'], bootstyle="info"
        )
        cooldown_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(cooldown_settings_frame, text="所有触发类型共享的冷却时间").grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(cooldown_settings_frame, text="说明: 无论手动、静置还是定时触发同步，执行后都会进入冷却期，", 
                 font=("Microsoft YaHei", 9), foreground="gray").grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        ttk.Label(cooldown_settings_frame, text="      冷却期间不会自动触发同步，但手动触发仍然可用。", 
                 font=("Microsoft YaHei", 9), foreground="gray").grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(0, 0))
        
        # === 标签页3: 日志设置 ===
        log_frame.columnconfigure(0, weight=1)
        
        logging_frame = ttk.LabelFrame(log_frame, text="日志记录设置", padding="15")
        logging_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        logging_frame.columnconfigure(2, weight=1)
        
        config_vars['logging_enabled'] = tk.BooleanVar(value=self.config.config.get('logging', {}).get('enabled', True))
        log_check = ttk.Checkbutton(
            logging_frame, 
            text="启用日志记录", 
            variable=config_vars['logging_enabled'],
            bootstyle="round-toggle"
        )
        log_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(logging_frame, text="日志级别:").grid(row=1, column=0, sticky=tk.W, pady=5)
        config_vars['log_level'] = tk.StringVar(value=self.config.config.get('logging', {}).get('level', 'debug'))
        level_combobox = ttk.Combobox(
            logging_frame, width=15,
            textvariable=config_vars['log_level'],
            values=['debug', 'info', 'warning', 'error'],
            bootstyle="info", state="readonly"
        )
        level_combobox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(logging_frame, text="详细程度控制").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(logging_frame, text="最大日志文件数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        config_vars['max_log_files'] = tk.StringVar(value=str(self.config.config.get('logging', {}).get('max_log_files', 5)))
        log_files_spinbox = ttk.Spinbox(
            logging_frame, from_=1, to=20, width=10,
            textvariable=config_vars['max_log_files'], bootstyle="info"
        )
        log_files_spinbox.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(logging_frame, text="自动清理旧日志").grid(row=2, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # === 标签页4: GUI设置 ===
        gui_frame.columnconfigure(0, weight=1)
        
        gui_settings_frame = ttk.LabelFrame(gui_frame, text="图形界面设置", padding="15")
        gui_settings_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        gui_settings_frame.columnconfigure(2, weight=1)
        
        ttk.Label(gui_settings_frame, text="关闭行为:").grid(row=0, column=0, sticky=tk.W, pady=5)
        # 关闭行为显示映射（中文显示，英文保存）
        close_behavior_display_map = {
            'ask': '询问用户',
            'minimize': '最小化到托盘',
            'exit': '直接退出'
        }
        close_behavior_value_map = {v: k for k, v in close_behavior_display_map.items()}  # 反向映射
        
        current_close_behavior = self.config.config.get('gui', {}).get('close_behavior', 'exit')
        current_close_display = close_behavior_display_map.get(current_close_behavior, '直接退出')
        
        config_vars['close_behavior'] = tk.StringVar(value=current_close_display)
        close_combobox = ttk.Combobox(
            gui_settings_frame, width=15,
            textvariable=config_vars['close_behavior'],
            values=list(close_behavior_display_map.values()),
            bootstyle="info", state="readonly"
        )
        close_combobox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(gui_settings_frame, text="询问/最小化/直接退出").grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        config_vars['remember_close'] = tk.BooleanVar(value=self.config.config.get('gui', {}).get('remember_close_choice', False))
        remember_check = ttk.Checkbutton(
            gui_settings_frame, 
            text="记住关闭方式选择", 
            variable=config_vars['remember_close'],
            bootstyle="round-toggle"
        )
        remember_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # === 标签页5: 启动设置 ===
        startup_frame.columnconfigure(0, weight=1)
        
        startup_settings_frame = ttk.LabelFrame(startup_frame, text="程序启动设置", padding="15")
        startup_settings_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        startup_settings_frame.columnconfigure(2, weight=1)
        
        config_vars['auto_start'] = tk.BooleanVar(value=self.config.config.get('startup', {}).get('auto_start_service', False))
        auto_start_check = ttk.Checkbutton(
            startup_settings_frame, 
            text="开机自动启动监控服务", 
            variable=config_vars['auto_start'],
            bootstyle="round-toggle"
        )
        auto_start_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        ttk.Label(startup_settings_frame, text="(未来功能)", font=("Microsoft YaHei", 8)).grid(row=0, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        
        config_vars['minimize_tray'] = tk.BooleanVar(value=self.config.config.get('startup', {}).get('minimize_to_tray', True))
        minimize_check = ttk.Checkbutton(
            startup_settings_frame, 
            text="启动时最小化到系统托盘", 
            variable=config_vars['minimize_tray'],
            bootstyle="round-toggle"
        )
        minimize_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        ttk.Label(startup_settings_frame, text="(未来功能)", font=("Microsoft YaHei", 8)).grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=5)
        
        
        def save_all_config():
            try:
                # Validate input values first (fast validation before closing dialog)
                int(config_vars['idle_minutes'].get())
                int(config_vars['cooldown_minutes'].get())
                int(config_vars['wait_after_sync'].get())
                int(config_vars['max_retry'].get())
                int(config_vars['max_log_files'].get())
                
                # Extract all values while UI is still responsive
                # 转换显示值为实际值
                scheduled_days_display = config_vars['scheduled_days'].get()
                scheduled_days_value = days_value_map.get(scheduled_days_display, 'daily')
                
                close_behavior_display = config_vars['close_behavior'].get()
                close_behavior_value = close_behavior_value_map.get(close_behavior_display, 'exit')
                
                config_updates = {
                    'idle_trigger': {
                        'enabled': config_vars['idle_enabled'].get(),
                        'idle_minutes': int(config_vars['idle_minutes'].get()),
                        'cooldown_minutes': int(config_vars['cooldown_minutes'].get())
                    },
                    'scheduled_trigger': {
                        'enabled': config_vars['scheduled_enabled'].get(),
                        'time': config_vars['scheduled_time'].get(),
                        'days': ['daily'] if scheduled_days_value == 'daily' 
                               else [scheduled_days_value]
                    },
                    'sync_settings': {
                        'wait_after_sync_minutes': int(config_vars['wait_after_sync'].get()),
                        'max_retry_attempts': int(config_vars['max_retry'].get())
                    },
                    'logging': {
                        'enabled': config_vars['logging_enabled'].get(),
                        'level': config_vars['log_level'].get(),
                        'max_log_files': int(config_vars['max_log_files'].get())
                    },
                    'gui': {
                        'close_behavior': close_behavior_value,
                        'remember_close_choice': config_vars['remember_close'].get()
                    },
                    'startup': {
                        'auto_start_service': config_vars['auto_start'].get(),
                        'minimize_to_tray': config_vars['minimize_tray'].get()
                    }
                }
                
                # Close dialog immediately for responsive UI
                config_window.destroy()
                
                # Show immediate feedback
                self.log_message("正在保存配置...", "INFO")
                
                # Background save operation
                def save_in_background():
                    try:
                        # Efficient config update without full copy
                        for section, updates in config_updates.items():
                            if section not in self.config.config:
                                self.config.config[section] = {}
                            self.config.config[section].update(updates)
                        
                        # Asynchronous save
                        success = self.config.save_config(self.config.config)
                        
                        # Non-blocking log messages instead of messageboxes
                        if success:
                            self.log_message("完整配置已保存成功", "SUCCESS")
                        else:
                            self.log_message("保存配置失败", "ERROR")
                            
                    except Exception as e:
                        self.log_message(f"保存配置时出错: {e}", "ERROR")
                
                # Start background thread
                threading.Thread(target=save_in_background, daemon=True).start()
                
            except ValueError as e:
                # Only show error dialog for validation failures before closing
                self.log_message(f"请输入有效的数字：{e}", "ERROR")
                # Don't close dialog on validation error, let user fix it
            except Exception as e:
                self.log_message(f"配置验证失败: {e}", "ERROR")
        
        def reset_to_defaults():
            result = messagebox.askyesno("确认重置", "确定要重置所有设置为默认值吗？")
            if result:
                try:
                    # 重置为默认值
                    config_vars['idle_enabled'].set(True)
                    config_vars['idle_minutes'].set('1')
                    config_vars['cooldown_minutes'].set('60')
                    config_vars['scheduled_enabled'].set(False)
                    config_vars['scheduled_time'].set('13:05')
                    config_vars['scheduled_days'].set('daily')
                    config_vars['wait_after_sync'].set('1')
                    config_vars['max_retry'].set('3')
                    config_vars['logging_enabled'].set(True)
                    config_vars['log_level'].set('debug')
                    config_vars['max_log_files'].set('5')
                    config_vars['close_behavior'].set('exit')
                    config_vars['remember_close'].set(False)
                    config_vars['auto_start'].set(False)
                    config_vars['minimize_tray'].set(True)
                    
                    messagebox.showinfo("重置完成", "所有设置已重置为默认值，请点击保存配置使更改生效。")
                except Exception as e:
                    messagebox.showerror("错误", f"重置配置时出错: {e}")
        
        ttk.Button(
            button_frame, 
            text="重置为默认值", 
            command=reset_to_defaults,
            bootstyle="outline-warning",
            width=15
        ).grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="保存配置", 
            command=save_all_config,
            bootstyle="success",
            width=15
        ).grid(row=0, column=2, padx=(10, 10))
        
        ttk.Button(
            button_frame, 
            text="取消", 
            command=config_window.destroy,
            bootstyle="outline-secondary",
            width=15
        ).grid(row=0, column=3)
        
        # ⚡ 性能优化：简化窗口居中，避免强制布局计算
        # 使用预估尺寸进行居中，避免 update_idletasks() 的性能开销
        screen_width = config_window.winfo_screenwidth()
        screen_height = config_window.winfo_screenheight()
        # 使用配置中的尺寸 (900x700) 进行居中计算
        x = (screen_width - 900) // 2
        y = (screen_height - 700) // 2
        config_window.geometry(f"+{x}+{y}")
        
        # ⚡ 性能优化：延迟设置模态抓取，直到窗口显示
        def finalize_dialog():
            config_window.grab_set()
        
        # ⚡ 性能优化：移除重复的加载指示器代码
        config_window.after(1, finalize_dialog)  # 延迟1ms执行，让窗口先显示
        
        # ⚡ 异步加载完成后的性能统计将在各个标签页创建完成时记录

    # === 其他必需方法的简化版本 ===
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.quit_application)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="切换调试模式", command=self.toggle_debug_mode)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def toggle_debug_mode(self):
        """切换调试模式"""
        self._debug_enabled = not self._debug_enabled
        status = "启用" if self._debug_enabled else "禁用"
        self.log_message(f"[调试] 调试模式已{status}", "INFO")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """微信OneDrive冲突解决工具 v2.1

这是一个自动化工具，用于解决微信Windows端与OneDrive同步冲突的问题。

v2.1 性能优化特性：
• 优化线程管理，减少卡顿
• 智能状态缓存机制
• 批量GUI更新处理
• 减少API调用频率
• 线程安全的状态检查

开发：Python + tkinter + ttkbootstrap
版本：v2.1 (性能优化版)"""
        
        messagebox.showinfo("关于", about_text)
    
    def start_auto_monitor_thread(self):
        """启动自动监控线程"""
        def monitor_loop():
            last_trigger_time = None
            sync_running_message_shown = False  # 避免重复显示"同步正在运行"消息
            cooldown_message_shown = False  # 避免重复显示"冷却中"消息
            if self._debug_enabled:
                self.log_message("[监控线程] 自动监控线程已启动，每秒检查静置状态", "DEBUG")
            
            while True:
                try:
                    # 检查静置触发是否启用
                    if not self.config.is_idle_trigger_enabled():
                        if self._debug_enabled:
                            self.log_message("[监控线程] 静置触发未启用，等待30秒", "DEBUG")
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
                        self.log_message(f"[监控线程] 监控检查: 空闲{idle_seconds:.1f}s, 阈值{idle_threshold}s", "DEBUG")
                    
                    # 检查是否满足触发条件
                    
                    # 检查是否达到空闲时间阈值
                    if idle_seconds >= idle_threshold:
                        if self._debug_enabled:
                            self.log_message(f"[监控线程] 达到触发条件！空闲时间{idle_seconds:.1f}s >= 阈值{idle_threshold}s", "DEBUG")
                        # 检查全局冷却时间
                        if not self.is_global_cooldown_active():
                            # 检查是否已经在运行同步
                            if not self.is_running_sync:
                                # 执行空闲同步
                                self.log_message(f"执行空闲同步（空闲{idle_minutes}分钟）", "INFO")
                                # 触发自动同步
                                # 在新线程中执行同步，避免阻塞监控线程
                                def auto_sync():
                                    try:
                                        self.is_running_sync = True
                                        self.root.after(0, lambda: self.sync_button.config(text="自动同步中...", state="disabled"))
                                        # 日志消息已在上面根据pending状态记录
                                        
                                        # 冷却时间将在同步成功完成后更新
                                        
                                        # 更新托盘图标状态
                                        if self.system_tray:
                                            self.system_tray.update_icon_status("running")
                                        
                                        # 执行同步流程
                                        success = sync_workflow.run_full_sync_workflow_gui(self.log_message)
                                        
                                        self.last_sync_time = datetime.now()
                                        if success:
                                            self.sync_success_count += 1
                                            self.log_message("自动同步流程执行成功", "SUCCESS")
                                            
                                            # 同步成功后更新全局冷却时间
                                            self.update_global_trigger_time()
                                            
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
                                        
                                        # 立即更新GUI状态显示
                                        self.update_other_status_optimized()
                                                
                                    except Exception as e:
                                        self.sync_error_count += 1
                                        self.log_message(f"自动同步流程异常: {e}", "ERROR")
                                        
                                        # 更新托盘图标状态
                                        if self.system_tray:
                                            self.system_tray.update_icon_status("error")
                                            self.system_tray.show_notification("自动同步异常", f"自动同步流程发生异常: {e}")
                                        
                                        # 更新GUI状态显示
                                        self.update_other_status_optimized()
                                    finally:
                                        self.is_running_sync = False
                                        self.root.after(0, lambda: self.sync_button.config(text="🚀 立即执行同步流程", state="normal"))
                                        
                                        # 恢复托盘图标到正常状态
                                        if self.system_tray:
                                            self.system_tray.update_icon_status("normal")
                                
                                # 启动自动同步线程
                                sync_thread = threading.Thread(target=auto_sync, daemon=True)
                                sync_thread.start()
                                
                                # 更新静置触发时间
                                self.last_idle_trigger_time = datetime.now()
                                sync_running_message_shown = False  # 重置标志，允许下次显示运行中消息
                                cooldown_message_shown = False  # 重置标志，允许下次显示冷却消息
                            else:
                                # 只在第一次检测到同步正在运行时显示消息，避免重复打印
                                if not sync_running_message_shown:
                                    self.log_message("检测到空闲触发条件，但同步流程已在运行中", "INFO")
                                    sync_running_message_shown = True
                        else:
                            # 全局冷却时间未到，忽略触发
                            if not cooldown_message_shown:
                                remaining_time = self.get_remaining_cooldown_minutes()
                                self.log_message(f"静置触发条件已满足（空闲{idle_minutes}分钟），但全局冷却未到，剩余{remaining_time:.1f}分钟", "INFO")
                                cooldown_message_shown = True
                            
                            if self._debug_enabled:
                                remaining_time = self.get_remaining_cooldown_minutes()
                                self.log_message(f"[监控线程] 全局冷却时间未到，剩余{remaining_time:.1f}分钟", "DEBUG")
                            sync_running_message_shown = False
                    else:
                        # 空闲时间不足，重置所有标志
                        sync_running_message_shown = False
                        cooldown_message_shown = False
                        # 用户有活动，重置标志
                        pass
                    
                    # 每1秒检查一次（接近实时响应，资源消耗极小~0.06ms/秒）
                    time.sleep(1)
                    
                except Exception as e:
                    if self._debug_enabled:
                        print(f"自动监控线程出错: {e}")
                    time.sleep(60)  # 出错时等待1分钟
        
        # 启动相关监控线程
        threads_started = []
        
        if self.config.is_idle_trigger_enabled():
            idle_thread = threading.Thread(target=monitor_loop, daemon=True)
            idle_thread.start()
            threads_started.append("静置触发")
        
        if self.config.is_scheduled_trigger_enabled():
            scheduled_thread = threading.Thread(target=self.start_scheduled_monitor, daemon=True)
            scheduled_thread.start()
            threads_started.append("定时触发")
        
        if threads_started:
            self.log_message(f"监控线程已启动: {', '.join(threads_started)}", "INFO")
        else:
            self.log_message("所有触发器均未启用，监控线程未启动", "INFO")
    
    def start_scheduled_monitor(self):
        """启动定时触发监控"""
        import time
        from datetime import datetime, time as dt_time
        
        self.log_message("定时触发监控线程已启动", "INFO")
        
        while True:
            try:
                # 检查定时触发是否仍然启用
                if not self.config.is_scheduled_trigger_enabled():
                    self.log_message("定时触发已被禁用，监控线程退出", "INFO")
                    break
                
                # 获取当前时间和配置的触发时间
                current_time = datetime.now()
                current_weekday = current_time.strftime('%A').lower()  # monday, tuesday等
                
                trigger_time_str = self.config.get_scheduled_time()  # 如 "15:20"
                trigger_days = self.config.config.get('scheduled_trigger', {}).get('days', ['daily'])
                
                # 解析触发时间
                try:
                    hour, minute = map(int, trigger_time_str.split(':'))
                    trigger_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                except (ValueError, AttributeError):
                    self.log_message(f"定时触发时间格式错误: {trigger_time_str}", "ERROR")
                    time.sleep(300)  # 等待5分钟后重试
                    continue
                
                # 检查是否需要触发
                should_trigger = False
                
                if 'daily' in trigger_days:
                    # 每天都触发
                    should_trigger = True
                elif current_weekday in trigger_days:
                    # 指定星期几触发
                    should_trigger = True
                
                if should_trigger:
                    # 检查时间是否匹配（允许1分钟误差）
                    time_diff = abs((current_time - trigger_time).total_seconds())
                    if time_diff <= 60:  # 1分钟内
                        # 检查全局冷却时间
                        if not self.is_global_cooldown_active():
                            # 检查是否已经在运行同步
                            if not self.is_running_sync:
                                self.log_message(f"定时触发: {trigger_time_str}", "INFO")
                                
                                # 执行定时同步
                                def scheduled_sync():
                                    try:
                                        self.is_running_sync = True
                                        self.root.after(0, lambda: self.sync_button.config(text="定时同步中...", state="disabled"))
                                        self.log_message("开始执行定时同步流程", "INFO")
                                        
                                        # 冷却时间将在同步成功完成后更新
                                        
                                        # 更新托盘图标状态
                                        if self.system_tray:
                                            self.system_tray.update_icon_status("running")
                                        
                                        # 执行同步流程
                                        success = sync_workflow.run_full_sync_workflow_gui(self.log_message)
                                        
                                        self.last_sync_time = datetime.now()
                                        if success:
                                            self.sync_success_count += 1
                                            self.log_message("定时同步流程执行成功", "SUCCESS")
                                            
                                            # 同步成功后更新全局冷却时间
                                            self.update_global_trigger_time()
                                            
                                            # 更新托盘图标和通知
                                            if self.system_tray:
                                                self.system_tray.update_icon_status("success")
                                                self.system_tray.show_notification("定时同步完成", "定时同步任务已成功完成")
                                        else:
                                            self.sync_error_count += 1
                                            self.log_message("定时同步流程执行失败", "ERROR")
                                            
                                            # 更新托盘图标和通知
                                            if self.system_tray:
                                                self.system_tray.update_icon_status("error")
                                                self.system_tray.show_notification("定时同步失败", "定时同步任务执行失败，请查看日志")
                                        
                                        # 立即更新GUI状态显示
                                        self.update_other_status_optimized()

                                    except Exception as e:
                                        self.sync_error_count += 1
                                        self.log_message(f"定时同步流程异常: {e}", "ERROR")
                                        
                                        # 更新托盘图标状态
                                        if self.system_tray:
                                            self.system_tray.update_icon_status("error")
                                            self.system_tray.show_notification("定时同步异常", f"定时同步流程发生异常: {e}")
                                        
                                        # 更新GUI状态显示
                                        self.update_other_status_optimized()
                                    finally:
                                        self.is_running_sync = False
                                        self.root.after(0, lambda: self.sync_button.config(text="🚀 立即执行同步流程", state="normal"))
                                        
                                        # 恢复托盘图标到正常状态
                                        if self.system_tray:
                                            self.system_tray.update_icon_status("normal")
                                
                                # 启动定时同步线程
                                sync_thread = threading.Thread(target=scheduled_sync, daemon=True)
                                sync_thread.start()
                                
                                # 等待一天，避免重复触发同一时间点
                                time.sleep(24 * 60 * 60)  # 24小时
                                continue
                            else:
                                self.log_message("定时触发条件满足，但同步流程已在运行中", "INFO")
                        else:
                            remaining_time = self.get_remaining_cooldown_minutes()
                            self.log_message(f"定时触发条件已满足（{trigger_time_str}），但全局冷却未到，剩余{remaining_time:.1f}分钟", "INFO")
                
                # 每分钟检查一次
                time.sleep(60)
                
            except Exception as e:
                self.log_message(f"定时监控线程出错: {e}", "ERROR")
                time.sleep(300)  # 出错时等待5分钟

    def is_global_cooldown_active(self):
        """检查全局冷却时间是否仍在生效"""
        if self.last_global_trigger_time is None:
            return False
        
        cooldown_minutes = self.config.config.get('idle_trigger', {}).get('cooldown_minutes', 60)
        current_time = datetime.now()
        elapsed_minutes = (current_time - self.last_global_trigger_time).total_seconds() / 60
        
        return elapsed_minutes < cooldown_minutes
    
    def get_remaining_cooldown_minutes(self):
        """获取剩余冷却时间（分钟）"""
        if self.last_global_trigger_time is None:
            return 0
        
        cooldown_minutes = self.config.config.get('idle_trigger', {}).get('cooldown_minutes', 60)
        current_time = datetime.now()
        elapsed_minutes = (current_time - self.last_global_trigger_time).total_seconds() / 60
        remaining = cooldown_minutes - elapsed_minutes
        
        return max(0, remaining)
    
    def update_global_trigger_time(self):
        """更新全局触发时间（同步成功完成后）"""
        self.last_global_trigger_time = datetime.now()
        cooldown_minutes = self.config.config.get('idle_trigger', {}).get('cooldown_minutes', 60)
        self.log_message(f"同步成功完成，开始{cooldown_minutes}分钟全局冷却时间", "INFO")
        
        # 立即更新冷却显示，无需等待下次定时更新
        self.update_cooldown_display_optimized()

    def reset_global_cooldown(self):
        """重置全局冷却时间"""
        from tkinter import messagebox
        
        # 检查是否有冷却时间需要重置
        if not self.is_global_cooldown_active():
            messagebox.showinfo("提示", "当前没有全局冷却时间，无需重置。")
            return
        
        # 显示剩余冷却时间并确认重置
        remaining_time = self.get_remaining_cooldown_minutes()
        remaining_minutes = int(remaining_time)
        remaining_seconds = int((remaining_time - remaining_minutes) * 60)
        
        if remaining_minutes > 0:
            time_str = f"{remaining_minutes}分{remaining_seconds}秒"
        else:
            time_str = f"{remaining_seconds}秒"
        
        result = messagebox.askyesno(
            "确认重置冷却时间",
            f"当前剩余冷却时间：{time_str}\n\n重置后将立即允许自动触发同步。\n\n确定要重置吗？",
            icon='question'
        )
        
        if result:
            # 重置全局冷却时间
            self.last_global_trigger_time = None
            
            self.log_message("全局冷却时间已手动重置，自动触发恢复正常", "INFO")
            
            # 立即更新GUI显示
            self.update_other_status_optimized()
            self.update_cooldown_display_optimized()  # 立即更新冷却显示
            
            messagebox.showinfo("重置完成", "全局冷却时间已重置，自动触发功能已恢复。")

    def update_reset_cooldown_button_state(self):
        """更新重置冷却按钮的状态"""
        if hasattr(self, 'reset_cooldown_button'):
            try:
                if self.is_global_cooldown_active():
                    # 有冷却时间时启用按钮
                    self.reset_cooldown_button.configure(state='normal')
                else:
                    # 没有冷却时间时禁用按钮
                    self.reset_cooldown_button.configure(state='disabled')
            except Exception as e:
                self.log_message(f"更新重置冷却按钮状态出错: {e}", "ERROR")

    def log_message(self, message, level="INFO"):
        """添加日志消息（根据配置的日志级别过滤，同时写入GUI和文件）"""
        # 检查日志级别过滤
        if not self._should_log(level):
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        # 同时写入文件日志
        self._write_to_file(formatted_message)
        
        # 在主线程中更新GUI
        self.root.after(0, lambda: self._append_log(formatted_message, level))
    
    def _should_log(self, level):
        """检查是否应该记录此级别的日志"""
        # 定义日志级别优先级
        level_priority = {
            'DEBUG': 1,
            'INFO': 2,
            'WARNING': 3,
            'ERROR': 4
        }
        
        # 获取配置的日志级别
        config_level = self.config.config.get('logging', {}).get('level', 'info').upper()
        message_level = level.upper()
        
        # 只有当消息级别 >= 配置级别时才记录
        config_priority = level_priority.get(config_level, 2)  # 默认INFO
        message_priority = level_priority.get(message_level, 2)  # 默认INFO
        
        return message_priority >= config_priority
    
    def _setup_file_logging(self):
        """设置文件日志系统"""
        try:
            # 创建logs目录
            self.logs_dir = "logs"
            os.makedirs(self.logs_dir, exist_ok=True)
            
            # 获取当前日期作为日志文件名
            current_date = datetime.now().strftime("%Y-%m-%d")
            self.current_log_file = os.path.join(self.logs_dir, f"{current_date}.log")
            
            # 写入启动日志
            self._write_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: 程序启动，开始记录日志\n")
            
            # 执行日志文件轮转清理
            self._rotate_log_files()
            
        except Exception as e:
            # 如果文件日志设置失败，只在GUI中显示错误，不中断程序
            print(f"文件日志设置失败: {e}")
    
    def _write_to_file(self, message):
        """写入日志到文件"""
        try:
            # 检查是否启用日志记录
            if not self.config.config.get('logging', {}).get('enabled', True):
                return
            
            # 检查是否需要创建新的日志文件（日期变化）
            current_date = datetime.now().strftime("%Y-%m-%d")
            expected_log_file = os.path.join(self.logs_dir, f"{current_date}.log")
            
            if expected_log_file != self.current_log_file:
                self.current_log_file = expected_log_file
                # 为新文件写入开始标记
                self._write_to_file(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: 新日志文件开始\n")
            
            # 写入日志
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                f.write(message)
                f.flush()  # 确保立即写入
                
        except Exception as e:
            # 文件写入失败时不中断程序运行
            print(f"写入日志文件失败: {e}")
    
    def _rotate_log_files(self):
        """日志文件轮转清理"""
        try:
            if not os.path.exists(self.logs_dir):
                return
            
            # 获取配置的最大文件数
            max_files = self.config.config.get('logging', {}).get('max_log_files', 5)
            
            # 获取所有.log文件，按修改时间排序
            log_files = []
            for filename in os.listdir(self.logs_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(self.logs_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    log_files.append((filepath, mtime))
            
            # 按时间排序（最新的在前）
            log_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超出数量限制的旧文件
            if len(log_files) > max_files:
                for filepath, _ in log_files[max_files:]:
                    try:
                        os.remove(filepath)
                        print(f"已删除旧日志文件: {os.path.basename(filepath)}")
                    except Exception as e:
                        print(f"删除旧日志文件失败 {filepath}: {e}")
            
        except Exception as e:
            print(f"日志轮转清理失败: {e}")
    
    def _append_log(self, message, level):
        """在主线程中添加日志"""
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
        if lines > 300:  # 进一步减少到300行
            self.log_text.delete('1.0', '100.0')
    
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
                
                # 冷却时间将在同步成功完成后更新（手动触发也会产生冷却）
                
                # 更新托盘图标状态
                if self.system_tray:
                    self.system_tray.update_icon_status("running")
                
                # 执行同步流程（GUI版本）
                success = sync_workflow.run_full_sync_workflow_gui(self.log_message)
                
                self.last_sync_time = datetime.now()
                if success:
                    self.sync_success_count += 1
                    self.log_message("同步流程执行成功", "SUCCESS")
                    
                    # 同步成功后更新全局冷却时间
                    self.update_global_trigger_time()
                    
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
                # 更新GUI状态显示
                self.update_other_status_optimized()
                
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
    
    def on_closing(self):
        """窗口关闭事件处理"""
        # 获取关闭行为配置
        close_behavior = self.config.config.get('gui', {}).get('close_behavior', 'exit')
        remember_choice = self.config.config.get('gui', {}).get('remember_close_choice', False)
        
        if close_behavior == 'exit':
            # 直接退出
            self.quit_application()
        elif close_behavior == 'minimize':
            # 最小化到托盘（如果支持的话）
            if self.system_tray and self.system_tray.is_running:
                try:
                    self.root.withdraw()  # 隐藏窗口
                    self.log_message("应用已最小化到系统托盘", "INFO")
                except Exception as e:
                    self.log_message(f"最小化到托盘失败: {e}", "ERROR")
                    self.quit_application()
            else:
                # 托盘不可用，询问用户是否直接退出
                from tkinter import messagebox
                result = messagebox.askyesno(
                    "系统托盘不可用",
                    "系统托盘功能不可用，无法最小化到托盘。\n\n是否直接退出程序？\n\n点击'否'将保持窗口显示。",
                    icon='warning'
                )
                if result:
                    self.quit_application()
                # 否则什么都不做，保持窗口显示
        elif close_behavior == 'ask':
            # 询问用户 - 始终显示自定义对话框让用户选择
            self.show_close_choice_dialog()
    
    def restore_from_tray(self):
        """从托盘恢复窗口显示"""
        try:
            self.root.deiconify()  # 显示窗口
            self.root.lift()       # 提升窗口到最前面
            self.root.focus_force() # 强制获得焦点
            self.log_message("应用已从系统托盘恢复", "INFO")
        except Exception as e:
            self.log_message(f"从托盘恢复窗口失败: {e}", "ERROR")
    
    def show_close_choice_dialog(self):
        """显示带记住选择的关闭对话框"""
        import tkinter as tk
        from tkinter import messagebox
        
        # 创建自定义对话框
        dialog = ttk.Toplevel(self.root)
        dialog.title("选择关闭方式")
        dialog.geometry("700x700")
        dialog.resizable(True, True)
        dialog.minsize(600, 600)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding="25")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="请选择程序关闭方式",
            font=("Microsoft YaHei", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 说明文字
        desc_label = ttk.Label(
            main_frame,
            text="您可以选择直接退出程序，或者将程序最小化到后台继续运行。",
            font=("Microsoft YaHei", 10),
            foreground="gray"
        )
        desc_label.pack(pady=(0, 20))
        
        # 选择变量
        choice_var = tk.StringVar(value="exit")
        remember_var = tk.BooleanVar(value=False)
        
        # 选项框架
        options_frame = ttk.LabelFrame(main_frame, text="关闭方式选项", padding="20")
        options_frame.pack(fill="x", pady=(0, 20))
        options_frame.columnconfigure(0, weight=1)
        
        # 退出选项
        exit_frame = ttk.Frame(options_frame)
        exit_frame.pack(fill="x", pady=(0, 10))
        
        exit_radio = ttk.Radiobutton(
            exit_frame,
            text="直接退出程序",
            variable=choice_var,
            value="exit",
            bootstyle="info"
        )
        exit_radio.pack(anchor="w")
        
        exit_desc = ttk.Label(
            exit_frame,
            text="完全关闭程序，停止所有监控服务",
            font=("Microsoft YaHei", 9),
            foreground="gray"
        )
        exit_desc.pack(anchor="w", padx=(25, 0))
        
        # 最小化选项
        minimize_frame = ttk.Frame(options_frame)
        minimize_frame.pack(fill="x", pady=(10, 0))
        
        minimize_radio = ttk.Radiobutton(
            minimize_frame,
            text="最小化到系统托盘（后台运行）",
            variable=choice_var,
            value="minimize",
            bootstyle="info"
        )
        minimize_radio.pack(anchor="w")
        
        minimize_desc = ttk.Label(
            minimize_frame,
            text="隐藏窗口但继续在后台运行，监控服务保持活跃",
            font=("Microsoft YaHei", 9),
            foreground="gray"
        )
        minimize_desc.pack(anchor="w", padx=(25, 0))
        
        # 记住选择区域
        remember_frame = ttk.LabelFrame(main_frame, text="记住设置", padding="15")
        remember_frame.pack(fill="x", pady=(0, 20))
        
        remember_check = ttk.Checkbutton(
            remember_frame,
            text="记住我的选择，下次关闭时不再询问",
            variable=remember_var,
            bootstyle="round-toggle"
        )
        remember_check.pack(anchor="w")
        
        remember_desc = ttk.Label(
            remember_frame,
            text="勾选此项后，程序将记住您的选择并在下次关闭时自动执行",
            font=("Microsoft YaHei", 9),
            foreground="gray",
            wraplength=450
        )
        remember_desc.pack(anchor="w", pady=(5, 0), fill="x")
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        def on_confirm():
            choice = choice_var.get()
            remember = remember_var.get()
            
            # 如果选择记住，更新配置
            if remember:
                try:
                    config_data = self.config.config.copy()
                    config_data['gui']['close_behavior'] = choice
                    config_data['gui']['remember_close_choice'] = True
                    self.config.save_config(config_data)
                    self.log_message(f"已保存关闭方式设置: {choice}", "INFO")
                except Exception as e:
                    self.log_message(f"保存设置失败: {e}", "ERROR")
            
            dialog.destroy()
            
            # 执行选择的操作
            if choice == "exit":
                self.quit_application()
            elif choice == "minimize":
                if self.system_tray and self.system_tray.is_running:
                    try:
                        self.root.withdraw()
                        self.log_message("应用已最小化到系统托盘", "INFO")
                    except Exception as e:
                        self.log_message(f"最小化到托盘失败: {e}", "ERROR")
                        self.quit_application()
                else:
                    # 托盘不可用，提示用户
                    from tkinter import messagebox
                    messagebox.showwarning(
                        "系统托盘不可用",
                        "系统托盘功能不可用，无法最小化到托盘。\n程序将继续在前台运行。"
                    )
        
        def on_cancel():
            dialog.destroy()
        
        # 居中按钮
        button_center_frame = ttk.Frame(button_frame)
        button_center_frame.pack(anchor="center")
        
        ttk.Button(
            button_center_frame,
            text="确定",
            command=on_confirm,
            bootstyle="success",
            width=15
        ).pack(side="left", padx=(0, 15))
        
        ttk.Button(
            button_center_frame,
            text="取消",
            command=on_cancel,
            bootstyle="outline-secondary",
            width=15
        ).pack(side="left")
    
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