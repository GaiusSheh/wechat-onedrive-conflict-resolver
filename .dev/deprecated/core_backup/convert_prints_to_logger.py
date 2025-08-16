#!/usr/bin/env python3
"""
批量替换print语句为logger调用的脚本
"""

import os
import re
import sys
from pathlib import Path

def add_logger_import(content):
    """在文件开头添加logger导入"""
    lines = content.split('\n')
    
    # 检查是否已经导入了logger
    if any('from core.logger_helper import' in line or 'import logger_helper' in line for line in lines):
        return content
    
    # 找到导入语句的位置
    import_index = -1
    for i, line in enumerate(lines):
        if (line.startswith('import ') or line.startswith('from ')) and not line.startswith('"""') and not line.startswith("'''"):
            import_index = i
    
    # 如果没有找到导入语句，在文件开头添加
    if import_index == -1:
        # 跳过shebang和docstring
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('#!') or line.strip().startswith('"""') or line.strip().startswith("'''"):
                continue
            else:
                insert_index = i
                break
    else:
        insert_index = import_index + 1
    
    # 添加logger导入
    logger_import = [
        "import sys",
        "import os",
        "",
        "# 添加core模块到路径（如果需要）",
        "if 'logger_helper' not in sys.modules:",
        "    try:",
        "        from core.logger_helper import logger",
        "    except ImportError:",
        "        # 如果在core目录中，直接导入",
        "        try:",
        "            from logger_helper import logger",
        "        except ImportError:",
        "            # 添加路径后导入",
        "            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))",
        "            from core.logger_helper import logger",
        ""
    ]
    
    # 插入导入语句
    lines[insert_index:insert_index] = logger_import
    return '\n'.join(lines)

def convert_print_statements(content):
    """转换print语句为logger调用"""
    
    # 定义转换规则
    patterns = [
        # 错误信息
        (r'print\(f?"([^"]*失败[^"]*): \{([^}]+)\}"\)', r'logger.error(f"\1: {\2}")'),
        (r'print\(f?"([^"]*出错[^"]*): \{([^}]+)\}"\)', r'logger.error(f"\1: {\2}")'),
        (r'print\(f?"([^"]*错误[^"]*): \{([^}]+)\}"\)', r'logger.error(f"\1: {\2}")'),
        (r'print\("([^"]*失败[^"]*)"', r'logger.error("\1"'),
        (r'print\("([^"]*出错[^"]*)"', r'logger.error("\1"'),
        (r'print\("([^"]*错误[^"]*)"', r'logger.error("\1"'),
        
        # 成功/完成信息
        (r'print\(f?"([^"]*成功[^"]*): \{([^}]+)\}"\)', r'logger.info(f"\1: {\2}")'),
        (r'print\(f?"([^"]*完成[^"]*): \{([^}]+)\}"\)', r'logger.info(f"\1: {\2}")'),
        (r'print\(f?"([^"]*已[^"]*): \{([^}]+)\}"\)', r'logger.info(f"\1: {\2}")'),
        (r'print\("([^"]*成功[^"]*)"', r'logger.info("\1"'),
        (r'print\("([^"]*完成[^"]*)"', r'logger.info("\1"'),
        (r'print\("([^"]*已[^"]*)"', r'logger.info("\1"'),
        
        # 调试信息
        (r'print\(f?"\[调试\] ([^"]+): \{([^}]+)\}"\)', r'logger.debug(f"\1: {\2}")'),
        (r'print\(f?"\[DEBUG\] ([^"]+): \{([^}]+)\}"\)', r'logger.debug(f"\1: {\2}")'),
        (r'print\("\[调试\] ([^"]+)"', r'logger.debug("\1"'),
        (r'print\("\[DEBUG\] ([^"]+)"', r'logger.debug("\1"'),
        
        # 警告信息
        (r'print\(f?"([^"]*警告[^"]*): \{([^}]+)\}"\)', r'logger.warning(f"\1: {\2}")'),
        (r'print\("([^"]*警告[^"]*)"', r'logger.warning("\1"'),
        
        # 状态信息
        (r'print\(f?"([^"]*状态[^"]*): \{([^}]+)\}"\)', r'logger.info(f"\1: {\2}")'),
        (r'print\("([^"]*状态[^"]*)"', r'logger.info("\1"'),
        
        # 通用f-string转换
        (r'print\(f"([^"]*)"\)', r'logger.info(f"\1")'),
        
        # 通用字符串转换
        (r'print\("([^"]*)"\)', r'logger.info("\1")'),
        
        # 多参数print转换为info
        (r'print\(([^)]+)\)', r'logger.info(\1)'),
    ]
    
    result = content
    
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.MULTILINE)
    
    return result

def process_file(file_path):
    """处理单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有print语句
        if 'print(' not in content:
            return False, "无print语句"
        
        # 添加logger导入
        content = add_logger_import(content)
        
        # 转换print语句
        new_content = convert_print_statements(content)
        
        # 检查是否有变化
        if content == new_content:
            return False, "无变化"
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True, "转换成功"
        
    except Exception as e:
        return False, f"处理失败: {e}"

def main():
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    # 要处理的目录
    dirs_to_process = [
        project_dir / "core",
        project_dir / "gui", 
        project_dir / "tools"
    ]
    
    print("开始批量转换print语句为logger调用...")
    
    total_files = 0
    converted_files = 0
    
    for dir_path in dirs_to_process:
        if not dir_path.exists():
            continue
            
        print(f"\n处理目录: {dir_path}")
        
        # 遍历所有Python文件
        for py_file in dir_path.glob("**/*.py"):
            # 跳过__pycache__等目录
            if '__pycache__' in str(py_file):
                continue
            
            total_files += 1
            success, message = process_file(py_file)
            
            if success:
                converted_files += 1
                print(f"  ✅ {py_file.name} - {message}")
            else:
                print(f"  ⏭️  {py_file.name} - {message}")
    
    print(f"\n转换完成！")
    print(f"总文件数: {total_files}")
    print(f"转换文件数: {converted_files}")
    print(f"跳过文件数: {total_files - converted_files}")

if __name__ == "__main__":
    main()