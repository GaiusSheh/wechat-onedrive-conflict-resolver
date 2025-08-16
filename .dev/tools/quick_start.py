#!/usr/bin/env python3
"""
微信OneDrive冲突解决工具 - 快速开始脚本
"""

import os
import sys
import subprocess

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 6):
        print("❌ 需要Python 3.6或更高版本")
        return False
    print(f"✅ Python版本: {sys.version}")
    return True

def check_dependencies():
    """检查依赖包"""
    try:
        import psutil
        print("✅ psutil 已安装")
        return True
    except ImportError:
        print("❌ psutil 未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            print("✅ psutil 安装成功")
            return True
        except subprocess.CalledProcessError:
            print("❌ psutil 安装失败，请手动安装: pip install psutil")
            return False

def create_config():
    """创建配置文件"""
    config_path = "configs/sync_config.json"
    if os.path.exists(config_path):
        print(f"✅ 配置文件已存在: {config_path}")
        return True
    
    try:
        print("📝 创建默认配置文件...")
        result = subprocess.run([
            sys.executable, "core/config_manager.py", "create"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 配置文件创建成功")
            return True
        else:
            print(f"❌ 配置文件创建失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 创建配置文件时出错: {e}")
        return False

def show_usage():
    """显示使用方法"""
    print("\n" + "="*60)
    print("🚀 微信OneDrive冲突解决工具 - 准备就绪！")
    print("="*60)
    
    print("\n📋 基本使用方法：")
    print("1. 手动执行一次同步流程：")
    print("   python core/sync_workflow.py run")
    
    print("\n2. 启动自动监控服务：")
    print("   python core/sync_monitor.py start")
    
    print("\n3. 查看当前状态：")
    print("   python core/sync_workflow.py status")
    
    print("\n⚙️ 配置管理：")
    print("- 查看配置: python core/config_manager.py show")
    print("- 验证配置: python core/config_manager.py validate")
    print("- 编辑配置: notepad configs/sync_config.json")
    
    print("\n📖 详细文档：")
    print("- README.md - 完整使用说明")
    print("- PROJECT_STRUCTURE.md - 项目结构")
    print("- dev/requirements.md - 功能需求文档")
    
    print("\n" + "="*60)

def main():
    print("微信OneDrive冲突解决工具 - 快速启动检查")
    print("="*50)
    
    # 检查环境
    if not check_python_version():
        return False
    
    if not check_dependencies():
        return False
    
    # 创建配置
    if not create_config():
        return False
    
    # 显示使用方法
    show_usage()
    
    # 询问是否立即运行
    try:
        choice = input("\n🤔 是否现在运行一次同步流程测试? (y/n): ").lower()
        if choice == 'y':
            print("\n▶️ 启动同步流程测试...")
            subprocess.run([sys.executable, "core/sync_workflow.py", "run"])
    except (EOFError, KeyboardInterrupt):
        print("\n👋 退出快速启动")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("请检查Python环境和文件权限")