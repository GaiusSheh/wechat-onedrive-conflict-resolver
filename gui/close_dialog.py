#!/usr/bin/env python3
"""
微信OneDrive冲突解决工具 - 自定义关闭对话框
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加core模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from core.logger_helper import logger

class CloseDialog:
    """自定义关闭对话框"""
    
    def __init__(self, parent, tray_available=True):
        logger.debug(f"创建关闭对话框，托盘可用: {tray_available}")
        self.parent = parent
        self.tray_available = tray_available
        self.result = None
        self.close_method = "minimize"  # 默认最小化到托盘
        self.remember_choice = False
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("关闭选项")
        self.dialog.geometry("520x420")  # 调整为更大的对话框
        self.dialog.resizable(False, False)
        
        # 设置为模态对话框
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.center_window()
        
        # 创建界面
        self.create_widgets()
        
        # 设置焦点
        self.dialog.focus_set()
        
        # 绑定关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def center_window(self):
        """窗口居中显示"""
        self.dialog.update_idletasks()
        
        # 获取窗口尺寸
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        
        # 获取屏幕尺寸
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """创建对话框组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="选择关闭方式:", 
                               font=("Microsoft YaHei UI", 10, "bold"))
        title_label.pack(pady=(0, 15))
        
        # 关闭方式选择框架
        method_frame = ttk.LabelFrame(main_frame, text="关闭方式", padding="10")
        method_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 关闭方式选项
        self.close_method_var = tk.StringVar(value="minimize" if self.tray_available else "exit")
        
        if self.tray_available:
            minimize_radio = ttk.Radiobutton(
                method_frame, 
                text="最小化到系统托盘（程序继续在后台运行）", 
                variable=self.close_method_var, 
                value="minimize"
            )
            minimize_radio.pack(anchor=tk.W, pady=2)
        
        exit_radio = ttk.Radiobutton(
            method_frame, 
            text="直接退出程序", 
            variable=self.close_method_var, 
            value="exit"
        )
        exit_radio.pack(anchor=tk.W, pady=2)
        
        # 如果托盘不可用，禁用最小化选项并选择退出
        if not self.tray_available:
            self.close_method_var.set("exit")
        
        # 记住选择框架
        remember_frame = ttk.Frame(main_frame)
        remember_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.remember_var = tk.BooleanVar(value=False)
        remember_checkbox = ttk.Checkbutton(
            remember_frame, 
            text="记住这种方式（下次不再询问）", 
            variable=self.remember_var
        )
        remember_checkbox.pack(anchor=tk.W)
        
        # 确认提示
        confirm_frame = ttk.Frame(main_frame)
        confirm_frame.pack(fill=tk.X, pady=(15, 20))
        
        confirm_label = ttk.Label(confirm_frame, text="确认使用上述设置关闭程序？",
                                 font=("Microsoft YaHei UI", 10))
        confirm_label.pack()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 10))
        
        # 取消按钮（否）
        cancel_button = tk.Button(
            button_frame, 
            text="否", 
            command=self.on_cancel,
            width=12,
            # height=2,
            font=("Microsoft YaHei UI", 12, "bold"),
            bg="lightgray",
            relief="raised",
            cursor="hand2"
        )
        cancel_button.pack(side=tk.RIGHT, padx=(15, 10))
        
        # 确认按钮（是）
        confirm_button = tk.Button(
            button_frame, 
            text="是", 
            command=self.on_confirm,
            width=12,
            # height=2,
            font=("Microsoft YaHei UI", 12, "bold"),
            bg="#0078d4",
            fg="white",
            relief="raised",
            cursor="hand2"
        )
        confirm_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 设置默认按钮和键盘绑定
        confirm_button.focus_set()  # 默认焦点在"是"按钮
        self.dialog.bind('<Return>', lambda e: self.on_confirm())
        self.dialog.bind('<Escape>', lambda e: self.on_cancel())
    
    def on_confirm(self):
        """确认按钮点击事件"""
        self.close_method = self.close_method_var.get()
        self.remember_choice = self.remember_var.get()
        self.result = True
        self.dialog.destroy()
    
    def on_cancel(self):
        """取消按钮点击事件"""
        self.result = False
        self.dialog.destroy()
    
    def show(self):
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return {
            'confirmed': self.result,
            'close_method': self.close_method,
            'remember': self.remember_choice
        }

def test_dialog():
    """测试对话框"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    dialog = CloseDialog(root, tray_available=True)
    result = dialog.show()
    
    logger.debug(f"对话框结果: {result}")
    
    root.destroy()

if __name__ == "__main__":
    test_dialog()