#!/usr/bin/env python3
"""
版本号自动更新脚本
用法: python scripts/update_version.py 2.3 "配置面板优化版"
"""

import os
import re
import json
import sys
from pathlib import Path

class VersionManager:
    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir or os.getcwd())
        self.version_file = self.root_dir / "version.json"
        
    def load_version_config(self):
        """加载版本配置"""
        if self.version_file.exists():
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"version": "1.0", "name": "初始版本"}
    
    def save_version_config(self, version, name):
        """保存版本配置"""
        config = {"version": version, "name": name}
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return config
    
    def get_files_to_update(self):
        """获取需要更新版本号的文件列表"""
        files = [
            # Python文件
            "gui/main_window.py",
            "gui/config_panel.py",
            
            # 文档文件
            "README.md",
            ".claude/CLAUDE.md",
            ".dev/CHANGELOG.md",
            ".dev/PROJECT_SUMMARY.md",
            
            # 配置文件
            "configs/sync_config.json"
        ]
        
        # 只返回存在的文件
        return [f for f in files if (self.root_dir / f).exists()]
    
    def update_python_files(self, version, name):
        """更新Python文件中的版本号"""
        patterns = [
            # 文件头部注释
            (r'微信OneDrive冲突解决工具 - .* v\d+\.\d+', f'微信OneDrive冲突解决工具 - {name}GUI主窗口 v{version}'),
            # 类文档字符串
            (r'""".*类 - v\d+\.\d+ .*版"""', f'"""主GUI窗口类 - v{version} {name}"""'),
            # 窗口标题
            (r'self\.root\.title\("微信OneDrive冲突解决工具 v\d+\.\d+"\)', f'self.root.title("微信OneDrive冲突解决工具 v{version}")'),
            # 版本标签
            (r'text="v\d+\.\d+ \| .*版"', f'text="v{version} | {name}"'),
        ]
        
        for file_path in ["gui/main_window.py", "gui/config_panel.py"]:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue
                
            content = full_path.read_text(encoding='utf-8')
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            full_path.write_text(content, encoding='utf-8')
            print(f"✅ 更新 {file_path}")
    
    def update_markdown_files(self, version, name):
        """更新Markdown文件中的版本号"""
        patterns = [
            # 当前版本标记
            (r'\*\*当前版本\*\*: v\d+\.\d+ - .*', f'**当前版本**: v{version} - {name}'),
            # 版本标题
            (r'### \[v\d+\.\d+\] - \d{4}-\d{2}-\d{2} - .*', f'### [v{version}] - 2025-08-08 - {name}'),
        ]
        
        md_files = [".claude/CLAUDE.md", "README.md", ".dev/PROJECT_SUMMARY.md"]
        
        for file_path in md_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue
                
            content = full_path.read_text(encoding='utf-8')
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            full_path.write_text(content, encoding='utf-8')
            print(f"✅ 更新 {file_path}")
    
    def update_all(self, version, name):
        """更新所有文件的版本号"""
        print(f"🚀 开始更新版本号到 v{version} - {name}")
        
        # 保存版本配置
        self.save_version_config(version, name)
        print(f"✅ 保存版本配置: {self.version_file}")
        
        # 更新Python文件
        self.update_python_files(version, name)
        
        # 更新Markdown文件
        self.update_markdown_files(version, name)
        
        print(f"✨ 版本更新完成！当前版本: v{version} - {name}")
        
        # 显示更新的文件
        updated_files = self.get_files_to_update()
        print(f"📁 共更新了 {len(updated_files)} 个文件")

def main():
    if len(sys.argv) != 3:
        print("用法: python scripts/update_version.py <版本号> <版本名称>")
        print("示例: python scripts/update_version.py 2.3 '配置面板优化版'")
        sys.exit(1)
    
    version = sys.argv[1]
    name = sys.argv[2]
    
    # 验证版本号格式
    if not re.match(r'^\d+\.\d+$', version):
        print("❌ 版本号格式错误，应为: X.Y (如: 2.3)")
        sys.exit(1)
    
    manager = VersionManager()
    manager.update_all(version, name)

if __name__ == "__main__":
    main()