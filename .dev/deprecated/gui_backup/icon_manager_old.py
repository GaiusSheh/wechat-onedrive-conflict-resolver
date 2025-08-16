#!/usr/bin/env python3
"""
GUI图标管理器 - 创建和管理界面图标
"""

from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import ttk
import os
import sys

# 添加core模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.logger_helper import logger

class IconManager:
    """图标管理器"""
    
    def __init__(self):
        self.icons = {}
        self.icon_size = (30, 30)  # 30x30像素图标大小
        self.icons_dir = "gui/resources/icons"
        
        # 确保图标目录存在
        os.makedirs(self.icons_dir, exist_ok=True)
    
    def create_simple_icon(self, text, bg_color, text_color="white", filename=None):
        """创建简单的文字图标"""
        img = Image.new('RGBA', self.icon_size, bg_color)
        draw = ImageDraw.Draw(img)
        
        # 尝试使用系统字体
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # 计算文字位置（居中）
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.icon_size[0] - text_width) // 2
        y = (self.icon_size[1] - text_height) // 2  # 完全居中对齐
        
        draw.text((x, y), text, fill=text_color, font=font)
        
        if filename:
            filepath = os.path.join(self.icons_dir, filename)
            img.save(filepath, "PNG")
        
        return img
    
    def create_colored_circle(self, color, filename=None):
        """创建彩色圆形图标"""
        img = Image.new('RGBA', self.icon_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 画圆形
        margin = 2
        draw.ellipse([margin, margin, self.icon_size[0]-margin, self.icon_size[1]-margin], 
                    fill=color, outline=color)
        
        if filename:
            filepath = os.path.join(self.icons_dir, filename)
            img.save(filepath, "PNG")
        
        return img
    
    def create_icons(self):
        """创建所有需要的图标"""
        # 微信图标 - 绿色背景
        self.create_simple_icon("微", "#07C160", "white", "wechat.png")
        
        # OneDrive图标 - 蓝色背景  
        self.create_simple_icon("云", "#0078D4", "white", "onedrive.png")
        
        # 空闲时间图标 - 紫色背景
        self.create_simple_icon("时", "#6A4C93", "white", "idle.png")
        
        # 同步图标 - 橙色背景
        self.create_simple_icon("同", "#FF8C00", "white", "sync.png")
        
        # 统计图标 - 绿色背景
        self.create_simple_icon("统", "#28A745", "white", "stats.png")
        
        # 冷却图标 - 青色背景
        self.create_simple_icon("冷", "#17A2B8", "white", "cooldown.png")
        
        logger.info("图标创建完成")
    
    def load_icon(self, icon_name):
        """加载图标为PhotoImage对象"""
        if icon_name in self.icons:
            return self.icons[icon_name]
        
        filepath = os.path.join(self.icons_dir, f"{icon_name}.png")
        if os.path.exists(filepath):
            # 加载为PhotoImage
            photo = tk.PhotoImage(file=filepath)
            self.icons[icon_name] = photo
            return photo
        
        return None
    
    def get_all_icons(self):
        """获取所有图标的PhotoImage对象"""
        icon_names = ['wechat', 'onedrive', 'idle', 'sync', 'stats', 'cooldown']
        icons = {}
        
        for name in icon_names:
            icons[name] = self.load_icon(name)
        
        return icons

# 测试函数
def test_icon_manager():
    """测试图标管理器"""
    logger.info("测试图标管理器")
    
    manager = IconManager()
    icons = manager.get_all_icons()
    
    logger.info(f"成功加载 {len(icons)} 个图标")
    for name, icon in icons.items():
        if icon:
            logger.debug(f"✓ {name}: {icon}")
        else:
            logger.warning(f"✗ {name}: 加载失败")

if __name__ == "__main__":
    test_icon_manager()