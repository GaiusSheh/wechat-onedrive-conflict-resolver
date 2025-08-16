#!/usr/bin/env python3
"""
临时脚本：将main.png转换为ICO格式和30x30尺寸
"""
from PIL import Image
import os
import sys

def convert_main_icon():
    """转换main图标为各种需要的格式"""
    
    # 路径设置
    source_path = "gui/resources/downloads/main.png"
    ico_path = "gui/resources/icons/app.ico"  # 替换现有的app.ico
    icons_30x30_path = "gui/resources/icons/main.png"
    
    print("开始转换main图标...")
    
    try:
        # 打开源图像
        with Image.open(source_path) as img:
            print(f"源图像尺寸: {img.size}")
            
            # 1. 创建ICO格式（多个尺寸）
            ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            ico_images = []
            
            for size in ico_sizes:
                resized = img.resize(size, Image.Resampling.LANCZOS)
                if resized.mode != 'RGBA':
                    resized = resized.convert('RGBA')
                ico_images.append(resized)
            
            # 保存为ICO文件
            ico_images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in ico_images], append_images=ico_images[1:])
            print(f"✓ ICO格式已保存: {ico_path}")
            
            # 2. 创建30x30 PNG格式（供图标管理器使用）
            resized_30x30 = img.resize((30, 30), Image.Resampling.LANCZOS)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                resized_30x30 = resized_30x30.convert('RGBA')
            
            resized_30x30.save(icons_30x30_path, 'PNG')
            print(f"✓ 30x30 PNG已保存: {icons_30x30_path}")
            
            print("图标转换完成！")
            return True
            
    except Exception as e:
        print(f"转换失败: {e}")
        return False

if __name__ == "__main__":
    success = convert_main_icon()
    if success:
        print("\n可以删除此临时脚本了")
        sys.exit(0)
    else:
        sys.exit(1)