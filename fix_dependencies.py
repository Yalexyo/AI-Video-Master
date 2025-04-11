#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复moviepy导入问题的脚本
"""

import os
import sys
import subprocess
import importlib

def check_imports():
    """检查关键导入是否正常"""
    print("检查依赖导入...")
    
    libraries = [
        ("moviepy", ["editor"]),
        ("numpy", []),
        ("sentence_transformers", ["SentenceTransformer"]),
        ("streamlit", []),
        ("torch", []),
    ]
    
    for lib, modules in libraries:
        try:
            imported_lib = importlib.import_module(lib)
            print(f"✓ 成功导入 {lib} ({imported_lib.__version__ if hasattr(imported_lib, '__version__') else 'unknown version'})")
            
            # 检查子模块
            for module in modules:
                try:
                    if "." in module:
                        parent, child = module.split(".", 1)
                        parent_mod = getattr(imported_lib, parent)
                        getattr(parent_mod, child)
                    else:
                        getattr(imported_lib, module)
                    print(f"  ✓ 成功导入 {lib}.{module}")
                except (AttributeError, ImportError) as e:
                    print(f"  ✗ 无法导入 {lib}.{module}: {str(e)}")
                    if lib == "moviepy" and module == "editor":
                        fix_moviepy()
        except ImportError as e:
            print(f"✗ 无法导入 {lib}: {str(e)}")
            if lib == "moviepy":
                fix_moviepy()

def fix_moviepy():
    """修复moviepy相关问题"""
    print("\n正在修复moviepy相关问题...")
    
    # 1. 确保安装了正确版本的moviepy及其依赖
    print("重新安装moviepy和关键依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "moviepy==1.0.3", "numpy==1.26.4", "decorator", "imageio", "imageio_ffmpeg", "tqdm", "proglog"])
    
    # 2. 检查ffmpeg是否正常安装
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"✓ 找到ffmpeg: {ffmpeg_path}")
    except Exception as e:
        print(f"✗ 检查ffmpeg失败: {str(e)}")
        print("正在尝试安装ffmpeg...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "imageio_ffmpeg"])
    
    # 3. 创建修复版的moviepy导入文件
    try:
        fix_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "fixed_imports")
        os.makedirs(fix_dir, exist_ok=True)
        
        with open(os.path.join(fix_dir, "__init__.py"), "w") as f:
            f.write("# Fix for moviepy imports\n")
        
        with open(os.path.join(fix_dir, "moviepy_fixed.py"), "w") as f:
            f.write("""
# 修复版moviepy导入
try:
    from moviepy.editor import (
        VideoFileClip, 
        TextClip, 
        CompositeVideoClip, 
        concatenate_videoclips,
        ColorClip
    )
    from moviepy import video
    vfx = video.fx.all
    
    print("成功导入moviepy组件")
except ImportError as e:
    print(f"导入moviepy组件失败: {str(e)}")
    # 提供空实现防止程序崩溃
    class DummyClip:
        def __init__(self, *args, **kwargs):
            self.duration = 0
            self.size = (640, 480)
        def set_position(self, pos): return self
        def set_duration(self, duration): return self
        def fadeout(self, duration): return self
        def fadein(self, duration): return self
    
    VideoFileClip = TextClip = CompositeVideoClip = ColorClip = DummyClip
    concatenate_videoclips = lambda clips, *args, **kwargs: DummyClip()
    class vfx: pass
""")
        
        print(f"✓ 创建了修复文件: {os.path.join(fix_dir, 'moviepy_fixed.py')}")
        print("\n请使用以下导入代替原有的moviepy导入:")
        print("from core.fixed_imports.moviepy_fixed import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ColorClip, vfx")
        
    except Exception as e:
        print(f"创建修复文件失败: {str(e)}")
    
    print("\n完成修复尝试。请重启应用以查看是否解决问题。")

if __name__ == "__main__":
    print("======== 依赖修复工具 ========")
    check_imports()
    print("\n如果仍有导入问题，请运行: pip install -r requirements.txt --force-reinstall")
    print("=============================") 