#!/usr/bin/env python3
"""
响应性测试脚本 - 验证GUI修复效果
"""
import sys
import time
import threading
from gui.main_window import MainWindow

def test_responsiveness():
    """测试GUI响应性，避免无限运行"""
    print("开始响应性测试...")
    
    try:
        # 创建主窗口实例
        app = MainWindow()
        
        # 启动定时器，30秒后自动关闭
        def auto_close():
            time.sleep(30)
            print("测试完成，正在关闭应用...")
            try:
                app.root.quit()
                app.root.destroy()
            except:
                pass
        
        close_thread = threading.Thread(target=auto_close, daemon=True)
        close_thread.start()
        
        print("GUI已启动，测试30秒后自动关闭...")
        print("请在此期间测试:")
        print("1. 空闲时间是否正常计数")
        print("2. 鼠标移动后是否在3秒内重置")
        print("3. GUI界面是否保持响应")
        
        # 运行GUI
        app.run()
        
    except KeyboardInterrupt:
        print("测试被用户中断")
    except Exception as e:
        print(f"测试过程中出错: {e}")
    finally:
        print("响应性测试结束")

if __name__ == "__main__":
    test_responsiveness()