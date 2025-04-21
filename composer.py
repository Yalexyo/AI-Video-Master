from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import os
import logging
import numpy as np
# 使用修复版的moviepy导入
from core.fixed_imports.moviepy_fixed import (
    VideoFileClip, 
    TextClip, 
    CompositeVideoClip, 
    concatenate_videoclips,
    ColorClip,
    vfx
)

logger = logging.getLogger(__name__)

@dataclass
class VideoSegment:
    """视频片段类：表示视频的一个片段"""
    start: float  # 开始时间点（秒）
    end: float    # 结束时间点（秒）
    text: str     # 相关文本（字幕或描述）
    score: float  # 匹配分数
    source: str   # 视频源（URL或文件路径）
    clip_path: Optional[str] = None  # 提取的片段文件路径

class VideoComposer:
    """视频合成引擎：将匹配的片段合成为最终输出视频"""
    
    def __init__(self, config: Dict):
        """初始化视频合成器"""
        self.config = config
        self.output_dir = config.get('OUTPUT_DIR', 'data/output/videos')
        os.makedirs(self.output_dir, exist_ok=True)
        self.temp_dir = config.get('TEMP_DIR', 'data/output/temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.transition_types = config.get('TRANSITION_TYPES', {
            'fade': {'duration': 1.0},
            'slide': {'direction': 'right', 'duration': 0.8},
            'zoom': {'factor': 1.2, 'duration': 1.2},
            'none': {}
        })
    
    def compose_video(self, segments: List[VideoSegment], settings: Dict) -> str:
        """
        合成最终视频
        
        Args:
            segments: 视频片段列表
            settings: 用户设置（转场、时长等）
            
        Returns:
            str: 输出视频路径
        """
        if not segments:
            logger.error("No segments provided for composition")
            raise ValueError("No segments provided for composition")
        
        try:
            # 1. 准备片段
            clips = self._prepare_clips(segments)
            
            # 2. 应用转场效果
            transition = settings.get('transition', 'fade')
            final_clips = self._apply_transitions(clips, transition, 
                                              settings.get('transition_duration', 1.0))
            
            # 3. 添加文本标语（如果有）
            if 'slogan' in settings and settings['slogan']:
                final_clips = self._add_slogan(final_clips, settings['slogan'])
            
            # 4. 渲染输出视频
            output_path = os.path.join(self.output_dir, 
                                      settings.get('output_name', 'final_video.mp4'))
            
            final_clip = concatenate_videoclips(final_clips)
            
            # 设置目标分辨率
            target_resolution = settings.get('resolution', (1280, 720))
            if target_resolution != (final_clip.w, final_clip.h):
                final_clip = final_clip.resize(target_resolution)
            
            # 导出视频
            final_clip.write_videofile(
                output_path, 
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=os.path.join(self.temp_dir, 'temp_audio.m4a'),
                remove_temp=True,
                fps=settings.get('fps', 30)
            )
            
            logger.info(f"Video successfully composed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error composing video: {str(e)}")
            raise
    
    def _prepare_clips(self, segments: List[VideoSegment]) -> List[VideoFileClip]:
        """准备视频片段"""
        clips = []
        
        for i, segment in enumerate(segments):
            if not segment.clip_path or not os.path.exists(segment.clip_path):
                logger.warning(f"Segment clip not found at {segment.clip_path}, skipping.")
                continue
                
            try:
                clip = VideoFileClip(segment.clip_path)
                # 添加字幕
                if segment.text:
                    txt_clip = TextClip(
                        segment.text, 
                        fontsize=24, 
                        color='white',
                        bg_color='rgba(0,0,0,0.5)',
                        font='Arial',
                        size=(clip.w * 0.9, None),
                        method='caption'
                    ).set_position(('center', 'bottom')).set_duration(clip.duration)
                    
                    clip = CompositeVideoClip([clip, txt_clip])
                
                clips.append(clip)
                logger.debug(f"Added clip {i+1}/{len(segments)}: {segment.clip_path}")
            except Exception as e:
                logger.error(f"Error loading clip {segment.clip_path}: {str(e)}")
        
        return clips
    
    def _apply_transitions(self, clips: List[VideoFileClip], 
                          transition_type: str, 
                          duration: float) -> List[VideoFileClip]:
        """应用转场效果"""
        if not clips:
            return []
            
        if len(clips) == 1 or transition_type == 'none':
            return clips
            
        result_clips = []
        transition_settings = self.transition_types.get(
            transition_type, 
            self.transition_types['fade']
        )
        
        # 使用相同的转场时长
        transition_duration = duration
        
        for i, clip in enumerate(clips):
            if i == 0:  # 第一个片段
                clip = clip.fadeout(transition_duration)
            elif i == len(clips) - 1:  # 最后一个片段
                clip = clip.fadein(transition_duration)
            else:  # 中间片段
                clip = clip.fadein(transition_duration).fadeout(transition_duration)
                
            result_clips.append(clip)
            
        return result_clips
    
    def _add_slogan(self, clips: List[VideoFileClip], slogan: str) -> List[VideoFileClip]:
        """添加宣传语片尾"""
        if not clips:
            return []
            
        # 获取第一个片段的分辨率作为标准
        width, height = clips[0].size
        
        # 创建片尾标语
        duration = 5.0  # 宣传语持续5秒
        
        txt_clip = TextClip(
            slogan,
            fontsize=36,
            color='white',
            bg_color='black',
            font='Arial-Bold',
            size=(width * 0.8, None),
            method='caption'
        ).set_position('center').set_duration(duration)
        
        # 创建背景
        bg_clip = TextClip(
            " ", 
            color='white', 
            bg_color='black',
            size=(width, height),
            fontsize=1
        ).set_duration(duration)
        
        # 合成片尾
        end_clip = CompositeVideoClip([bg_clip, txt_clip])
        end_clip = end_clip.fadein(1.0)
        
        # 添加到片段列表
        clips.append(end_clip)
        
        return clips
