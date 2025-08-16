#!/usr/bin/env python3
"""
清理print语句脚本 - 2025-08-09
将代码中的print语句替换为适当的日志调用
"""

import os
import re
import sys

def cleanup_print_in_file(filepath):
    """清理单个文件中的print语句"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换常见的print模式为日志调用
        replacements = [
            # 配置相关
            (r'print\(f?"已加载配置文件: {.*?}"\)', 'logger.info(f"已加载配置文件: {self.config_file}")'),
            (r'print\(f?"配置文件不存在，使用默认配置: {.*?}"\)', 'logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")'),
            (r'print\(f?"加载配置文件失败: {.*?}"\)', 'logger.error(f"加载配置文件失败: {e}")'),
            (r'print\("使用默认配置"\)', 'logger.info("使用默认配置")'),
            (r'print\(f?"配置已保存: {.*?}"\)', 'logger.info(f"配置已保存: {self.config_file}")'),
            (r'print\(f?"保存配置失败: {.*?}"\)', 'logger.error(f"保存配置失败: {e}")'),
            (r'print\(f?"配置已更新: {.*?}"\)', 'logger.debug(f"配置已更新: {key_path} = {value}")'),
            (r'print\(f?"配置文件已重新加载: {.*?}"\)', 'logger.info(f"配置文件已重新加载: {self.config_file}")'),
            (r'print\(f?"重新加载配置失败: {.*?}"\)', 'logger.error(f"重新加载配置失败: {e}")'),
            
            # 微信控制相关
            (r'print\("微信未运行"\)', 'logger.info("微信未运行")'),
            (r'print\("微信已经在运行"\)', 'logger.info("微信已经在运行")'),
            (r'print\(f?"找到 {.*?} 个微信进程"\)', 'logger.info(f"找到 {len(wechat_processes)} 个微信进程")'),
            (r'print\(f?"正在停止微信进程 \(PID: {.*?}\)"\)', 'logger.info(f"正在停止微信进程 (PID: {proc.pid})")'),
            (r'print\(f?"进程 {.*?} 已经停止"\)', 'logger.info(f"进程 {proc.pid} 已经停止")'),
            (r'print\(f?"错误：没有权限停止进程 {.*?}，请以管理员身份运行"\)', 'logger.error(f"没有权限停止进程 {proc.pid}，请以管理员身份运行")'),
            (r'print\(f?"停止进程 {.*?} 时发生错误：{.*?}"\)', 'logger.error(f"停止进程 {proc.pid} 时发生错误：{e}")'),
            (r'print\("等待微信进程退出..."\)', 'logger.info("等待微信进程退出...")'),
            (r'print\(f?"还有 {.*?} 个进程未退出，强制结束..."\)', 'logger.warning(f"还有 {len(remaining_processes)} 个进程未退出，强制结束...")'),
            (r'print\(f?"强制结束进程 {.*?}"\)', 'logger.info(f"强制结束进程 {proc.pid}")'),
            (r'print\(f?"强制结束进程 {.*?} 失败：{.*?}"\)', 'logger.error(f"强制结束进程 {proc.pid} 失败：{e}")'),
            (r'print\("所有微信进程已成功停止"\)', 'logger.info("所有微信进程已成功停止")'),
            (r'print\(f?"仍有 {.*?} 个微信进程在运行"\)', 'logger.warning(f"仍有 {len(final_processes)} 个微信进程在运行")'),
            (r'print\(f?"正在启动微信：{.*?}"\)', 'logger.info(f"正在启动微信：{wechat_path}")'),
            (r'print\("微信启动成功"\)', 'logger.info("微信启动成功")'),
            (r'print\("微信启动命令已执行"\)', 'logger.info("微信启动命令已执行")'),
            (r'print\(f?"启动微信失败：{.*?}"\)', 'logger.error(f"启动微信失败：{e}")'),
            
            # OneDrive控制相关
            (r'print\("OneDrive未运行"\)', 'logger.info("OneDrive未运行")'),
            (r'print\("OneDrive未运行，无需暂停"\)', 'logger.info("OneDrive未运行，无需暂停")'),
            (r'print\("正在暂停OneDrive同步..."\)', 'logger.info("正在暂停OneDrive同步...")'),
            (r'print\(f?"找到 {.*?} 个OneDrive进程"\)', 'logger.info(f"找到 {len(onedrive_processes)} 个OneDrive进程")'),
            (r'print\(f?"正在停止OneDrive进程 \(PID: {.*?}\)"\)', 'logger.info(f"正在停止OneDrive进程 (PID: {proc.pid})")'),
            (r'print\("等待OneDrive进程退出..."\)', 'logger.info("等待OneDrive进程退出...")'),
            (r'print\("所有OneDrive进程已成功停止"\)', 'logger.info("所有OneDrive进程已成功停止")'),
            (r'print\(f?"正在启动OneDrive（后台模式）：{.*?}"\)', 'logger.info(f"正在启动OneDrive（后台模式）：{onedrive_path}")'),
            (r'print\("OneDrive启动命令已执行"\)', 'logger.info("OneDrive启动命令已执行")'),
            (r'print\(f?"恢复OneDrive同步时发生错误：{.*?}"\)', 'logger.error(f"恢复OneDrive同步时发生错误：{e}")'),
            
            # 错误相关
            (r'print\(f?"错误：未找到.*?安装路径"\)', 'logger.error(f"未找到安装路径")'),
            (r'print\(f?".*?命令失败: {.*?}，回退到psutil方法"\)', 'logger.warning(f"系统命令失败: {e}，回退到psutil方法")'),
            (r'print\(f?".*?命令超时，回退到psutil方法"\)', 'logger.warning("系统命令超时，回退到psutil方法")'),
        ]
        
        # 应用替换
        changes_made = 0
        for pattern, replacement in replacements:
            new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
            if count > 0:
                content = new_content
                changes_made += count
                print(f"  替换了{count}个匹配的print语句")
        
        # 如果有更改，写回文件
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {filepath}: 更新了{changes_made}个print语句")
            return changes_made
        else:
            print(f"⚪ {filepath}: 无需更改")
            return 0
            
    except Exception as e:
        print(f"❌ {filepath}: 处理失败 - {e}")
        return 0

def main():
    """主函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 需要处理的文件列表
    files_to_process = [
        os.path.join(project_root, 'core', 'config_manager.py'),
        os.path.join(project_root, 'core', 'wechat_controller.py'),
        os.path.join(project_root, 'core', 'onedrive_controller.py'),
        os.path.join(project_root, 'core', 'sync_workflow.py'),
        os.path.join(project_root, 'core', 'task_scheduler.py'),
    ]
    
    total_changes = 0
    
    print("=== 开始清理print语句 ===")
    for filepath in files_to_process:
        if os.path.exists(filepath):
            changes = cleanup_print_in_file(filepath)
            total_changes += changes
        else:
            print(f"⚠️  文件不存在: {filepath}")
    
    print(f"\n=== 清理完成 ===")
    print(f"总共处理了 {total_changes} 个print语句")
    
    if total_changes > 0:
        print("\n⚠️  注意：被修改的文件需要添加以下导入语句：")
        print("from core.logger_helper import logger")
        print("或者使用统一的日志系统")

if __name__ == "__main__":
    main()