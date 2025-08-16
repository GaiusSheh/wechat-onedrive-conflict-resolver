#!/usr/bin/env python3
"""
微信自动登录工具
使用Windows UI自动化API来检测微信登录界面并自动点击登录按钮
"""

import time
import ctypes
from ctypes import wintypes
import psutil
from wechat_controller import find_wechat_processes

# 导入统一日志系统
from core.logger_helper import logger

# Windows API constants
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_CHAR = 0x0102
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

class WeChatAutoLogin:
    """微信自动登录处理器"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
    def find_wechat_windows(self):
        """查找微信窗口"""
        windows = []
        
        def enum_windows_callback(hwnd, lparam):
            """窗口枚举回调函数"""
            # 获取窗口标题
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buffer, length + 1)
                window_title = buffer.value
                
                # 获取窗口类名
                class_buffer = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(hwnd, class_buffer, 256)
                class_name = class_buffer.value
                
                # 检查是否为微信窗口
                if self._is_wechat_window(window_title, class_name, hwnd):
                    # 获取窗口进程ID
                    process_id = wintypes.DWORD()
                    self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                    
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_title,
                        'class': class_name,
                        'pid': process_id.value,
                        'visible': bool(self.user32.IsWindowVisible(hwnd))
                    })
            
            return True
        
        # 枚举所有窗口
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
        
        return windows
    
    def _is_wechat_window(self, title, class_name, hwnd):
        """判断是否为微信相关窗口"""
        # 微信主窗口通常标题包含"微信"
        wechat_indicators = [
            "微信", "WeChat", "登录", "Login"
        ]
        
        # 检查标题
        for indicator in wechat_indicators:
            if indicator in title:
                return True
        
        # 检查类名（微信的常见窗口类名）
        wechat_classes = [
            "WeChatMainWndForPC",  # 微信主窗口
            "WeUIDialog",          # 微信对话框
            "Chrome_RenderWidgetHostHWND"  # 微信内嵌浏览器
        ]
        
        for wechat_class in wechat_classes:
            if wechat_class in class_name:
                return True
        
        return False
    
    def find_login_button(self, hwnd):
        """在指定窗口中查找登录按钮"""
        buttons = []
        
        def enum_child_callback(child_hwnd, lparam):
            """子窗口枚举回调"""
            # 获取控件类名
            class_buffer = ctypes.create_unicode_buffer(256)
            self.user32.GetClassNameW(child_hwnd, class_buffer, 256)
            class_name = class_buffer.value
            
            # 获取控件文本
            length = self.user32.GetWindowTextLengthW(child_hwnd)
            text = ""
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(child_hwnd, buffer, length + 1)
                text = buffer.value
            
            # 检查是否为按钮控件
            if ("Button" in class_name or "button" in class_name.lower() or 
                "登录" in text or "Login" in text or "进入" in text):
                
                # 获取按钮位置
                rect = wintypes.RECT()
                if self.user32.GetWindowRect(child_hwnd, ctypes.byref(rect)):
                    buttons.append({
                        'hwnd': child_hwnd,
                        'text': text,
                        'class': class_name,
                        'rect': (rect.left, rect.top, rect.right, rect.bottom),
                        'visible': bool(self.user32.IsWindowVisible(child_hwnd)),
                        'enabled': bool(self.user32.IsWindowEnabled(child_hwnd))
                    })
            
            return True
        
        # 枚举子窗口
        EnumChildProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumChildWindows(hwnd, EnumChildProc(enum_child_callback), 0)
        
        return buttons
    
    def click_button(self, hwnd, x=None, y=None):
        """点击按钮"""
        try:
            if x is None or y is None:
                # 获取窗口中心点
                rect = wintypes.RECT()
                if not self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    return False
                x = (rect.left + rect.right) // 2
                y = (rect.top + rect.bottom) // 2
            
            # 将窗口带到前台
            self.user32.SetForegroundWindow(hwnd)
            time.sleep(0.1)
            
            # 发送鼠标点击消息
            lParam = (y << 16) | x
            self.user32.SendMessageW(hwnd, WM_LBUTTONDOWN, 1, lParam)
            time.sleep(0.05)
            self.user32.SendMessageW(hwnd, WM_LBUTTONUP, 0, lParam)
            
            logger.debug(f"已点击按钮位置: ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"点击按钮失败: {e}")
            return False
    
    def detect_and_login(self, timeout=30):
        """检测登录界面并自动登录"""
        logger.info("正在检测微信登录界面...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查微信是否在运行
            if not find_wechat_processes():
                print("微信未运行，跳过自动登录")
                return False
            
            # 查找微信窗口
            windows = self.find_wechat_windows()
            if not windows:
                print("未找到微信窗口")
                time.sleep(1)
                continue
            
            print(f"找到 {len(windows)} 个微信窗口")
            
            # 检查每个窗口
            for window in windows:
                # 如果窗口不可见，尝试恢复显示
                if not window['visible']:
                    print(f"窗口 '{window['title']}' 不可见，尝试恢复显示...")
                    self.user32.ShowWindow(window['hwnd'], 9)  # SW_RESTORE
                    self.user32.SetForegroundWindow(window['hwnd'])
                    time.sleep(0.5)
                    # 重新检查可见性
                    if not self.user32.IsWindowVisible(window['hwnd']):
                        print(f"无法恢复窗口 '{window['title']}'")
                        continue
                
                print(f"检查窗口: {window['title']} (类名: {window['class']})")
                
                # 查找登录按钮
                buttons = self.find_login_button(window['hwnd'])
                
                if buttons:
                    print(f"找到 {len(buttons)} 个可能的登录按钮:")
                    for i, button in enumerate(buttons):
                        print(f"  {i+1}. 文本: '{button['text']}', 类名: {button['class']}")
                        if button['visible'] and button['enabled']:
                            print(f"     位置: {button['rect']}")
                    
                    # 选择最佳的登录按钮
                    login_button = self._select_best_login_button(buttons)
                    if login_button:
                        print(f"尝试点击登录按钮: '{login_button['text']}'")
                        
                        # 计算按钮中心点（相对于按钮窗口）
                        rect = login_button['rect']
                        center_x = (rect[0] + rect[2]) // 2
                        center_y = (rect[1] + rect[3]) // 2
                        
                        if self.click_button(login_button['hwnd'], center_x, center_y):
                            print("[OK] 自动登录点击已发送")
                            return True
                        else:
                            # 尝试直接点击窗口
                            if self.click_button(window['hwnd']):
                                print("[OK] 尝试点击主窗口")
                                return True
            
            # 等待一秒再重试
            time.sleep(1)
        
        print(f"[!] 在 {timeout} 秒内未检测到登录界面")
        return False
    
    def _select_best_login_button(self, buttons):
        """选择最佳的登录按钮"""
        if not buttons:
            return None
        
        # 过滤可见且可用的按钮
        visible_buttons = [btn for btn in buttons if btn['visible'] and btn['enabled']]
        if not visible_buttons:
            return None
        
        # 优先选择包含"登录"或"Login"的按钮
        for button in visible_buttons:
            text = button['text'].lower()
            if "登录" in text or "login" in text:
                return button
        
        # 其次选择包含"进入"的按钮
        for button in visible_buttons:
            if "进入" in button['text']:
                return button
        
        # 返回第一个可用按钮
        return visible_buttons[0]
    
    def wait_for_login_completion(self, timeout=10):
        """等待登录完成"""
        print("等待登录完成...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            windows = self.find_wechat_windows()
            
            # 检查是否出现主界面
            for window in windows:
                if window['visible'] and "微信" in window['title']:
                    # 检查是否不再有登录按钮
                    buttons = self.find_login_button(window['hwnd'])
                    login_buttons = [btn for btn in buttons 
                                   if "登录" in btn['text'] or "Login" in btn['text']]
                    
                    if not login_buttons:
                        print("[OK] 登录已完成")
                        return True
            
            time.sleep(0.5)
        
        print("[!] 登录完成检测超时")
        return False

def auto_login_after_restart():
    """在微信重启后自动登录"""
    auto_login = WeChatAutoLogin()
    
    print("=" * 50)
    print("微信自动登录工具")
    print("=" * 50)
    
    # 等待微信启动
    print("等待微信启动...")
    time.sleep(3)
    
    # 检测并登录
    if auto_login.detect_and_login(timeout=30):
        # 等待登录完成
        auto_login.wait_for_login_completion()
        return True
    else:
        print("[X] 自动登录失败，可能需要手动登录")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 测试模式
        auto_login = WeChatAutoLogin()
        
        print("=== 微信窗口检测测试 ===")
        windows = auto_login.find_wechat_windows()
        
        if windows:
            print(f"找到 {len(windows)} 个微信窗口:")
            for i, window in enumerate(windows):
                print(f"  {i+1}. 标题: '{window['title']}'")
                print(f"      类名: {window['class']}")
                print(f"      可见: {window['visible']}")
                print(f"      PID: {window['pid']}")
                
                if window['visible']:
                    buttons = auto_login.find_login_button(window['hwnd'])
                    if buttons:
                        print(f"      发现 {len(buttons)} 个按钮:")
                        for btn in buttons[:3]:  # 只显示前3个
                            print(f"        - '{btn['text']}' ({btn['class']})")
                print()
        else:
            print("未找到微信窗口")
    else:
        # 正常运行
        auto_login_after_restart()