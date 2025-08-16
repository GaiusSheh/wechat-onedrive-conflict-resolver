#!/usr/bin/env python3
"""
测试打包后的图标路径问题
"""
import sys
import os

def test_resource_paths():
    """测试资源路径"""
    print("=== 图标路径测试 ===")
    
    def get_resource_path(relative_path):
        """获取正确的资源文件路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe环境
            bundle_dir = sys._MEIPASS
            bundle_path = os.path.join(bundle_dir, relative_path)
            print(f"打包环境: bundle_dir={bundle_dir}")
            print(f"Bundle路径: {bundle_path}")
            print(f"Bundle文件存在: {os.path.exists(bundle_path)}")
            
            if not os.path.exists(bundle_path):
                exe_dir = os.path.dirname(sys.executable)
                exe_path = os.path.join(exe_dir, relative_path)
                print(f"EXE目录路径: {exe_path}")
                print(f"EXE目录文件存在: {os.path.exists(exe_path)}")
                return exe_path
            return bundle_path
        else:
            # 开发环境
            base_path = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(base_path, relative_path)
    
    # 测试所需的图标文件
    test_paths = [
        'gui/resources/icons/app.ico',
        'gui/resources/icons/main.png', 
        'gui/resources/downloads/main_transp_bg.png'
    ]
    
    for path in test_paths:
        print(f"\n--- 测试: {path} ---")
        full_path = get_resource_path(path)
        print(f"完整路径: {full_path}")
        print(f"文件存在: {os.path.exists(full_path)}")
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            print(f"文件大小: {file_size} 字节")
    
    # 如果是打包环境，列出bundle目录内容
    if getattr(sys, 'frozen', False):
        print(f"\n=== Bundle目录内容 ===")
        bundle_dir = sys._MEIPASS
        try:
            for root, dirs, files in os.walk(bundle_dir):
                level = root.replace(bundle_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    if 'icon' in file.lower() or file.endswith(('.ico', '.png')):
                        print(f"{subindent}{file}")
        except Exception as e:
            print(f"列出目录失败: {e}")

if __name__ == "__main__":
    test_resource_paths()