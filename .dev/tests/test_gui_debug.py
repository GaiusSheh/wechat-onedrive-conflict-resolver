#!/usr/bin/env python3
"""
GUI调试测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_basic_gui():
    """测试基本GUI创建"""
    try:
        # 导入GUI模块
        from gui.main_window import MainWindow
        
        print("开始创建MainWindow实例...")
        app = MainWindow()
        
        print("MainWindow创建成功！")
        print(f"Root窗口: {app.root}")
        print(f"Root几何: {app.root.geometry()}")
        
        # 检查是否有组件
        children = app.root.winfo_children()
        print(f"子组件数量: {len(children)}")
        
        if len(children) == 0:
            print("警告：窗口没有任何子组件！")
            return False
        
        # 显示2秒后关闭
        app.root.after(2000, app.root.destroy)
        app.root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"GUI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始GUI调试测试...")
    success = test_basic_gui()
    if success:
        print("GUI调试测试成功")
    else:
        print("GUI调试测试失败")