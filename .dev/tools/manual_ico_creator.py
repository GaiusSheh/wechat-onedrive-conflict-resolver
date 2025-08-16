#!/usr/bin/env python3
"""
Manual ICO file creator using raw binary approach
"""
import struct
import os
from PIL import Image
import io

def create_ico_manual():
    """手动创建多尺寸ICO文件"""
    source_path = "gui/resources/downloads/main_transp_bg.png"
    output_path = "gui/resources/icons/app_manual.ico"
    
    print("Manual ICO creation starting...")
    
    try:
        with Image.open(source_path) as img:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 要创建的尺寸
            sizes = [16, 32, 48, 256]  # 减少尺寸数量避免问题
            
            # 为每个尺寸创建PNG数据
            icon_data = []
            for size in sizes:
                # 创建尺寸
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # 将图像保存为PNG字节数据
                png_buffer = io.BytesIO()
                resized.save(png_buffer, format='PNG')
                png_data = png_buffer.getvalue()
                
                icon_data.append({
                    'size': size,
                    'data': png_data,
                    'length': len(png_data)
                })
                print(f"Prepared {size}x{size}: {len(png_data)} bytes")
            
            # 构建ICO文件
            with open(output_path, 'wb') as ico_file:
                # ICO文件头
                ico_file.write(struct.pack('<HHH', 0, 1, len(icon_data)))  # 保留字段, 类型(1=ico), 图标数量
                
                # 计算数据偏移
                header_size = 6  # 文件头
                directory_size = 16 * len(icon_data)  # 每个图标目录项16字节
                data_offset = header_size + directory_size
                
                # 写入图标目录项
                for icon in icon_data:
                    size = icon['size']
                    # 如果尺寸是256，在ICO格式中写入0
                    width = 0 if size == 256 else size
                    height = 0 if size == 256 else size
                    
                    ico_file.write(struct.pack('<BBBBHHII',
                        width,           # 宽度 (0 = 256)
                        height,          # 高度 (0 = 256)
                        0,               # 颜色数 (0 = >256色)
                        0,               # 保留
                        1,               # 颜色平面数
                        32,              # 每像素位数
                        icon['length'],  # 数据大小
                        data_offset      # 数据偏移
                    ))
                    data_offset += icon['length']
                
                # 写入实际的PNG数据
                for icon in icon_data:
                    ico_file.write(icon['data'])
            
            file_size = os.path.getsize(output_path)
            print(f"ICO file created: {output_path}")
            print(f"File size: {file_size} bytes")
            print(f"Contains {len(icon_data)} icon sizes")
            
            return True
            
    except Exception as e:
        print(f"Manual ICO creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_ico_manual()
    if success:
        print("Manual ICO creation completed!")
    else:
        print("Manual ICO creation failed!")