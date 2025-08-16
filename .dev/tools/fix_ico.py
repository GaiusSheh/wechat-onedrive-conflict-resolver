#!/usr/bin/env python3
"""
修复ICO文件创建问题
"""
from PIL import Image

def create_ico():
    # 加载源图片
    with Image.open('gui/resources/downloads/main_transp_bg.png') as img:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 创建多个尺寸
        sizes = [16, 24, 32, 48, 64, 96, 128, 256]
        images = []
        
        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            images.append(resized)
            print(f"Created {size}x{size}")
        
        # 使用第一个图像保存，其他作为附加图像
        if images:
            images[0].save(
                'gui/resources/icons/app.ico',
                format='ICO',
                sizes=[(size, size) for size in sizes]
            )
            print(f"Saved ICO with {len(sizes)} sizes")

if __name__ == '__main__':
    create_ico()