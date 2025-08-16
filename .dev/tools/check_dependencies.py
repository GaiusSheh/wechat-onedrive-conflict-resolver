#!/usr/bin/env python3
"""
依赖包检查脚本
验证项目所需的所有Python包是否正确安装
"""

import sys

def check_dependencies():
    """检查所有必需的依赖包"""
    print("检查微信OneDrive冲突解决工具的依赖包...")
    print("=" * 50)
    
    # 第三方依赖包
    dependencies = [
        ("psutil", "进程管理"),
        ("schedule", "任务调度"),
    ]
    
    # 标准库（仅验证可用性）
    stdlib_modules = [
        ("ctypes", "Windows API调用"),
        ("winreg", "Windows注册表访问"),
        ("subprocess", "子进程管理"),
        ("json", "JSON配置文件处理"),
        ("logging", "日志记录"),
        ("threading", "多线程支持"),
        ("time", "时间处理"),
        ("datetime", "日期时间处理"),
        ("os", "操作系统接口"),
        ("sys", "系统接口"),
        ("signal", "信号处理"),
    ]
    
    all_success = True
    
    print("检查第三方依赖包:")
    for module_name, description in dependencies:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', '未知版本')
            print(f"  [OK] {module_name:<12} - {description} (版本: {version})")
        except ImportError as e:
            print(f"  [X]  {module_name:<12} - {description} (缺失: {e})")
            all_success = False
    
    print(f"\n检查Python标准库 (Python {sys.version_info.major}.{sys.version_info.minor}):")
    for module_name, description in stdlib_modules:
        try:
            __import__(module_name)
            print(f"  [OK] {module_name:<12} - {description}")
        except ImportError as e:
            print(f"  [X]  {module_name:<12} - {description} (错误: {e})")
            all_success = False
    
    print("\n" + "=" * 50)
    if all_success:
        print("[SUCCESS] 所有依赖包检查通过！")
        print("可以正常运行微信OneDrive冲突解决工具")
    else:
        print("[WARNING] 部分依赖包缺失！")
        print("请运行以下命令安装缺失的包:")
        print("   pip install -r requirements.txt")
    
    return all_success

def main():
    try:
        success = check_dependencies()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] 检查过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()