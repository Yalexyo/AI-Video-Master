import streamlit as st
import os
from typing import Optional, Dict, List, Tuple
import tempfile
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import logging

logger = logging.getLogger(__name__)

class VideoPreview:
    """视频预览组件：展示视频片段和效果预览"""
    
    def __init__(self, temp_dir: str = "data/output/temp"):
        """初始化视频预览器"""
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def render_preview(self, segments: List[Dict], 
                      settings: Dict,
                      with_controls: bool = True):
        """渲染视频预览"""
        if not segments:
            st.info("未找到匹配的视频片段，无法预览。")
            return
        
        # 显示预览控件
        if with_controls:
            self._render_controls(segments, settings)
        
        # 显示片段预览
        self._render_segment_previews(segments, settings)
        
        # 显示转场预览
        if len(segments) > 1:
            self._render_transition_preview(settings)
        
        # 显示标语预览
        if settings.get('slogan'):
            self._render_slogan_preview(settings)
    
    def _render_controls(self, segments: List[Dict], settings: Dict):
        """渲染预览控件"""
        st.subheader("预览设置")
        
        cols = st.columns(3)
        
        with cols[0]:
            # 选择片段
            segment_options = [f"片段 {i+1}: {seg.get('text', '')[:20]}..." 
                              for i, seg in enumerate(segments)]
            selected_idx = st.selectbox(
                "查看片段",
                range(len(segment_options)),
                format_func=lambda i: segment_options[i]
            )
        
        with cols[1]:
            # 转场效果
            transition = st.selectbox(
                "转场效果",
                ["淡入淡出", "滑动", "缩放", "无"],
                index=["淡入淡出", "滑动", "缩放", "无"].index(
                    settings.get('transition', '淡入淡出')
                )
            )
            settings['transition'] = transition
        
        with cols[2]:
            # 转场时长
            duration = st.slider(
                "转场时长(秒)",
                0.5, 2.0, 
                value=settings.get('transition_duration', 1.0),
                step=0.1
            )
            settings['transition_duration'] = duration
    
    def _render_segment_previews(self, segments: List[Dict], settings: Dict):
        """渲染片段预览"""
        st.subheader("片段预览")
        
        # 创建多列布局
        cols = st.columns(min(3, len(segments)))
        
        for i, segment in enumerate(segments[:3]):  # 仅显示前3个
            with cols[i % 3]:
                # 生成片段预览图像
                preview_img = self._generate_segment_preview(
                    segment, 
                    f"片段 {i+1}", 
                    settings
                )
                
                if preview_img:
                    st.image(
                        preview_img, 
                        caption=f"片段 {i+1}: {segment.get('text', '')[:20]}...",
                        use_container_width=True
                    )
        
        # 如果有更多片段
        if len(segments) > 3:
            st.info(f"还有 {len(segments) - 3} 个片段未显示")
    
    def _generate_segment_preview(self, 
                                segment: Dict, 
                                label: str, 
                                settings: Dict) -> Optional[Image.Image]:
        """生成片段预览图像"""
        try:
            # 创建示例预览图像
            width, height = 400, 225  # 16:9 比例
            img = Image.new('RGB', (width, height), color=(50, 50, 50))
            draw = ImageDraw.Draw(img)
            
            # 添加背景网格
            for x in range(0, width, 20):
                draw.line([(x, 0), (x, height)], fill=(60, 60, 60), width=1)
            for y in range(0, height, 20):
                draw.line([(0, y), (width, y)], fill=(60, 60, 60), width=1)
            
            # 添加标签
            try:
                font = ImageFont.truetype("Arial", 24)
            except IOError:
                font = ImageFont.load_default()
                
            draw.text(
                (width // 2, height // 2), 
                label, 
                fill=(255, 255, 255), 
                font=font, 
                anchor="mm"
            )
            
            # 添加文本
            if segment.get('text'):
                text = segment['text']
                if len(text) > 50:
                    text = text[:47] + "..."
                
                try:
                    small_font = ImageFont.truetype("Arial", 14)
                except IOError:
                    small_font = ImageFont.load_default()
                
                # 添加半透明背景
                text_w, text_h = small_font.getsize(text) if hasattr(small_font, 'getsize') else (width * 0.8, 20)
                draw.rectangle(
                    [(width // 2 - text_w // 2 - 10, height - 40 - 10), 
                     (width // 2 + text_w // 2 + 10, height - 10)],
                    fill=(0, 0, 0, 128)
                )
                
                draw.text(
                    (width // 2, height - 25), 
                    text, 
                    fill=(255, 255, 255), 
                    font=small_font, 
                    anchor="mm"
                )
            
            return img
        
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}")
            return None
    
    def _render_transition_preview(self, settings: Dict):
        """渲染转场效果预览"""
        st.subheader("转场效果预览")
        
        transition = settings.get('transition', '淡入淡出')
        duration = settings.get('transition_duration', 1.0)
        
        # 创建示例转场图像序列
        images = []
        frames = 5  # 显示5帧
        
        for i in range(frames):
            progress = i / (frames - 1)  # 0 到 1
            
            # 创建帧图像
            width, height = 300, 169  # 16:9 比例
            img = Image.new('RGB', (width, height), color=(50, 50, 50))
            draw = ImageDraw.Draw(img)
            
            # 根据转场类型绘制不同效果
            if transition == '淡入淡出':
                # 左侧图像淡出
                opacity_left = 255 * (1 - progress)
                # 右侧图像淡入
                opacity_right = 255 * progress
                
                # 分割线
                draw.line(
                    [(width // 2, 0), (width // 2, height)], 
                    fill=(100, 100, 100), 
                    width=2
                )
                
                # 左右区域
                draw.rectangle(
                    [(0, 0), (width // 2 - 1, height)],
                    fill=(200, 100, 100, int(opacity_left))
                )
                draw.rectangle(
                    [(width // 2 + 1, 0), (width, height)],
                    fill=(100, 200, 100, int(opacity_right))
                )
                
            elif transition == '滑动':
                # 滑动效果
                offset = int(width * progress)
                
                # 绘制移动的区块
                draw.rectangle(
                    [(0 - offset, 0), (width - offset, height)],
                    fill=(200, 100, 100)
                )
                draw.rectangle(
                    [(width - offset, 0), (width * 2 - offset, height)],
                    fill=(100, 200, 100)
                )
                
            elif transition == '缩放':
                # 缩放效果
                scale = 0.5 + 0.5 * progress
                
                center_x, center_y = width // 2, height // 2
                size = int(min(width, height) * scale * 0.4)
                
                # 绘制缩放的区块
                if progress < 0.5:
                    # 第一个图形缩小
                    fill_color = (200, 100, 100)
                else:
                    # 第二个图形放大
                    fill_color = (100, 200, 100)
                    
                draw.ellipse(
                    [(center_x - size, center_y - size), 
                     (center_x + size, center_y + size)],
                    fill=fill_color
                )
            
            else:  # 'none'
                # 没有转场，直接切换
                if progress < 0.5:
                    draw.rectangle(
                        [(0, 0), (width, height)],
                        fill=(200, 100, 100)
                    )
                else:
                    draw.rectangle(
                        [(0, 0), (width, height)],
                        fill=(100, 200, 100)
                    )
            
            # 添加帧标签
            try:
                font = ImageFont.truetype("Arial", 14)
            except IOError:
                font = ImageFont.load_default()
                
            draw.text(
                (width // 2, height - 15), 
                f"帧 {i+1}", 
                fill=(255, 255, 255), 
                font=font, 
                anchor="mm"
            )
            
            images.append(img)
        
        # 显示帧序列
        st.write(f"转场类型: **{transition}**, 持续时间: **{duration}秒**")
        
        cols = st.columns(len(images))
        for i, img in enumerate(images):
            with cols[i]:
                st.image(img, use_container_width=True)
    
    def _render_slogan_preview(self, settings: Dict):
        """渲染标语预览"""
        st.subheader("标语预览")
        
        slogan = settings.get('slogan', '')
        
        # 创建标语预览图像
        width, height = 600, 337  # 16:9 比例
        img = Image.new('RGB', (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 添加文本
        try:
            font = ImageFont.truetype("Arial", 36)
        except IOError:
            font = ImageFont.load_default()
            
        # 绘制文本
        text_w, text_h = font.getsize(slogan) if hasattr(font, 'getsize') else (width * 0.8, 40)
        
        draw.text(
            (width // 2, height // 2), 
            slogan, 
            fill=(255, 255, 255), 
            font=font, 
            anchor="mm"
        )
        
        st.image(img, use_container_width=True)
        
    def get_video_display(self, video_path: str, width: int = 720):
        """获取视频显示HTML"""
        if not os.path.exists(video_path):
            return None
            
        # 获取视频mime类型
        mime_type = 'video/mp4'  # 默认为mp4
        if video_path.endswith('.webm'):
            mime_type = 'video/webm'
        elif video_path.endswith('.ogg'):
            mime_type = 'video/ogg'
            
        video_file = open(video_path, 'rb')
        video_bytes = video_file.read()
        video_file.close()
        
        video_b64 = base64.b64encode(video_bytes).decode()
        
        html = f"""
        <video width="{width}" controls>
            <source src="data:{mime_type};base64,{video_b64}">
            您的浏览器不支持视频标签。
        </video>
        """
        return html
