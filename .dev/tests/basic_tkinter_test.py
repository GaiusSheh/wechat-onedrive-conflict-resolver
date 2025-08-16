#!/usr/bin/env python3
"""
最基础的tkinter测试 - 无任何线程或复杂逻辑
"""
import tkinter as tk
from tkinter import ttk

def test_click():
    """测试按钮点击"""
    print("按钮被点击了！")
    label.config(text="按钮被点击了！")

def main():
    """最基础的GUI测试"""
    print("创建基础tkinter窗口...")
    
    root = tk.Tk()
    root.title("基础GUI测试")
    root.geometry("300x200")
    
    # 创建简单控件
    global label
    label = ttk.Label(root, text="GUI测试 - 点击下面按钮")
    label.pack(pady=20)
    
    button = ttk.Button(root, text="测试按钮", command=test_click)
    button.pack(pady=10)
    
    print("开始运行GUI...")
    root.mainloop()
    print("GUI已关闭")

if __name__ == "__main__":
    main()