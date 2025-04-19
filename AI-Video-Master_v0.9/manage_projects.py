#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目管理工具 - 用于管理AI视频分析系统中的项目

使用方式:
- 列出所有项目: python manage_projects.py list
- 删除项目: python manage_projects.py delete 项目名称
"""

import os
import sys
import glob
import json
import shutil
import subprocess  # 添加subprocess导入

# 项目目录
STORAGE_PATH = "data/session"

def list_projects():
    """列出所有可用项目"""
    print("\n=== 可用项目列表 ===")
    pattern = os.path.join(STORAGE_PATH, "*_settings.json")
    files = glob.glob(pattern)
    
    if not files:
        print("没有找到任何项目。")
        return
    
    # 提取项目名称
    projects = []
    for file in files:
        base_name = os.path.basename(file)
        # 从文件名 "project_name_settings.json" 中提取项目名
        project_name = base_name.replace("_settings.json", "")
        projects.append(project_name)
    
    # 显示项目列表
    for idx, project in enumerate(sorted(projects), 1):
        print(f"{idx}. {project}")
    print("")

def delete_project(project_name, silent=False):
    """删除指定项目及其相关文件
    
    参数:
        project_name (str): 要删除的项目名称
        silent (bool): 是否静默执行（不打印输出）
    
    返回:
        bool: 删除是否成功
    """
    if not project_name:
        if not silent:
            print("错误: 未指定项目名称")
        return False
    
    settings_file = os.path.join(STORAGE_PATH, f"{project_name}_settings.json")
    results_file = os.path.join(STORAGE_PATH, f"{project_name}_results.json")
    
    files_deleted = False
    
    # 删除设置文件
    if os.path.exists(settings_file):
        if not silent:
            print(f"正在删除设置文件: {settings_file}")
        try:
            os.chmod(settings_file, 0o777)  # 确保有删除权限
            os.remove(settings_file)
            if not os.path.exists(settings_file):
                if not silent:
                    print(f"✓ 已成功删除设置文件")
                files_deleted = True
            else:
                if not silent:
                    print(f"⚠ 设置文件删除失败，尝试使用强制删除")
                # 尝试强制删除 - 使用subprocess替代os.system
                try:
                    result = subprocess.run(["rm", "-f", settings_file], 
                                         capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        if not silent:
                            print(f"✓ 强制删除成功")
                        files_deleted = True
                    else:
                        if not silent:
                            print(f"⚠ 强制删除返回错误: {result.stderr}")
                        # 最后尝试shell=True方式
                        result = subprocess.run(f"rm -f '{settings_file}'", 
                                              shell=True, capture_output=True, text=True, check=False)
                        if result.returncode == 0 and not os.path.exists(settings_file):
                            if not silent:
                                print(f"✓ shell方式强制删除成功")
                            files_deleted = True
                except Exception as sub_err:
                    if not silent:
                        print(f"强制删除过程中出错: {str(sub_err)}")
        except Exception as e:
            if not silent:
                print(f"删除设置文件时出错: {str(e)}")
    else:
        if not silent:
            print(f"⚠ 设置文件不存在: {settings_file}")
    
    # 删除结果文件
    if os.path.exists(results_file):
        if not silent:
            print(f"正在删除结果文件: {results_file}")
        try:
            os.chmod(results_file, 0o777)  # 确保有删除权限
            os.remove(results_file)
            if not os.path.exists(results_file):
                if not silent:
                    print(f"✓ 已成功删除结果文件")
                files_deleted = True
            else:
                if not silent:
                    print(f"⚠ 结果文件删除失败，尝试使用强制删除")
                # 尝试强制删除 - 使用subprocess替代os.system
                try:
                    result = subprocess.run(["rm", "-f", results_file], 
                                         capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        if not silent:
                            print(f"✓ 强制删除成功")
                        files_deleted = True
                    else:
                        if not silent:
                            print(f"⚠ 强制删除返回错误: {result.stderr}")
                        # 最后尝试shell=True方式
                        result = subprocess.run(f"rm -f '{results_file}'", 
                                              shell=True, capture_output=True, text=True, check=False)
                        if result.returncode == 0 and not os.path.exists(results_file):
                            if not silent:
                                print(f"✓ shell方式强制删除成功")
                            files_deleted = True
                except Exception as sub_err:
                    if not silent:
                        print(f"强制删除过程中出错: {str(sub_err)}")
        except Exception as e:
            if not silent:
                print(f"删除结果文件时出错: {str(e)}")
    
    if files_deleted:
        if not silent:
            print(f"\n✅ 项目 '{project_name}' 已成功删除！\n")
        return True
    else:
        if not silent:
            print(f"\n❌ 项目 '{project_name}' 删除失败或未找到相关文件。\n")
        return False

def show_help():
    """显示帮助信息"""
    print("\n使用方法:")
    print("  python manage_projects.py list        - 列出所有项目")
    print("  python manage_projects.py delete 项目名  - 删除指定项目")
    print("  python manage_projects.py help        - 显示帮助信息\n")

if __name__ == "__main__":
    # 确保存储目录存在
    os.makedirs(STORAGE_PATH, exist_ok=True)
    
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_projects()
    elif command == "delete" and len(sys.argv) >= 3:
        project_name = sys.argv[2]
        delete_project(project_name)
    elif command == "help":
        show_help()
    else:
        print("无效的命令或参数不足。")
        show_help()
        sys.exit(1) 