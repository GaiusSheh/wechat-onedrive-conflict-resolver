#!/usr/bin/env python3
"""
现代化GUI测试脚本
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_ttkbootstrap_import():
    """测试ttkbootstrap导入"""
    try:
        import ttkbootstrap as ttk
        print("ttkbootstrap导入成功")
        
        # 测试可用主题
        style = ttk.Style()
        themes = style.theme_names()
        print(f"可用主题：{themes}")
        return True
    except ImportError as e:
        print(f"ttkbootstrap导入失败：{e}")
        return False

def test_simple_modern_window():
    """测试简单的现代化窗口"""
    try:
        import ttkbootstrap as ttk
        
        # 创建测试窗口
        root = ttk.Window(themename="cosmo")
        root.title("现代化GUI测试")
        root.geometry("400x300")
        
        # 测试现代化组件
        header_label = ttk.Label(
            root,
            text="现代化GUI测试",
            font=("Microsoft YaHei UI", 14, "bold"),
            bootstyle="primary"
        )
        header_label.pack(pady=20)
        
        # 测试卡片样式
        card = ttk.LabelFrame(
            root,
            text="测试卡片",
            padding="20",
            bootstyle="success"
        )
        card.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(
            card,
            text="现代化界面组件正常工作！",
            bootstyle="success"
        ).pack()
        
        # 测试按钮样式
        ttk.Button(
            root,
            text="测试按钮",
            bootstyle="success",
            width=15
        ).pack(pady=10)
        
        print("现代化GUI组件测试成功")
        
        # 显示窗口2秒后自动关闭
        root.after(2000, root.destroy)
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"现代化GUI测试失败：{e}")
        return False

def main():
    """主测试函数"""
    print("开始现代化GUI测试...")
    
    success_count = 0
    total_tests = 2
    
    # 测试1：导入测试
    if test_ttkbootstrap_import():
        success_count += 1
    
    # 测试2：界面测试
    if test_simple_modern_window():
        success_count += 1
    
    # 结果统计
    print(f"\n测试结果：{success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("所有现代化GUI测试通过！")
        return True
    else:
        print("部分测试失败，请检查环境配置")
        return False

if __name__ == "__main__":
    main()