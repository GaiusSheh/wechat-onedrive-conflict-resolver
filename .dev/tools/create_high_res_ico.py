#!/usr/bin/env python3
"""
创建高分辨率ICO文件 - 从透明背景PNG生成多尺寸ICO
"""
from PIL import Image
import os

def create_high_resolution_ico():
    """从main_transp_bg.png创建包含多种尺寸的高分辨率ICO文件"""
    
    source_path = "gui/resources/downloads/main_transp_bg.png"
    output_path = "gui/resources/icons/app_high_res.ico"
    
    print("开始创建高分辨率ICO文件...")
    
    try:
        # 打开源图像
        source_img = Image.open(source_path)
        print(f"源图尺寸: {source_img.size}, 模式: {source_img.mode}")
        
        # 确保为RGBA模式
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')
        
        # 定义ICO文件需要的多种尺寸
        sizes = [16, 24, 32, 48, 64, 96, 128, 256]
        
        # 创建不同尺寸的图标
        icon_images = []
        for size in sizes:
            # 使用高质量重采样算法缩放
            resized = source_img.resize((size, size), Image.Resampling.LANCZOS)
            icon_images.append(resized)
            print(f"[OK] 创建 {size}x{size} 尺寸图标")
        
        # 保存为ICO文件（包含所有尺寸）
        icon_images[0].save(
            output_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in icon_images],
            append_images=icon_images[1:]  # 添加其他尺寸
        )
        
        print(f"[OK] 高分辨率ICO文件已创建: {output_path}")
        print(f"包含尺寸: {', '.join([f'{s}x{s}' for s in sizes])}")
        
        return True
        
    except Exception as e:
        print(f"创建ICO文件失败: {e}")
        return False

def test_ico_file():
    """测试生成的ICO文件"""
    ico_path = "gui/resources/icons/app_high_res.ico"
    
    if not os.path.exists(ico_path):
        print("ICO文件不存在")
        return False
    
    try:
        # 打开ICO文件并显示信息
        with Image.open(ico_path) as ico:
            print(f"ICO文件信息:")
            print(f"  格式: {ico.format}")
            print(f"  尺寸: {ico.size}")
            print(f"  模式: {ico.mode}")
            
            # 如果ICO包含多个图标，显示所有尺寸
            if hasattr(ico, 'n_frames'):
                print(f"  包含图标数量: {ico.n_frames}")
        
        return True
        
    except Exception as e:
        print(f"测试ICO文件失败: {e}")
        return False

if __name__ == "__main__":
    if create_high_resolution_ico():
        print("\n测试生成的ICO文件:")
        test_ico_file()
    else:
        print("ICO文件创建失败")