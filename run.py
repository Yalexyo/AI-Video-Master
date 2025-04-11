#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视频分析系统启动脚本
"""

import os
import sys
import subprocess
import importlib.util

def check_env():
    """检查环境"""
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查关键依赖
    dependencies = ["streamlit", "moviepy", "torch", "sentence_transformers"]
    missing = []
    
    for dep in dependencies:
        if importlib.util.find_spec(dep) is None:
            missing.append(dep)
    
    if missing:
        print(f"警告: 以下依赖缺失: {', '.join(missing)}")
        install = input("是否安装缺失的依赖? (y/n): ")
        if install.lower() == 'y':
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # 检查目录结构
    required_dirs = ["data/input", "data/output", "data/session"]
    for d in required_dirs:
        os.makedirs(d, exist_ok=True)
        print(f"确保目录存在: {d}")

def run_app():
    """运行应用"""
    # 首先运行依赖修复工具
    try:
        if os.path.exists("fix_dependencies.py"):
            print("运行依赖修复工具...")
            subprocess.run([sys.executable, "fix_dependencies.py"])
    except Exception as e:
        print(f"依赖修复失败: {str(e)}")
    
    # 启动Streamlit应用
    print("\n启动应用...")
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        print("以调试模式启动")
        os.environ["PYTHONTRACEMALLOC"] = "1"
        os.environ["STREAMLIT_DEBUG"] = "true"
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n应用已停止")

if __name__ == "__main__":
    print("=" * 50)
    print("AI视频分析系统启动器 v1.0")
    print("=" * 50)
    
    check_env()
    run_app() 