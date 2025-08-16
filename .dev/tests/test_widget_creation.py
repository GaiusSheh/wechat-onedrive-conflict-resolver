#!/usr/bin/env python3
"""
组件创建调试测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_widget_creation():
    """测试组件创建过程"""
    try:
        import ttkbootstrap as ttk
        
        print("创建ttkbootstrap窗口...")
        root = ttk.Window(themename="cosmo")
        root.title("组件创建测试")
        root.geometry("800x600")
        
        print("创建主容器...")
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        print("配置网格权重...")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        print("创建头部...")
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        title_label = ttk.Label(
            header_frame, 
            text="微信OneDrive冲突解决工具",
            font=("Microsoft YaHei UI", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack()
        
        print("创建测试卡片...")
        card = ttk.LabelFrame(
            main_frame,
            text="测试卡片",
            padding="20",
            bootstyle="success"
        )
        card.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        ttk.Label(card, text="这是一个测试标签").pack()
        ttk.Button(card, text="测试按钮", bootstyle="success").pack(pady=10)
        
        print("检查窗口状态...")
        print(f"窗口几何: {root.geometry()}")
        print(f"主容器子组件: {len(main_frame.winfo_children())}")
        
        # 强制更新窗口
        root.update()
        print(f"更新后窗口几何: {root.geometry()}")
        
        # 显示3秒
        root.after(3000, root.destroy)
        root.mainloop()
        
        print("测试完成！")
        return True
        
    except Exception as e:
        print(f"组件创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始组件创建调试...")
    test_widget_creation()