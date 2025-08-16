#!/usr/bin/env python3
"""
图标GUI测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import tkinter as tk
import ttkbootstrap as ttk
from gui.icon_manager import IconManager

def test_icon_gui():
    """测试图标GUI"""
    try:
        # 创建窗口
        root = ttk.Window(themename="cosmo")
        root.title("图标测试")
        root.geometry("400x300")
        
        # 创建图标管理器
        icon_manager = IconManager()
        icons = icon_manager.get_all_icons()
        
        # 创建测试标签
        frame = ttk.Frame(root, padding="20")
        frame.pack(fill="both", expand=True)
        
        icon_names = ['wechat', 'onedrive', 'idle', 'sync', 'stats', 'cooldown']
        texts = ['微信状态:', 'OneDrive:', '空闲时间:', '上次同步:', '成功/失败:', '触发冷却:']
        
        for i, (name, text) in enumerate(zip(icon_names, texts)):
            icon = icons.get(name)
            if icon:
                label = ttk.Label(
                    frame,
                    text=text,
                    image=icon,
                    compound="left",
                    font=("Microsoft YaHei UI", 10, "bold"),
                    width=12
                )
                label.grid(row=i, column=0, sticky="w", pady=5)
                
                status_label = ttk.Label(
                    frame,
                    text="测试状态",
                    font=("Microsoft YaHei UI", 10)
                )
                status_label.grid(row=i, column=1, sticky="w", padx=(15, 0), pady=5)
            else:
                print(f"图标 {name} 加载失败")
        
        print("图标GUI测试启动...")
        root.after(3000, root.destroy)  # 3秒后自动关闭
        root.mainloop()
        
        print("图标GUI测试完成！")
        return True
        
    except Exception as e:
        print(f"图标GUI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_icon_gui()