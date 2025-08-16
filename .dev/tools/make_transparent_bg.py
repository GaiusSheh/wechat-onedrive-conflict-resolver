#!/usr/bin/env python3
"""
将main.png的白色背景替换为透明背景
"""
from PIL import Image

def make_transparent_background():
    """将白色背景替换为透明背景"""
    
    source_path = "gui/resources/downloads/main.png"
    output_path = "gui/resources/downloads/main_transp_bg.png"
    
    print("开始处理图标透明背景...")
    
    try:
        # 打开图像
        img = Image.open(source_path)
        print(f"原图尺寸: {img.size}, 模式: {img.mode}")
        
        # 转换为RGBA模式（支持透明度）
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 获取图像数据
        data = img.getdata()
        
        # 定义白色的阈值（允许一些容差）
        white_threshold = 240  # 240-255范围内的像素都视为白色
        
        # 处理每个像素
        new_data = []
        transparent_count = 0
        
        for pixel in data:
            r, g, b, a = pixel
            
            # 如果是白色或接近白色的像素，设为透明
            if r >= white_threshold and g >= white_threshold and b >= white_threshold:
                new_data.append((r, g, b, 0))  # 透明度设为0
                transparent_count += 1
            else:
                new_data.append((r, g, b, a))  # 保持原有透明度
        
        # 创建新图像
        result_img = Image.new('RGBA', img.size)
        result_img.putdata(new_data)
        
        # 保存处理后的图像
        result_img.save(output_path, 'PNG')
        print(f"透明背景图标已保存: {output_path}")
        
        # 显示处理统计
        total_pixels = len(data)
        print(f"处理统计: 共{total_pixels}像素，{transparent_count}像素变为透明")
        
        return True
        
    except Exception as e:
        print(f"处理失败: {e}")
        return False

if __name__ == "__main__":
    make_transparent_background()