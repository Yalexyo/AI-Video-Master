#!/usr/bin/env python3
import streamlit as st
import os
import sys
import logging
import subprocess
import platform

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/run.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        "logs",
        "data",
        "data/dimensions",
        "data/output",
        "data/input",
        "data/clips",
        "data/session"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"确保目录存在: {directory}")

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import streamlit
        import pandas as pd
        import numpy as np
        import sentence_transformers
        logger.info("核心依赖已安装")
        return True
    except ImportError as e:
        logger.error(f"缺少依赖: {str(e)}")
        logger.info("尝试安装依赖...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            logger.info("依赖安装完成")
            return True
        except Exception as e:
            logger.error(f"依赖安装失败: {str(e)}")
            return False

def start_app():
    """启动Streamlit应用"""
    logger.info("启动AI视频分析系统...")
    
    # 检查操作系统
    system = platform.system()
    logger.info(f"操作系统: {system}")
    
    # 构建启动命令
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    
    try:
        logger.info(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd)
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    # 确保必要的目录存在
    ensure_directories()
    
    # 检查依赖
    if check_dependencies():
        # 启动应用
        start_app()
    else:
        print("请确保已安装所有依赖项。运行: pip install -r requirements.txt") 