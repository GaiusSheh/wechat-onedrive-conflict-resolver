#!/usr/bin/env python3
"""
微信OneDrive冲突解决工具 - GUI启动器
v4.0版本：支持命令行参数和最小化启动
"""

import sys
import os
import argparse

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入统一日志系统
from core.logger_helper import logger

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='微信OneDrive冲突解决工具 v4.0')
    parser.add_argument('--start-minimized', action='store_true', 
                      help='启动时最小化到系统托盘')
    parser.add_argument('--hidden', action='store_true',
                      help='完全隐藏启动（仅托盘模式）')
    # 动态读取版本号
    try:
        from core.version_helper import version_helper
        version_str = f'%(prog)s {version_helper.get_version()}'
    except:
        version_str = '%(prog)s 4.1'  # 备用版本号
    
    parser.add_argument('--version', action='version', version=version_str)
    
    return parser.parse_args()

def main_with_args():
    """带参数的主函数"""
    args = parse_arguments()
    
    # 记录启动信息
    if args.start_minimized or args.hidden:
        logger.system_status("GUI应用", "最小化启动", "微信OneDrive冲突解决工具")
    else:
        logger.system_status("GUI应用", "正常启动", "微信OneDrive冲突解决工具")
    
    try:
        # 导入主窗口类
        from gui.main_window import MainWindow
        from gui.system_tray import SystemTray, TRAY_AVAILABLE
        from core.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        # 检查是否需要最小化启动
        start_minimized = (args.start_minimized or args.hidden or 
                          config_manager.get('startup.minimize_to_tray', False))
        
        system_tray = None
        if start_minimized and TRAY_AVAILABLE:
            # 先创建SystemTray
            system_tray = SystemTray()  # 先创建无main_window的实例
        
        # 创建主窗口，传入system_tray
        main_window = MainWindow(system_tray=system_tray)
        
        # 如果创建了system_tray，设置main_window引用
        if system_tray:
            system_tray.main_window = main_window
        
        if start_minimized and TRAY_AVAILABLE and system_tray:
            # 启动托盘
            if system_tray.start_tray():
                # 托盘启动成功，隐藏主窗口
                main_window.root.withdraw()  # 隐藏窗口
                main_window.log_message("程序已最小化到系统托盘启动", "INFO")
                
                # 如果是完全隐藏模式，不显示任何界面
                if not args.hidden:
                    # 可以添加一个简单的提示
                    pass
            else:
                # 托盘启动失败，显示主窗口
                main_window.log_message("系统托盘启动失败，显示主窗口", "WARNING")
                main_window.root.deiconify()
                main_window.root.lift()
        else:
            # 正常启动，显示主窗口
            main_window.root.deiconify()
            main_window.root.lift()
            
            if start_minimized and not TRAY_AVAILABLE:
                main_window.log_message("系统托盘不可用，无法最小化启动", "WARNING")
        
        # 运行主循环
        if hasattr(main_window, 'root'):
            main_window.root.mainloop()
        else:
            main_window.mainloop()
            
    except ImportError as e:
        logger.error(f"导入GUI模块失败: {e}")
        logger.info("请确保已安装所需的依赖包")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动GUI失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main_with_args()