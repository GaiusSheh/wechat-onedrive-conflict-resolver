#!/usr/bin/env python3
"""
创建多分辨率ICO文件，包含透明背景的main图标
"""
from PIL import Image
import os

def create_multi_resolution_ico():
    """创建包含多分辨率的ICO文件"""
    
    source_path = "gui/resources/downloads/main_transp_bg.png"
    ico_output_path = "gui/resources/icons/app.ico"  # 替换现有的app.ico
    png_30x30_path = "gui/resources/icons/main.png"  # 30x30版本供GUI使用
    
    print("Creating multi-resolution ICO file...")
    
    # 确保输出目录存在
    os.makedirs("gui/resources/icons", exist_ok=True)
    
    try:
        # 打开透明背景的源图像
        with Image.open(source_path) as img:
            print(f"Source image: {img.size}, mode: {img.mode}")
            
            # 确保图像为RGBA模式
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 定义ICO文件中要包含的分辨率
            ico_sizes = [
                (16, 16),    # 小图标
                (24, 24),    # 小图标
                (32, 32),    # 中等图标
                (48, 48),    # 中等图标
                (64, 64),    # 大图标
                (96, 96),    # 大图标
                (128, 128),  # 超大图标
                (256, 256)   # 最大图标
            ]
            
            # 创建不同尺寸的图像
            ico_images = []
            print("Generating different resolution icons:")
            
            for size in ico_sizes:
                # 使用高质量重采样算法
                resized = img.resize(size, Image.Resampling.LANCZOS)
                ico_images.append(resized)
                print(f"  - {size[0]}x{size[1]}")
            
            # 保存为ICO文件（包含所有分辨率）
            if ico_images:
                ico_images[0].save(
                    ico_output_path, 
                    format='ICO', 
                    sizes=[img.size for img in ico_images],
                    append_images=ico_images[1:]
                )
                print(f"Multi-resolution ICO file saved: {ico_output_path}")
            
            # 另外创建30x30的PNG版本供图标管理器使用
            img_30x30 = img.resize((30, 30), Image.Resampling.LANCZOS)
            img_30x30.save(png_30x30_path, 'PNG')
            print(f"30x30 PNG版本已保存: {png_30x30_path}")
            
            print(f"\n图标创建完成!")
            print(f"ICO文件包含 {len(ico_sizes)} 种分辨率，系统会自动选择合适的尺寸")
            
            return True
            
    except Exception as e:
        print(f"创建失败: {e}")
        return False

if __name__ == "__main__":
    create_multi_resolution_ico()