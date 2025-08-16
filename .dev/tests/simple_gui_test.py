#!/usr/bin/env python3
"""
最简化的GUI测试 - 验证基本响应性
"""
import tkinter as tk
from tkinter import ttk
import threading
import time

class SimpleTestWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("简单GUI测试")
        self.root.geometry("400x300")
        
        # 创建简单界面
        self.create_simple_ui()
        
        print("GUI初始化完成")
    
    def create_simple_ui(self):
        """创建简单的用户界面"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="GUI响应性测试", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 计数器显示
        self.counter_label = ttk.Label(main_frame, text="计数器: 0", font=("Arial", 12))
        self.counter_label.grid(row=1, column=0, pady=(0, 10))
        
        # 测试按钮
        test_button = ttk.Button(main_frame, text="点击测试响应", command=self.test_click)
        test_button.grid(row=2, column=0, pady=(0, 10))
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, text="状态: 就绪", foreground="green")
        self.status_label.grid(row=3, column=0)
        
        # 启动简单的计数器线程（测试线程安全）
        self.counter = 0
        self.start_counter_thread()
    
    def test_click(self):
        """测试按钮点击响应"""
        self.status_label.config(text="状态: 按钮被点击!", foreground="blue")
        self.root.after(2000, lambda: self.status_label.config(text="状态: 就绪", foreground="green"))
        print("按钮点击响应正常")
    
    def start_counter_thread(self):
        """启动计数器线程（线程安全方式）"""
        def counter_loop():
            while True:
                try:
                    time.sleep(1)
                    self.counter += 1
                    # 使用root.after线程安全地更新GUI
                    self.root.after(0, self.update_counter_display)
                except Exception as e:
                    print(f"计数器线程出错: {e}")
                    break
        
        thread = threading.Thread(target=counter_loop, daemon=True)
        thread.start()
        print("计数器线程已启动")
    
    def update_counter_display(self):
        """线程安全地更新计数器显示"""
        try:
            self.counter_label.config(text=f"计数器: {self.counter}")
        except Exception as e:
            print(f"更新计数器显示出错: {e}")
    
    def run(self):
        """运行GUI"""
        try:
            print("开始运行GUI...")
            self.root.mainloop()
        except Exception as e:
            print(f"运行GUI出错: {e}")
        finally:
            print("GUI已关闭")

def main():
    """主函数"""
    print("启动简化GUI测试...")
    app = SimpleTestWindow()
    app.run()

if __name__ == "__main__":
    main()