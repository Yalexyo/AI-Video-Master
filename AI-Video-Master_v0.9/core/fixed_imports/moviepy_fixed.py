
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
