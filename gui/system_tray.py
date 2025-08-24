#!/usr/bin/env python3
"""
微信OneDrive冲突解决工具 - 系统托盘支持
"""

try:
    import pystray
    from pystray import Menu, MenuItem
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    # logger.warning("pystray模块未安装，系统托盘功能不可用")

import threading
import time
from datetime import datetime
import sys
import os

# 添加core模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from core.logger_helper import logger

# 导入性能调试系统
from core.performance_debug import (
    measure_time, perf_log, log_user_action, log_gui_update, 
    log_system_call, perf_timer, PERFORMANCE_DEBUG_ENABLED
)

class SystemTray:
    """系统托盘管理类"""
    
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.icon = None
        self.is_running = False
        
        if not TRAY_AVAILABLE:
            return
    
    def _get_resource_path(self, relative_path):
        """获取正确的资源文件路径，支持打包后的exe环境"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe环境
            bundle_dir = sys._MEIPASS
            bundle_path = os.path.join(bundle_dir, relative_path)
            
            # 如果bundle中不存在，尝试exe同目录
            if not os.path.exists(bundle_path):
                exe_dir = os.path.dirname(sys.executable)
                exe_path = os.path.join(exe_dir, relative_path)
                return exe_path
            return bundle_path
        else:
            # 开发环境
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, relative_path)

    def create_icon_image(self, color="blue"):
        """创建托盘图标"""
        try:
            # 尝试使用main图标作为托盘图标
            main_icon_path = self._get_resource_path("gui/resources/downloads/main_transp_bg.png")
            if os.path.exists(main_icon_path):
                # 加载main图标
                image = Image.open(main_icon_path)
                
                # 缩放到64x64像素（托盘图标大小）
                image = image.resize((64, 64), Image.Resampling.LANCZOS)
                
                # 确保为RGBA模式
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                
                # 根据状态添加颜色覆盖效果（可选）
                if color != "blue":  # blue为默认状态，不需要修改
                    # 创建颜色叠加层
                    overlay = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(overlay)
                    
                    # 根据状态添加边框或背景色调
                    if color == "green":
                        # 成功状态 - 绿色边框
                        draw.rectangle((0, 0, 63, 63), outline='green', width=3)
                    elif color == "red":
                        # 错误状态 - 红色边框
                        draw.rectangle((0, 0, 63, 63), outline='red', width=3)
                    elif color == "orange":
                        # 运行中状态 - 橙色边框
                        draw.rectangle((0, 0, 63, 63), outline='orange', width=3)
                    
                    # 合成图像
                    image = Image.alpha_composite(image, overlay)
                
                return image
                
        except Exception as e:
            # 如果加载main图标失败，回退到原来的简单图标
            logger.warning(f"无法加载main图标，使用备用图标: {e}")
        
        # 备用方案：创建一个简单的图标
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        
        if color == "blue":
            # 正常状态 - 蓝色圆圈
            draw.ellipse((8, 8, 56, 56), fill='blue', outline='darkblue', width=2)
        elif color == "green":
            # 成功状态 - 绿色圆圈
            draw.ellipse((8, 8, 56, 56), fill='green', outline='darkgreen', width=2)
        elif color == "red":
            # 错误状态 - 红色圆圈
            draw.ellipse((8, 8, 56, 56), fill='red', outline='darkred', width=2)
        elif color == "orange":
            # 运行中状态 - 橙色圆圈
            draw.ellipse((8, 8, 56, 56), fill='orange', outline='darkorange', width=2)
        
        # 添加字母W标识
        draw.text((28, 20), "W", fill='white', anchor="mm")
        
        return image
    
    def create_menu(self):
        """创建托盘菜单"""
        if not TRAY_AVAILABLE:
            return None
            
        menu_items = [
            MenuItem("显示主窗口", lambda: self.show_window(), default=True),  # 设为默认项
            Menu.SEPARATOR,
            MenuItem("立即执行同步", lambda: self.run_sync()),
            Menu.SEPARATOR,
            MenuItem("微信状态", lambda: self.show_wechat_status()),
            MenuItem("OneDrive状态", lambda: self.show_onedrive_status()),
            Menu.SEPARATOR,
            MenuItem("退出", lambda: self.quit_application())
        ]
        
        return Menu(*menu_items)
    
    def start_tray(self):
        """启动系统托盘"""
        if not TRAY_AVAILABLE:
            return False
        
        if self.is_running:
            return True  # 已经在运行
        
        try:
            image = self.create_icon_image()
            menu = self.create_menu()
            
            self.icon = pystray.Icon(
                "WeChatOneDriveTool",
                image,
                "微信OneDrive冲突解决工具",
                menu,
                default_action=lambda: self.show_window()  # 设置双击默认动作
            )
            
            # 在新线程中运行托盘
            def run_tray():
                try:
                    self.is_running = True
                    self.icon.run()
                except Exception as e:
                    logger.error(f"系统托盘运行出错: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    self.is_running = False
            
            tray_thread = threading.Thread(target=run_tray, daemon=True)
            tray_thread.start()
            
            # 等待托盘启动并检查状态
            import time
            for i in range(20):  # 最多等待2秒
                time.sleep(0.1)
                if self.is_running:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"启动系统托盘失败: {e}")
            import traceback
            traceback.print_exc()
            self.is_running = False
            return False
    
    def stop_tray(self, timeout=2.0):
        """停止系统托盘（支持超时控制，修复关机时的阻塞问题）"""
        if self.icon and self.is_running:
            try:
                logger.info("正在停止系统托盘...")
                
                # 设置停止标志
                self.is_running = False
                
                # 使用线程来停止托盘，避免阻塞
                import threading
                import time
                
                def stop_icon():
                    try:
                        if self.icon:
                            self.icon.stop()
                    except Exception as e:
                        logger.warning(f"托盘图标停止时出错: {e}")
                
                # 启动停止线程
                stop_thread = threading.Thread(target=stop_icon, daemon=True)
                stop_thread.start()
                
                # 等待停止完成，但不超过指定超时时间
                stop_thread.join(timeout=timeout)
                
                if stop_thread.is_alive():
                    logger.warning(f"系统托盘停止超时({timeout}秒)，强制继续")
                else:
                    logger.info("系统托盘已成功停止")
                    
            except Exception as e:
                logger.error(f"停止系统托盘出错: {e}")
            finally:
                # 确保状态被清理
                self.is_running = False
                self.icon = None
    
    def update_icon_status(self, status="normal"):
        """更新托盘图标状态"""
        if not self.icon or not TRAY_AVAILABLE:
            return
        
        try:
            color_map = {
                "normal": "blue",
                "running": "orange", 
                "success": "green",
                "error": "red"
            }
            
            status_text_map = {
                "normal": "微信OneDrive工具 - 就绪",
                "running": "微信OneDrive工具 - 同步中...",
                "success": "微信OneDrive工具 - 同步成功",
                "error": "微信OneDrive工具 - 同步失败"
            }
            
            color = color_map.get(status, "blue")
            new_image = self.create_icon_image(color)
            self.icon.icon = new_image
            
            # 更新工具提示文本
            tooltip_text = status_text_map.get(status, "微信OneDrive工具")
            self.icon.title = tooltip_text
            
        except Exception as e:
            logger.error(f"更新托盘图标出错: {e}")
    
    def show_notification(self, title, message, timeout=3):
        """显示系统通知"""
        if not self.icon or not TRAY_AVAILABLE:
            return
        
        try:
            self.icon.notify(message, title)
        except Exception as e:
            logger.error(f"显示通知出错: {e}")
    
    @measure_time("SystemTray", "显示主窗口")
    def show_window(self, icon=None, item=None):
        """显示主窗口"""
        # PERFORMANCE: 记录用户双击托盘图标操作
        log_user_action("SystemTray", "双击托盘图标")
        
        if self.main_window:
            try:
                self.main_window.restore_from_tray()
            except Exception as e:
                logger.error(f"显示主窗口出错: {e}")
    
    @measure_time("SystemTray", "托盘同步流程")
    def run_sync(self, icon=None, item=None):
        """执行同步流程"""
        # PERFORMANCE: 记录用户点击托盘同步菜单
        log_user_action("SystemTray", "托盘同步菜单点击")
        
        if self.main_window:
            try:
                self.show_notification("同步流程", "开始执行微信OneDrive同步流程...")
                self.main_window.run_sync_workflow()
            except Exception as e:
                logger.error(f"执行同步流程出错: {e}")
    
    def show_wechat_status(self, icon=None, item=None):
        """显示微信状态"""
        try:
            from core.wechat_controller import is_wechat_running, find_wechat_processes
            if is_wechat_running():
                processes = find_wechat_processes()
                message = f"微信正在运行 ({len(processes)}个进程)"
            else:
                message = "微信未运行"
            
            self.show_notification("微信状态", message)
        except Exception as e:
            logger.error(f"检查微信状态出错: {e}")
    
    def show_onedrive_status(self, icon=None, item=None):
        """显示OneDrive状态"""
        try:
            from core.onedrive_controller import is_onedrive_running
            if is_onedrive_running():
                message = "OneDrive正在运行"
            else:
                message = "OneDrive未运行"
            
            self.show_notification("OneDrive状态", message)
        except Exception as e:
            logger.error(f"检查OneDrive状态出错: {e}")
    
    def quit_application(self, icon=None, item=None):
        """退出应用程序"""
        if self.main_window:
            # 检查是否是系统关机场景，如果是则使用快速退出
            try:
                import psutil
                # 简单检测：如果系统负载很高，可能是关机场景
                cpu_percent = psutil.cpu_percent(interval=0.1)
                if cpu_percent > 80:
                    # 系统负载高，可能是关机，使用快速退出
                    self.main_window.force_exit()
                else:
                    # 正常用户操作，使用标准退出
                    self.main_window.exit_application()
            except:
                # 如果检测失败，使用标准退出
                self.main_window.exit_application()
        else:
            self.stop_tray(timeout=1.0)  # 缩短托盘停止超时时间

# 安装指南
def check_tray_dependencies():
    """检查托盘依赖"""
    missing_packages = []
    
    try:
        import pystray
    except ImportError:
        missing_packages.append("pystray")
    
    try:
        import PIL
    except ImportError:
        missing_packages.append("Pillow")
    
    if missing_packages:
        logger.info("系统托盘功能需要以下额外依赖包:")
        for package in missing_packages:
            logger.info(f"  pip install {package}")
        return False
    
    return True

if __name__ == "__main__":
    # 测试托盘功能
    if check_tray_dependencies():
        logger.info("托盘依赖检查通过")
        tray = SystemTray()
        tray.start_tray()
        
        try:
            while tray.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("手动停止")
            tray.stop_tray()
    else:
        logger.error("托盘依赖检查失败")