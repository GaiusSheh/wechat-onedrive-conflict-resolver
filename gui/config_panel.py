#!/usr/bin/env python3
"""
配置面板GUI - 五个标签页的配置界面 v3.0
用于编辑 configs.json 配置文件

=== 开发日志 ===
v3.0 (2025-08-09) - 中文本地化完成
- [本地化] 窗口关闭行为选项全面中文化：每次询问我/最小化到托盘/直接退出程序
- [兼容性] 保持英文配置值映射，确保向后兼容性 (ask/minimize/exit)
- [界面] 窗口自动居中显示，提升用户体验
- [映射系统] 实现中英文选项双向映射机制

v2.3 (2025-08-08) - 性能优化版
- [性能] 启动速度优化，配置面板秒开秒关
- [响应] GUI操作流畅度提升，无卡顿现象
- [主题] 统一ttkbootstrap现代化主题风格

=== 技术实现 ===
- 中英文映射：self.close_behavior_mapping 双向转换
- 窗口居中：动态计算屏幕尺寸和窗口位置
- 配置验证：实时校验用户输入的配置有效性
- 热重载：支持配置文件实时更新和保存
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import sys
import os

# 添加core模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from config_manager import ConfigManager

# 导入性能调试系统
from core.performance_debug import (
    measure_time, perf_log, log_user_action, log_gui_update, 
    log_system_call, perf_timer, PERFORMANCE_DEBUG_ENABLED
)

class ConfigPanel:
    """配置面板类"""
    
    def __init__(self, parent=None, on_config_saved=None):
        self.parent = parent
        self.on_config_saved = on_config_saved  # 配置保存后的回调函数
        self.config_manager = ConfigManager()
        self.config_data = self.config_manager.config.copy()
        self.has_changes = False
        
        # 创建配置窗口
        if parent:
            self.window = ttk.Toplevel(parent)
            self.window.transient(parent)
            self.window.grab_set()
        else:
            self.window = ttk.Window(themename="cosmo")
        
        self.window.title("配置面板")
        
        # 计算屏幕中心位置
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = 800
        window_height = 800
        
        # 计算窗口左上角坐标（居中显示）
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.minsize(800, 800)
        
        # 配置变量字典
        self.vars = {}
        
        self.setup_ui()
        self.load_config_to_ui()
        
        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # 创建标签页（去掉标题）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # 创建四个标签页
        self.create_trigger_settings_tab()    # 触发设置（合并静置+定时）
        self.create_sync_timing_tab()         # 同步等待时间
        self.create_logging_tab()             # 日志行为
        self.create_interface_behavior_tab()  # 界面行为
        
        # 底部按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        # 按钮
        ttk.Button(button_frame, text="重置", command=self.reset_config, bootstyle=SECONDARY).pack(side=LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导入", command=self.import_config, bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="导出", command=self.export_config, bootstyle=INFO).pack(side=LEFT, padx=5)
        
        ttk.Button(button_frame, text="取消", command=self.on_closing, bootstyle=SECONDARY).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="保存", command=self.save_config, bootstyle=PRIMARY).pack(side=RIGHT, padx=5)
    
    def create_trigger_settings_tab(self):
        """创建触发设置标签页（合并静置和定时触发）"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="触发设置")
        
        # 滚动框架
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        content = ttk.Frame(scrollable_frame, padding=15)
        content.pack(fill=BOTH, expand=True)
        
        # 静置触发设置
        ttk.Label(content, text="静置触发", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor=W, pady=(0, 10))
        ttk.Label(content, text="当系统空闲指定时间后自动执行同步", foreground="gray").pack(anchor=W, pady=(0, 10))
        
        self.vars['idle_enabled'] = tk.BooleanVar()
        ttk.Checkbutton(content, text="启用静置触发", variable=self.vars['idle_enabled'],
                       command=self.on_config_change).pack(anchor=W, pady=5)
        
        idle_frame = ttk.Frame(content)
        idle_frame.pack(fill=X, pady=5)
        ttk.Label(idle_frame, text="静置时间:").pack(side=LEFT)
        self.vars['idle_minutes'] = tk.IntVar()
        idle_spinbox = ttk.Spinbox(idle_frame, from_=1, to=120, width=10, 
                                  textvariable=self.vars['idle_minutes'],
                                  command=self.on_config_change)
        idle_spinbox.pack(side=LEFT, padx=(10, 5))
        ttk.Label(idle_frame, text="分钟后触发同步").pack(side=LEFT)
        
        # 分隔线
        ttk.Separator(content, orient='horizontal').pack(fill=X, pady=20)
        
        # 定时触发设置
        ttk.Label(content, text="定时触发", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor=W, pady=(0, 10))
        ttk.Label(content, text="在指定时间自动执行同步", foreground="gray").pack(anchor=W, pady=(0, 10))
        
        self.vars['scheduled_enabled'] = tk.BooleanVar()
        ttk.Checkbutton(content, text="启用定时触发", variable=self.vars['scheduled_enabled'],
                       command=self.on_config_change).pack(anchor=W, pady=5)
        
        time_frame = ttk.Frame(content)
        time_frame.pack(fill=X, pady=10)
        ttk.Label(time_frame, text="执行时间:").pack(side=LEFT)
        self.vars['scheduled_time'] = tk.StringVar()
        time_entry = ttk.Entry(time_frame, textvariable=self.vars['scheduled_time'], width=10)
        time_entry.pack(side=LEFT, padx=(10, 5))
        ttk.Label(time_frame, text="(24小时格式，如: 16:30)").pack(side=LEFT)
        
        days_frame = ttk.Frame(content)
        days_frame.pack(fill=X, anchor=W, pady=5)
        ttk.Label(days_frame, text="执行日期:").pack(anchor=W)
        
        self.vars['daily'] = tk.BooleanVar()
        self.vars['monday'] = tk.BooleanVar()
        self.vars['tuesday'] = tk.BooleanVar()
        self.vars['wednesday'] = tk.BooleanVar()
        self.vars['thursday'] = tk.BooleanVar()
        self.vars['friday'] = tk.BooleanVar()
        self.vars['saturday'] = tk.BooleanVar()
        self.vars['sunday'] = tk.BooleanVar()
        
        days_check_frame = ttk.Frame(content)
        days_check_frame.pack(fill=X, anchor=W, padx=(20, 0), pady=5)
        
        ttk.Checkbutton(days_check_frame, text="每天", variable=self.vars['daily'],
                       command=self.on_daily_change).pack(anchor=W)
        
        specific_days_frame = ttk.Frame(days_check_frame)
        specific_days_frame.pack(fill=X, anchor=W, pady=(5, 0))
        
        ttk.Checkbutton(specific_days_frame, text="周一", variable=self.vars['monday'],
                       command=self.on_specific_day_change).grid(row=0, column=0, sticky=W, padx=(0, 10))
        ttk.Checkbutton(specific_days_frame, text="周二", variable=self.vars['tuesday'],
                       command=self.on_specific_day_change).grid(row=0, column=1, sticky=W, padx=(0, 10))
        ttk.Checkbutton(specific_days_frame, text="周三", variable=self.vars['wednesday'],
                       command=self.on_specific_day_change).grid(row=0, column=2, sticky=W, padx=(0, 10))
        ttk.Checkbutton(specific_days_frame, text="周四", variable=self.vars['thursday'],
                       command=self.on_specific_day_change).grid(row=0, column=3, sticky=W, padx=(0, 10))
        
        ttk.Checkbutton(specific_days_frame, text="周五", variable=self.vars['friday'],
                       command=self.on_specific_day_change).grid(row=1, column=0, sticky=W, padx=(0, 10), pady=(5, 0))
        ttk.Checkbutton(specific_days_frame, text="周六", variable=self.vars['saturday'],
                       command=self.on_specific_day_change).grid(row=1, column=1, sticky=W, padx=(0, 10), pady=(5, 0))
        ttk.Checkbutton(specific_days_frame, text="周日", variable=self.vars['sunday'],
                       command=self.on_specific_day_change).grid(row=1, column=2, sticky=W, padx=(0, 10), pady=(5, 0))
        
        # 绑定事件
        idle_spinbox.bind("<KeyRelease>", lambda e: self.on_config_change())
        time_entry.bind("<KeyRelease>", lambda e: self.on_config_change())
    
    def create_sync_timing_tab(self):
        """创建同步等待时间标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="同步等待时间")
        
        content = ttk.Frame(frame, padding=15)
        content.pack(fill=BOTH, expand=True)
        
        # OneDrive同步等待时间
        ttk.Label(content, text="OneDrive同步等待", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor=W, pady=(0, 10))
        ttk.Label(content, text="OneDrive重启后等待多久认为同步完成", foreground="gray").pack(anchor=W, pady=(0, 15))
        
        wait_frame = ttk.Frame(content)
        wait_frame.pack(fill=X, pady=5)
        ttk.Label(wait_frame, text="等待时间:").pack(side=LEFT)
        self.vars['wait_minutes'] = tk.IntVar()
        wait_spinbox = ttk.Spinbox(wait_frame, from_=1, to=30, width=10,
                                  textvariable=self.vars['wait_minutes'],
                                  command=self.on_config_change)
        wait_spinbox.pack(side=LEFT, padx=(10, 5))
        ttk.Label(wait_frame, text="分钟").pack(side=LEFT)
        
        # 分隔线
        ttk.Separator(content, orient='horizontal').pack(fill=X, pady=20)
        
        # 全局冷却时间
        ttk.Label(content, text="全局冷却时间", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor=W, pady=(0, 10))
        ttk.Label(content, text="所有触发类型共享冷却时间，防止过于频繁同步", foreground="gray").pack(anchor=W, pady=(0, 15))
        
        cooldown_frame = ttk.Frame(content)
        cooldown_frame.pack(fill=X, pady=5)
        ttk.Label(cooldown_frame, text="冷却时间:").pack(side=LEFT)
        self.vars['cooldown_minutes'] = tk.IntVar()
        cooldown_spinbox = ttk.Spinbox(cooldown_frame, from_=1, to=180, width=10,
                                      textvariable=self.vars['cooldown_minutes'],
                                      command=self.on_config_change)
        cooldown_spinbox.pack(side=LEFT, padx=(10, 5))
        ttk.Label(cooldown_frame, text="分钟").pack(side=LEFT)
        
        # 分隔线
        ttk.Separator(content, orient='horizontal').pack(fill=X, pady=20)
        
        # 重试设置
        ttk.Label(content, text="重试设置", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor=W, pady=(0, 10))
        ttk.Label(content, text="同步失败时的重试策略", foreground="gray").pack(anchor=W, pady=(0, 15))
        
        retry_frame = ttk.Frame(content)
        retry_frame.pack(fill=X, pady=5)
        ttk.Label(retry_frame, text="最大重试次数:").pack(side=LEFT)
        self.vars['retry_attempts'] = tk.IntVar()
        retry_spinbox = ttk.Spinbox(retry_frame, from_=0, to=10, width=10,
                                   textvariable=self.vars['retry_attempts'],
                                   command=self.on_config_change)
        retry_spinbox.pack(side=LEFT, padx=(10, 5))
        ttk.Label(retry_frame, text="次").pack(side=LEFT)
        
        # 绑定事件
        wait_spinbox.bind("<KeyRelease>", lambda e: self.on_config_change())
        cooldown_spinbox.bind("<KeyRelease>", lambda e: self.on_config_change())
        retry_spinbox.bind("<KeyRelease>", lambda e: self.on_config_change())
    
    
    def create_logging_tab(self):
        """创建日志设置标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="日志设置")
        
        content = ttk.Frame(frame, padding=15)
        content.pack(fill=BOTH, expand=True)
        
        # 日志设置
        ttk.Label(content, text="日志设置", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor=W, pady=(0, 10))
        ttk.Label(content, text="记录程序运行日志", foreground="gray").pack(anchor=W, pady=(0, 15))
        
        # 启用日志
        self.vars['logging_enabled'] = tk.BooleanVar()
        ttk.Checkbutton(content, text="启用日志记录", variable=self.vars['logging_enabled'],
                       command=self.on_config_change).pack(anchor=W, pady=5)
        
        # 日志级别
        level_frame = ttk.Frame(content)
        level_frame.pack(fill=X, pady=(15, 5))
        ttk.Label(level_frame, text="日志级别:").pack(side=LEFT)
        self.vars['log_level'] = tk.StringVar()
        level_combo = ttk.Combobox(level_frame, textvariable=self.vars['log_level'],
                                  values=["debug", "info", "warning", "error"],
                                  state="readonly", width=12)
        level_combo.pack(side=LEFT, padx=(10, 0))
        
        # 最大日志文件数
        files_frame = ttk.Frame(content)
        files_frame.pack(fill=X, pady=(15, 5))
        ttk.Label(files_frame, text="保留的最大日志文件数:").pack(side=LEFT)
        self.vars['max_log_files'] = tk.IntVar()
        files_spinbox = ttk.Spinbox(files_frame, from_=1, to=30, width=10,
                                   textvariable=self.vars['max_log_files'],
                                   command=self.on_config_change)
        files_spinbox.pack(side=LEFT, padx=(10, 5))
        ttk.Label(files_frame, text="个").pack(side=LEFT)
        
        # 绑定变化事件
        level_combo.bind("<<ComboboxSelected>>", lambda e: self.on_config_change())
        files_spinbox.bind("<KeyRelease>", lambda e: self.on_config_change())
    
    def create_interface_behavior_tab(self):
        """创建界面行为标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="界面行为")
        
        content = ttk.Frame(frame, padding=15)
        content.pack(fill=BOTH, expand=True)
        
        # 窗口关闭行为
        ttk.Label(content, text="窗口关闭行为", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor=W, pady=(0, 10))
        ttk.Label(content, text="决定点击关闭按钮时的行为", foreground="gray").pack(anchor=W, pady=(0, 15))
        
        close_frame = ttk.Frame(content)
        close_frame.pack(fill=X, pady=5)
        ttk.Label(close_frame, text="关闭行为:").pack(side=LEFT)
        self.vars['close_behavior'] = tk.StringVar()
        
        # 关闭行为映射
        self.close_behavior_mapping = {
            "每次询问我": "ask",
            "最小化到托盘": "minimize", 
            "直接退出程序": "exit"
        }
        self.reverse_close_behavior_mapping = {v: k for k, v in self.close_behavior_mapping.items()}
        
        close_combo = ttk.Combobox(close_frame, textvariable=self.vars['close_behavior'],
                                  values=["每次询问我", "最小化到托盘", "直接退出程序"],
                                  state="readonly", width=15)
        close_combo.pack(side=LEFT, padx=(10, 0))
        
        # 删除原来的说明文本，因为现在选项已经是中文了
        
        self.vars['remember_close'] = tk.BooleanVar()
        ttk.Checkbutton(content, text="记住选择，避免重复询问", variable=self.vars['remember_close'],
                       command=self.on_config_change).pack(anchor=W, pady=5)
        
        # 分隔线
        ttk.Separator(content, orient='horizontal').pack(fill=X, pady=20)
        
        # 开机自启动设置
        ttk.Label(content, text="开机自启动设置", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor=W, pady=(0, 10))
        ttk.Label(content, text="配置程序的开机自动启动行为", foreground="gray").pack(anchor=W, pady=(0, 15))
        
        self.vars['auto_start_enabled'] = tk.BooleanVar()
        ttk.Checkbutton(content, text="开机自动启动程序", variable=self.vars['auto_start_enabled'],
                       command=self.on_auto_start_change).pack(anchor=W, pady=5)
        
        self.vars['auto_start_minimized'] = tk.BooleanVar()
        ttk.Checkbutton(content, text="开机启动时最小化到托盘", variable=self.vars['auto_start_minimized'],
                       command=self.on_config_change).pack(anchor=W, pady=5)
        
        
        # 绑定事件
        close_combo.bind("<<ComboboxSelected>>", lambda e: self.on_config_change())
    
    def on_daily_change(self):
        """处理每天选项变化"""
        if self.vars['daily'].get():
            # 如果选择了每天，清除所有特定日期
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                self.vars[day].set(False)
        self.on_config_change()
    
    def on_specific_day_change(self):
        """处理特定日期选项变化"""
        # 如果选择了任何特定日期，取消每天选项
        any_specific = any(self.vars[day].get() for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'])
        if any_specific:
            self.vars['daily'].set(False)
        self.on_config_change()
    
    def on_config_change(self):
        """配置发生变化时的处理"""
        self.has_changes = True
        self.update_window_title()
    
    def on_auto_start_change(self):
        """处理开机自启动选项变化"""
        try:
            from core.startup_manager import StartupManager
            manager = StartupManager()
            
            if self.vars['auto_start_enabled'].get():
                # 启用自启动
                minimized = self.vars['auto_start_minimized'].get()
                success, message = manager.enable_startup(minimized=minimized)
                if not success:
                    messagebox.showerror("自启动设置失败", f"无法启用开机自启动:\n{message}")
                    self.vars['auto_start_enabled'].set(False)
                    return
                else:
                    messagebox.showinfo("自启动设置成功", "已成功启用开机自启动")
            else:
                # 禁用自启动
                success, message = manager.disable_startup()
                if not success:
                    messagebox.showerror("自启动设置失败", f"无法禁用开机自启动:\n{message}")
                    self.vars['auto_start_enabled'].set(True)
                    return
                else:
                    messagebox.showinfo("自启动设置成功", "已成功禁用开机自启动")
        
        except Exception as e:
            messagebox.showerror("自启动设置错误", f"设置开机自启动时发生错误:\n{str(e)}")
            self.vars['auto_start_enabled'].set(False)
        
        self.on_config_change()
    
    def update_window_title(self):
        """更新窗口标题"""
        title = "配置面板"
        if self.has_changes:
            title += " *"
        self.window.title(title)
    
    @measure_time("ConfigPanel", "加载配置到UI")
    def load_config_to_ui(self):
        """从配置数据加载到UI"""
        # PERFORMANCE: 记录配置加载过程
        perf_log("配置面板开始加载配置数据")
        
        try:
            # 静置触发设置
            idle_config = self.config_data.get('idle_trigger', {})
            self.vars['idle_enabled'].set(idle_config.get('enabled', True))
            self.vars['idle_minutes'].set(idle_config.get('idle_minutes', 1))
            self.vars['cooldown_minutes'].set(idle_config.get('cooldown_minutes', 20))
            
            # 定时触发设置
            scheduled_config = self.config_data.get('scheduled_trigger', {})
            self.vars['scheduled_enabled'].set(scheduled_config.get('enabled', True))
            self.vars['scheduled_time'].set(scheduled_config.get('time', '16:30'))
            
            # 处理日期设置
            days = scheduled_config.get('days', ['daily'])
            if 'daily' in days:
                self.vars['daily'].set(True)
            else:
                day_map = {
                    'monday': '周一', 'tuesday': '周二', 'wednesday': '周三', 'thursday': '周四',
                    'friday': '周五', 'saturday': '周六', 'sunday': '周日'
                }
                for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                    self.vars[day].set(day in days)
            
            # 同步设置
            sync_config = self.config_data.get('sync_settings', {})
            self.vars['wait_minutes'].set(sync_config.get('wait_after_sync_minutes', 2))
            self.vars['retry_attempts'].set(sync_config.get('max_retry_attempts', 3))
            
            # 日志设置
            logging_config = self.config_data.get('logging', {})
            self.vars['logging_enabled'].set(logging_config.get('enabled', True))
            self.vars['log_level'].set(logging_config.get('level', 'info'))
            self.vars['max_log_files'].set(logging_config.get('max_log_files', 5))
            
            # GUI设置
            gui_config = self.config_data.get('gui', {})
            close_behavior_value = gui_config.get('close_behavior', 'exit')
            # 将英文值转换为中文显示
            close_behavior_display = self.reverse_close_behavior_mapping.get(close_behavior_value, '直接退出程序')
            self.vars['close_behavior'].set(close_behavior_display)
            self.vars['remember_close'].set(gui_config.get('remember_close_choice', True))
            
            # 启动设置
            startup_config = self.config_data.get('startup', {})
            
            # 检查实际的自启动状态
            try:
                from core.startup_manager import StartupManager
                manager = StartupManager()
                actual_auto_start = manager.is_startup_enabled()
                # 如果配置文件和实际状态不一致，以实际状态为准
                auto_start_enabled = actual_auto_start
            except:
                auto_start_enabled = startup_config.get('auto_start_enabled', False)
            
            self.vars['auto_start_enabled'].set(auto_start_enabled)
            self.vars['auto_start_minimized'].set(startup_config.get('auto_start_minimized', True))
            
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
        
        self.has_changes = False
        self.update_window_title()
    
    def collect_config_from_ui(self):
        """从UI收集配置数据"""
        try:
            # 构建日期列表
            days = []
            if self.vars['daily'].get():
                days = ['daily']
            else:
                day_list = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                days = [day for day in day_list if self.vars[day].get()]
            
            # 构建配置数据
            config = {
                "idle_trigger": {
                    "enabled": self.vars['idle_enabled'].get(),
                    "idle_minutes": self.vars['idle_minutes'].get(),
                    "cooldown_minutes": self.vars['cooldown_minutes'].get()
                },
                "scheduled_trigger": {
                    "enabled": self.vars['scheduled_enabled'].get(),
                    "time": self.vars['scheduled_time'].get(),
                    "days": days if days else ['daily']
                },
                "sync_settings": {
                    "wait_after_sync_minutes": self.vars['wait_minutes'].get(),
                    "max_retry_attempts": self.vars['retry_attempts'].get()
                },
                "logging": {
                    "enabled": self.vars['logging_enabled'].get(),
                    "level": self.vars['log_level'].get(),
                    "max_log_files": self.vars['max_log_files'].get()
                },
                "gui": {
                    "close_behavior": self.close_behavior_mapping.get(self.vars['close_behavior'].get(), 'exit'),
                    "remember_close_choice": self.vars['remember_close'].get()
                },
                "startup": {
                    "auto_start_enabled": self.vars['auto_start_enabled'].get(),
                    "auto_start_minimized": self.vars['auto_start_minimized'].get()
                }
            }
            
            # 合并注释和其他原有配置
            for key, value in self.config_data.items():
                if key.startswith('_comment_') or key not in config:
                    config[key] = value
            
            # 合并子配置的注释
            for section_name, section_config in config.items():
                if isinstance(section_config, dict) and section_name in self.config_data:
                    original_section = self.config_data[section_name]
                    if isinstance(original_section, dict):
                        for key, value in original_section.items():
                            if key.startswith('_comment_') and key not in section_config:
                                section_config[key] = value
            
            return config
            
        except Exception as e:
            messagebox.showerror("错误", f"收集配置数据失败: {str(e)}")
            return None
    
    @measure_time("ConfigPanel", "保存配置")
    def save_config(self):
        """保存配置"""
        # PERFORMANCE: 记录用户点击保存按钮操作
        log_user_action("ConfigPanel", "保存按钮点击")
        
        config = self.collect_config_from_ui()
        if config is None:
            return
        
        try:
            # 验证配置
            if not self.validate_config(config):
                return
            
            # 保存到文件 - 区分开发环境和打包环境
            if getattr(sys, 'frozen', False):
                # 打包环境：使用ConfigManager的路径逻辑
                self.config_manager.config = config
                if not self.config_manager.save():
                    raise Exception("配置管理器保存失败")
            else:
                # 开发环境：使用相对路径
                config_file = os.path.join(os.path.dirname(__file__), '..', 'configs', 'configs.json')
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.config_data = config.copy()
            self.has_changes = False
            self.update_window_title()
            
            # 调用回调函数通知主窗口重新加载配置
            if self.on_config_saved:
                try:
                    self.on_config_saved()
                except Exception as callback_error:
                    # logger.error(f"配置保存回调函数执行失败: {callback_error}")
                    pass
            
            messagebox.showinfo("成功", "配置已保存")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def reset_config(self):
        """重置配置"""
        if messagebox.askyesno("确认", "确定要重置所有配置到默认值吗？"):
            try:
                # 重新加载原始配置
                self.config_manager.reload()
                self.config_data = self.config_manager.config.copy()
                self.load_config_to_ui()
                messagebox.showinfo("成功", "配置已重置")
            except Exception as e:
                messagebox.showerror("错误", f"重置配置失败: {str(e)}")
    
    @measure_time("ConfigPanel", "导入配置")
    def import_config(self):
        """导入配置文件"""
        # PERFORMANCE: 记录用户点击导入按钮操作
        log_user_action("ConfigPanel", "导入按钮点击")
        
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                if self.validate_config(imported_config):
                    self.config_data = imported_config
                    self.load_config_to_ui()
                    messagebox.showinfo("成功", "配置文件已导入")
                
            except Exception as e:
                messagebox.showerror("错误", f"导入配置文件失败: {str(e)}")
    
    @measure_time("ConfigPanel", "导出配置")
    def export_config(self):
        """导出配置文件"""
        # PERFORMANCE: 记录用户点击导出按钮操作
        log_user_action("ConfigPanel", "导出按钮点击")
        
        config = self.collect_config_from_ui()
        if config is None:
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"配置文件已导出到: {file_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出配置文件失败: {str(e)}")
    
    def validate_config(self, config):
        """验证配置数据"""
        try:
            # 验证时间格式
            time_str = config.get('scheduled_trigger', {}).get('time', '')
            if time_str:
                time_parts = time_str.split(':')
                if len(time_parts) != 2:
                    raise ValueError("时间格式错误")
                hour, minute = int(time_parts[0]), int(time_parts[1])
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("时间超出有效范围")
            
            # 验证数值范围
            idle_minutes = config.get('idle_trigger', {}).get('idle_minutes', 1)
            if not (1 <= idle_minutes <= 120):
                raise ValueError("静置时间必须在1-120分钟之间")
            
            cooldown_minutes = config.get('idle_trigger', {}).get('cooldown_minutes', 20)
            if not (1 <= cooldown_minutes <= 180):
                raise ValueError("冷却时间必须在1-180分钟之间")
            
            wait_minutes = config.get('sync_settings', {}).get('wait_after_sync_minutes', 2)
            if not (1 <= wait_minutes <= 30):
                raise ValueError("等待时间必须在1-30分钟之间")
            
            retry_attempts = config.get('sync_settings', {}).get('max_retry_attempts', 3)
            if not (0 <= retry_attempts <= 10):
                raise ValueError("重试次数必须在0-10次之间")
            
            max_log_files = config.get('logging', {}).get('max_log_files', 5)
            if not (1 <= max_log_files <= 30):
                raise ValueError("最大日志文件数必须在1-30之间")
            
            return True
            
        except Exception as e:
            messagebox.showerror("配置验证错误", str(e))
            return False
    
    def on_closing(self):
        """窗口关闭时的处理"""
        if self.has_changes:
            result = messagebox.askyesnocancel("未保存的更改", "配置已修改但未保存，是否保存？\n\n是=保存并退出\n否=不保存直接退出\n取消=返回")
            
            if result is True:  # 保存并退出
                self.save_config()
                if self.has_changes:  # 如果保存失败，不退出
                    return
                self.window.destroy()
            elif result is False:  # 不保存直接退出
                self.window.destroy()
            # result is None (取消) - 不做任何操作，继续停留在窗口
        else:
            self.window.destroy()
    
    def show(self):
        """显示配置面板"""
        self.window.mainloop()

def main():
    """独立运行配置面板"""
    app = ConfigPanel()
    app.show()

if __name__ == "__main__":
    main()