#!/usr/bin/env python3
"""
GUI图标管理器 - 缩放高清图标为30x30像素用于GUI界面
"""

from PIL import Image
import tkinter as tk
import os
import sys

# 添加core模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.logger_helper import logger

class IconManager:
    """图标管理器 - 专门用于缩放高清图标"""
    
    def __init__(self):
        self.icons = {}
        self.icon_size = (30, 30)  # 30x30像素图标大小
        self.downloads_dir = self._get_resource_path("gui/resources/downloads")  # 高清图标源目录
        self.icons_dir = self._get_resource_path("gui/resources/icons")  # 30x30图标目标目录
        
        # 确保目录存在（仅在开发环境）
        if not getattr(sys, 'frozen', False):
            os.makedirs(self.downloads_dir, exist_ok=True)
            os.makedirs(self.icons_dir, exist_ok=True)
    
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
    
    def resize_icon(self, source_file, target_file):
        """将单个图标缩放为30x30"""
        try:
            with Image.open(source_file) as img:
                # 使用高质量重采样算法
                resized_img = img.resize(self.icon_size, Image.Resampling.LANCZOS)
                
                # 如果原图有透明通道，保持透明通道
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    resized_img = resized_img.convert('RGBA')
                
                # 保存缩放后的图标
                resized_img.save(target_file, 'PNG')
                logger.info(f"成功缩放: {os.path.basename(source_file)} -> 30x30")
                return True
        except Exception as e:
            logger.error(f"缩放失败 {source_file}: {e}")
            return False
    
    def resize_all_icons(self):
        """缩放所有高清图标为30x30像素"""
        if not os.path.exists(self.downloads_dir):
            logger.error(f"源目录不存在: {self.downloads_dir}")
            return False
        
        # 获取所有PNG文件
        icon_files = [f for f in os.listdir(self.downloads_dir) if f.lower().endswith('.png')]
        
        if not icon_files:
            logger.warning(f"在 {self.downloads_dir} 中没有找到PNG图标文件")
            return False
        
        success_count = 0
        for filename in icon_files:
            source_path = os.path.join(self.downloads_dir, filename)
            target_path = os.path.join(self.icons_dir, filename)
            
            if self.resize_icon(source_path, target_path):
                success_count += 1
        
        logger.info(f"图标缩放完成: 成功 {success_count}/{len(icon_files)}")
        return success_count == len(icon_files)
    
    def load_icon(self, icon_name):
        """加载图标为PhotoImage对象"""
        if icon_name in self.icons:
            return self.icons[icon_name]
        
        # 使用绝对路径，确保打包后能找到
        filepath = os.path.join(self.icons_dir, f"{icon_name}.png")
        logger.info(f"尝试加载图标: {icon_name}, 路径: {filepath}")
        logger.info(f"图标文件存在: {os.path.exists(filepath)}")
        
        if os.path.exists(filepath):
            try:
                # 加载为PhotoImage
                photo = tk.PhotoImage(file=filepath)
                self.icons[icon_name] = photo
                logger.info(f"成功加载图标: {icon_name}")
                return photo
            except Exception as e:
                logger.error(f"加载图标失败 {icon_name}: {e}")
                return None
        
        logger.warning(f"图标文件不存在: {filepath}")
        return None
    
    def get_all_icons(self):
        """获取所有图标的PhotoImage对象"""
        icon_names = ['wechat', 'onedrive', 'idle', 'sync', 'stats', 'cooldown', 'main']
        icons = {}
        
        for name in icon_names:
            icons[name] = self.load_icon(name)
        
        return icons
    
    def list_available_icons(self):
        """列出可用的图标文件"""
        downloads_icons = []
        if os.path.exists(self.downloads_dir):
            downloads_icons = [f for f in os.listdir(self.downloads_dir) if f.lower().endswith('.png')]
        
        resized_icons = []
        if os.path.exists(self.icons_dir):
            resized_icons = [f for f in os.listdir(self.icons_dir) if f.lower().endswith('.png')]
        
        logger.info(f"高清图标 ({self.downloads_dir}): {downloads_icons}")
        logger.info(f"30x30图标 ({self.icons_dir}): {resized_icons}")
        
        return downloads_icons, resized_icons

# 测试函数
def test_icon_manager():
    """测试图标管理器"""
    logger.info("测试图标管理器")
    
    manager = IconManager()
    
    # 列出可用图标
    downloads, resized = manager.list_available_icons()
    
    # 缩放所有图标
    if downloads:
        logger.info("开始缩放高清图标...")
        success = manager.resize_all_icons()
        if success:
            logger.info("✓ 所有图标缩放成功")
        else:
            logger.error("✗ 部分图标缩放失败")
    else:
        logger.warning("没有找到高清图标文件")

if __name__ == "__main__":
    test_icon_manager()