#!/usr/bin/env python3
"""
创建单一高分辨率ICO文件（比多分辨率更可靠）
"""
from PIL import Image
import os

def create_single_high_res_ico(target_size=128):
    """创建单一高分辨率ICO文件"""
    
    source_path = "gui/resources/downloads/main_transp_bg.png"
    output_path = f"gui/resources/icons/app_{target_size}x{target_size}.ico"
    
    print(f"创建 {target_size}x{target_size} 高分辨率ICO文件...")
    
    try:
        # 打开源图像
        source_img = Image.open(source_path)
        print(f"源图尺寸: {source_img.size}, 模式: {source_img.mode}")
        
        # 确保为RGBA模式
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')
        
        # 缩放到目标尺寸
        resized_img = source_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
        print(f"[OK] 缩放到 {target_size}x{target_size}")
        
        # 保存为ICO文件
        resized_img.save(output_path, format='ICO')
        
        print(f"[OK] 高分辨率ICO文件已创建: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"创建ICO文件失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_multiple_sizes():
    """创建多个不同尺寸的ICO文件"""
    sizes = [64, 128, 256]
    created_files = []
    
    for size in sizes:
        result = create_single_high_res_ico(size)
        if result:
            created_files.append(result)
    
    return created_files

def verify_ico_quality(ico_path):
    """验证ICO文件质量"""
    if not os.path.exists(ico_path):
        print(f"文件不存在: {ico_path}")
        return False
    
    try:
        with Image.open(ico_path) as ico:
            print(f"\n验证: {os.path.basename(ico_path)}")
            print(f"  格式: {ico.format}")
            print(f"  尺寸: {ico.size}")
            print(f"  模式: {ico.mode}")
            print(f"  文件大小: {os.path.getsize(ico_path)} 字节")
        
        return True
        
    except Exception as e:
        print(f"验证失败: {e}")
        return False

if __name__ == "__main__":
    print("创建多种尺寸的高分辨率ICO文件")
    print("=" * 50)
    
    created_files = create_multiple_sizes()
    
    if created_files:
        print(f"\n成功创建 {len(created_files)} 个ICO文件:")
        for file_path in created_files:
            verify_ico_quality(file_path)
    else:
        print("没有成功创建任何ICO文件")