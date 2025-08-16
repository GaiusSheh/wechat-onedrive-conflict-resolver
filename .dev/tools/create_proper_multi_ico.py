#!/usr/bin/env python3
"""
使用正确的方法创建多分辨率ICO文件
"""
from PIL import Image
import os

def create_proper_multi_resolution_ico():
    """正确创建包含多种分辨率的ICO文件"""
    
    source_path = "gui/resources/downloads/main_transp_bg.png"
    output_path = "gui/resources/icons/app_multi_res.ico"
    
    print("使用正确方法创建多分辨率ICO文件...")
    
    try:
        # 打开源图像
        source_img = Image.open(source_path)
        print(f"源图尺寸: {source_img.size}, 模式: {source_img.mode}")
        
        # 确保为RGBA模式
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')
        
        # 定义ICO文件需要的尺寸
        sizes = [256, 128, 96, 64, 48, 32, 24, 16]  # 从大到小排序
        
        # 创建不同尺寸的图标列表
        images = []
        for size in sizes:
            # 使用高质量重采样算法缩放
            resized = source_img.resize((size, size), Image.Resampling.LANCZOS)
            images.append(resized)
            print(f"[OK] 创建 {size}x{size} 尺寸")
        
        # 使用第一个图像作为主图像，其他作为附加图像
        first_image = images[0]
        additional_images = images[1:]
        
        print(f"保存ICO文件: {output_path}")
        print(f"主图像: {first_image.size}")
        print(f"附加图像数量: {len(additional_images)}")
        
        # 保存为ICO文件
        first_image.save(
            output_path,
            format='ICO',
            append_images=additional_images,
            save_all=True  # 关键参数：保存所有图像
        )
        
        print(f"[OK] 多分辨率ICO文件已创建: {output_path}")
        print(f"包含尺寸: {', '.join([f'{s}x{s}' for s in sizes])}")
        
        return True
        
    except Exception as e:
        print(f"创建ICO文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_created_ico():
    """验证创建的ICO文件"""
    ico_path = "gui/resources/icons/app_multi_res.ico"
    
    if not os.path.exists(ico_path):
        print("ICO文件不存在")
        return False
    
    try:
        print(f"\n验证ICO文件: {ico_path}")
        print("=" * 40)
        
        with Image.open(ico_path) as ico:
            print(f"文件格式: {ico.format}")
            print(f"主要尺寸: {ico.size}")
            print(f"颜色模式: {ico.mode}")
            
            # 检查帧数
            frame_count = getattr(ico, 'n_frames', 1)
            print(f"图标帧数: {frame_count}")
            
            if frame_count > 1:
                print("\n所有分辨率:")
                for i in range(frame_count):
                    ico.seek(i)
                    print(f"  帧 {i+1}: {ico.size[0]}x{ico.size[1]} ({ico.mode})")
            
        return True
        
    except Exception as e:
        print(f"验证ICO文件失败: {e}")
        return False

if __name__ == "__main__":
    if create_proper_multi_resolution_ico():
        verify_created_ico()
    else:
        print("ICO文件创建失败")