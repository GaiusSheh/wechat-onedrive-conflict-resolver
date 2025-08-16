import ctypes
from ctypes import wintypes
import time
import sys

# 导入统一日志系统
from core.logger_helper import logger

class IdleDetector:
    """Windows系统静置时间检测器"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # 预定义LASTINPUTINFO结构体，避免重复定义
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [
                ('cbSize', wintypes.UINT),
                ('dwTime', wintypes.DWORD)
            ]
        
        self.LASTINPUTINFO = LASTINPUTINFO
    
    def get_idle_time_seconds(self):
        """获取系统静置时间（秒）"""
        try:
            # 创建结构体实例（使用预定义的结构体）
            last_input_info = self.LASTINPUTINFO()
            last_input_info.cbSize = ctypes.sizeof(self.LASTINPUTINFO)
            
            # 获取最后一次输入时间
            if not self.user32.GetLastInputInfo(ctypes.byref(last_input_info)):
                return 0
            
            # 获取当前系统时间
            current_tick = self.kernel32.GetTickCount()
            
            # 计算静置时间（毫秒转秒）
            idle_time_ms = current_tick - last_input_info.dwTime
            return max(0, idle_time_ms / 1000.0)  # 确保不返回负数
            
        except Exception as e:
            logger.error(f"获取静置时间失败: {e}")
            return 0
    
    def get_idle_time_minutes(self):
        """获取系统静置时间（分钟）"""
        return self.get_idle_time_seconds() / 60.0
    
    def is_idle_for(self, minutes):
        """检查系统是否已静置指定分钟数"""
        return self.get_idle_time_minutes() >= minutes
    
    def format_idle_time(self):
        """格式化显示静置时间"""
        total_seconds = int(self.get_idle_time_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"

def test_idle_detector():
    """测试静置检测功能"""
    detector = IdleDetector()
    
    logger.info("=== 静置时间检测器测试 ===\n")
    logger.info("请移动鼠标或按键盘，然后保持静置状态观察...")
    logger.info("按 Ctrl+Z 或 Ctrl+C 退出\n")
    
    try:
        while True:
            idle_time = detector.format_idle_time()
            idle_minutes = detector.get_idle_time_minutes()
            
            # 检查是否达到常见的触发条件
            status_indicators = []
            if idle_minutes >= 1:
                status_indicators.append("[1分钟]")
            if idle_minutes >= 5:
                status_indicators.append("[5分钟]")
            if idle_minutes >= 10:
                status_indicators.append("[10分钟]")
            
            status = " ".join(status_indicators) if status_indicators else "活跃中"
            
            # 对于实时更新的debug信息，去掉end和flush参数
            logger.debug(f"静置时间: {idle_time:<20} [{status}]")
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n\n测试结束")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        detector = IdleDetector()
        
        if command == 'test':
            test_idle_detector()
        elif command == 'current':
            print(f"当前静置时间: {detector.format_idle_time()}")
        elif command == 'check':
            if len(sys.argv) > 2:
                try:
                    minutes = float(sys.argv[2])
                    if detector.is_idle_for(minutes):
                        print(f"系统已静置 {minutes} 分钟")
                        sys.exit(0)
                    else:
                        print(f"系统未达到 {minutes} 分钟静置")
                        sys.exit(1)
                except ValueError:
                    print("请提供有效的分钟数")
                    sys.exit(1)
            else:
                print("用法: python idle_detector.py check <分钟数>")
                sys.exit(1)
        else:
            print(f"未知命令: {command}")
    else:
        print("静置时间检测器")
        print("\n用法:")
        print("  python idle_detector.py test     # 实时监控静置时间")
        print("  python idle_detector.py current  # 显示当前静置时间")
        print("  python idle_detector.py check 10 # 检查是否静置10分钟")
        print("\n功能:")
        print("- 使用Windows API检测键盘鼠标活动")
        print("- 精确计算系统静置时间")
        print("- 支持自定义静置阈值检查")

if __name__ == "__main__":
    main()