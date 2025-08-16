#!/usr/bin/env python3
"""
创建正确的多分辨率ICO文件
"""
from PIL import Image
import os

def create_proper_ico():
    """创建包含多分辨率的正确ICO文件"""
    
    source_path = "gui/resources/downloads/main_transp_bg.png"
    ico_output_path = "gui/resources/icons/app.ico"
    
    print("创建多分辨率ICO文件...")
    
    # 确保输出目录存在
    os.makedirs("gui/resources/icons", exist_ok=True)
    
    try:
        # 打开源图像
        with Image.open(source_path) as img:
            print(f"源图像: {img.size}, 模式: {img.mode}")
            
            # 确保图像为RGBA模式
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 定义要创建的尺寸
            sizes = [16, 24, 32, 48, 64, 96, 128, 256]
            
            # 创建所有尺寸的图像
            images = []
            for size in sizes:
                # 使用高质量重采样
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                images.append(resized)
                print(f"  创建 {size}x{size}")
            
            # 备份现有的ICO文件
            if os.path.exists(ico_output_path):
                backup_path = ico_output_path + ".backup"
                import shutil
                shutil.copy2(ico_output_path, backup_path)
                print(f"备份原文件到: {backup_path}")
            
            # 保存ICO文件 - 使用不同的方法
            try:
                # 方法1：使用PIL的标准方法
                images[0].save(
                    ico_output_path,
                    format='ICO',
                    sizes=[(s, s) for s in sizes],
                    append_images=images[1:] if len(images) > 1 else None
                )
                print(f"方法1成功：保存到 {ico_output_path}")
            except Exception as e:
                print(f"方法1失败: {e}")
                
                # 方法2：手动保存每个尺寸
                try:
                    # 只保存最重要的几个尺寸
                    important_sizes = [16, 32, 48, 256]
                    important_images = []
                    
                    for size in important_sizes:
                        resized = img.resize((size, size), Image.Resampling.LANCZOS)
                        important_images.append(resized)
                    
                    important_images[0].save(
                        ico_output_path,
                        format='ICO',
                        append_images=important_images[1:]
                    )
                    print(f"方法2成功：保存了 {len(important_sizes)} 个重要尺寸")
                except Exception as e2:
                    print(f"方法2也失败: {e2}")
                    return False
            
            # 验证创建的文件
            if os.path.exists(ico_output_path):
                file_size = os.path.getsize(ico_output_path)
                print(f"ICO文件大小: {file_size} 字节")
                
                if file_size > 1000:  # 多尺寸ICO应该比较大
                    print("✓ ICO文件创建成功！")
                    return True
                else:
                    print("⚠ ICO文件可能只包含单一尺寸")
                    return False
            else:
                print("✗ ICO文件创建失败")
                return False
            
    except Exception as e:
        print(f"创建ICO失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_proper_ico()
    if success:
        print("\n✓ ICO文件创建完成，现在可以用于打包了！")
    else:
        print("\n✗ ICO文件创建失败，需要进一步调试")