#!/usr/bin/env python3
"""
验证ICO文件的分辨率信息
"""
from PIL import Image
import os

def verify_ico_resolutions(ico_path):
    """验证ICO文件包含的所有分辨率"""
    
    if not os.path.exists(ico_path):
        print(f"文件不存在: {ico_path}")
        return False
    
    try:
        print(f"正在分析ICO文件: {ico_path}")
        print("=" * 50)
        
        # 打开ICO文件
        with Image.open(ico_path) as ico:
            print(f"文件格式: {ico.format}")
            print(f"主要尺寸: {ico.size}")
            print(f"颜色模式: {ico.mode}")
            
            # 检查是否有多帧（多个图标）
            if hasattr(ico, 'n_frames'):
                total_frames = ico.n_frames
                print(f"包含图标数量: {total_frames}")
            else:
                total_frames = 1
                print("单一图标文件")
            
            print("\n分辨率详情:")
            print("-" * 30)
            
            # 遍历所有帧/图标
            resolutions = []
            for i in range(total_frames):
                try:
                    ico.seek(i)  # 切换到第i个图标
                    size = ico.size
                    mode = ico.mode
                    resolutions.append(size)
                    print(f"图标 {i+1}: {size[0]}x{size[1]} ({mode})")
                except Exception as e:
                    print(f"读取图标 {i+1} 失败: {e}")
            
            print(f"\n总结: 共{len(resolutions)}种分辨率")
            unique_sizes = list(set(resolutions))
            unique_sizes.sort(key=lambda x: x[0])  # 按宽度排序
            print(f"唯一尺寸: {unique_sizes}")
            
            return True
            
    except Exception as e:
        print(f"分析ICO文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_ico_files():
    """比较新旧ICO文件"""
    
    old_ico = "gui/resources/icons/app.ico"
    new_ico = "gui/resources/icons/app_high_res.ico"
    
    print("ICO文件对比分析")
    print("=" * 60)
    
    print("\n[OLD] 原始ICO文件 (app.ico):")
    if os.path.exists(old_ico):
        verify_ico_resolutions(old_ico)
    else:
        print("文件不存在")
    
    print("\n[NEW] 新生成ICO文件 (app_high_res.ico):")
    if os.path.exists(new_ico):
        verify_ico_resolutions(new_ico)
    else:
        print("文件不存在")

if __name__ == "__main__":
    compare_ico_files()