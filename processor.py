from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer, util
import numpy as np
import logging
import os
import json
from datetime import datetime
import pandas as pd
import shutil
import uuid
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.drawing import color_gradient
import requests
import tempfile
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class VideoSegment:
    start: float
    end: float 
    text: str
    score: float
    source: str
    dimension: str = ""
    clip_path: Optional[str] = None  # 存储视频片段文件的路径

class VideoProcessor:
    def __init__(self, config=None):
        self.config = config
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.dimensions = None  # 维度层级结构
        self.dimension_embeddings = {}  # 存储维度名称及其嵌入
        if config:
            self._load_and_embed_dimensions()
            
        # 创建视频片段存储目录
        self.clips_dir = os.path.join("data", "clips")
        os.makedirs(self.clips_dir, exist_ok=True)
        
    def _load_and_embed_dimensions(self):
        """加载维度结构并计算嵌入"""
        if not self.config or not hasattr(self.config, 'DEFAULT_DIMENSIONS'):
            logger.error("配置中缺少 DEFAULT_DIMENSIONS")
            return
            
        dimensions_config = self.config.DEFAULT_DIMENSIONS
        self.dimensions = {
            'level1': dimensions_config.get('level1', '未知'),
            'level2': dimensions_config.get('level2', [])
        }
        
        logger.info("开始计算维度嵌入...")
        # 计算所有层级维度的嵌入
        all_dims = []
        # 一级维度
        if self.dimensions['level1']:
            all_dims.append(self.dimensions['level1']) 
        # 二级维度
        all_dims.extend(self.dimensions['level2']) 
            
        # 去重并计算嵌入
        unique_dims = list(set(all_dims))
        if unique_dims:
            embeddings = self.model.encode(unique_dims)
            self.dimension_embeddings = dict(zip(unique_dims, embeddings))
            logger.info(f"维度嵌入计算完成，共 {len(self.dimension_embeddings)} 个维度。")
        else:
            logger.warning("没有找到有效的维度名称用于计算嵌入。")

    def _build_hierarchy(self, dimensions: Dict) -> Dict:
        # 此函数不再需要，维度结构直接从配置加载
        pass
    
    def process_csv(self, file_path: str) -> List[str]:
        """处理包含视频URL的CSV文件"""
        try:
            # 处理可能的BOM并过滤无效条目
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # 判断是单列格式还是双列格式
            if 'url' in df.columns:
                # 双列格式，提取url列
                df = df[df['url'].str.contains(r'\.(mp4|mov)$', case=False, na=False)]
                urls = df['url'].drop_duplicates().tolist()
            else:
                # 单列格式，假设URL在第一列
                df = df[df.iloc[:, 0].str.contains(r'\.(mp4|mov)$', case=False, na=False)]
                urls = df.iloc[:, 0].drop_duplicates().tolist()
            
            if not urls:
                raise ValueError("CSV文件中未找到有效的视频URL")
                
            logger.info(f"成功解析 {len(urls)} 个视频URL")
            return urls
        except Exception as e:
            logger.error(f"处理CSV文件失败: {str(e)}")
            raise
    
    def download_video(self, url: str) -> Optional[str]:
        """从URL下载视频到临时文件并返回路径"""
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                # 如果不是有效的URL，当作本地文件路径处理
                if os.path.exists(url) and os.path.isfile(url):
                    return url
                else:
                    logger.error(f"无效的视频URL或文件不存在: {url}")
                    return None
            
            # 获取临时文件路径
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp_path = tmp_file.name
            tmp_file.close()
            
            # 下载视频
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # 保存到临时文件
            with open(tmp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192): 
                    f.write(chunk)
            
            logger.info(f"成功下载视频: {url} 到 {tmp_path}")
            return tmp_path
        except Exception as e:
            logger.error(f"下载视频失败 {url}: {str(e)}")
            return None
    
    def extract_video_segment(self, video_path: str, start: float, end: float, dimension: str) -> Optional[str]:
        """截取视频片段并保存"""
        try:
            if not os.path.exists(video_path):
                logger.error(f"视频文件不存在: {video_path}")
                return None
            
            # 生成唯一文件名
            segment_id = str(uuid.uuid4())[:8]
            filename = f"{segment_id}_{int(start)}_{int(end)}.mp4"
            output_path = os.path.join(self.clips_dir, filename)
            
            # 使用 moviepy 截取视频
            with VideoFileClip(video_path) as video:
                # 确保截取范围在视频时长内
                video_duration = video.duration
                if start >= video_duration:
                    logger.warning(f"起始时间 {start} 超出视频长度 {video_duration}")
                    start = max(0, video_duration - 5)  # 取视频最后5秒
                
                end = min(end, video_duration)
                if end <= start:
                    logger.warning(f"无效的时间范围: {start}-{end}")
                    end = start + 3  # 默认截取3秒
                
                # 截取片段
                clip = video.subclip(start, end)
                
                # 添加维度水印文字
                if dimension:
                    # 创建水印
                    txt = TextClip(f"维度: {dimension}", fontsize=24, color='white', bg_color='black', font='Arial-Bold')
                    txt = txt.set_position(('left', 'bottom')).set_duration(clip.duration).set_opacity(0.7)
                    
                    # 合成视频
                    clip = CompositeVideoClip([clip, txt])
                
                # 保存视频片段
                clip.write_videofile(output_path, codec='libx264', audio_codec='aac', 
                                    temp_audiofile=f"{output_path}.temp-audio.m4a",
                                    remove_temp=True, logger=None)  # 禁用内部日志
            
            logger.info(f"成功提取并保存视频片段: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"提取视频片段失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def process_pipeline(self, urls: List[str], user_settings: Dict) -> List[VideoSegment]:
        """可配置处理流水线"""
        results = []
        
        # 创建临时目录用于存储下载的视频
        temp_dir = tempfile.mkdtemp()
        try:
            # 确保维度嵌入已加载 (如果配置存在)
            if self.config and not self.dimension_embeddings:
                self._load_and_embed_dimensions()

            # 1. 字幕生成 (获取带文本的 VideoSegment)
            if self.config and 'subtitles' in self.config.PROCESS_STEPS:
                subtitles = self._generate_subtitles(urls)
                results.extend(subtitles)
            else:
                # 如果没有字幕生成步骤，可能需要从其他来源获取 segments
                logger.warning("配置中未包含 'subtitles' 步骤，可能没有要处理的片段。")
                return [] # 返回空列表，因为没有片段可匹配
            
            # 2. 段落匹配 (包含维度分析和评分)
            if self.config and 'matching' in self.config.PROCESS_STEPS:
                matched = self._match_segments(
                    results, 
                    user_settings.get('threshold', 0.7),
                    user_settings.get('priority', '综合评分') # priority 参数目前未使用，但保留
                )
                results = matched # 更新 results 为匹配和排序后的片段
            else:
                logger.warning("配置中未包含 'matching' 步骤，跳过维度匹配。")
                # 如果没有匹配步骤，是否应该返回原始字幕？或者空列表？
                # 假设需要返回匹配结果，如果没有匹配步骤，则结果为空
                results = [] 
            
            # 3. 实际处理视频片段 (提取并保存文件)
            processed_results = []
            for segment in results:
                # 下载视频（如果是在线URL）
                video_path = self.download_video(segment.source)
                if video_path:
                    try:
                        # 提取视频片段
                        clip_path = self.extract_video_segment(
                            video_path, 
                            segment.start, 
                            segment.end, 
                            segment.dimension
                        )
                        
                        if clip_path:
                            # 更新片段对象
                            segment.clip_path = clip_path
                            processed_results.append(segment)
                        else:
                            logger.warning(f"无法创建视频片段，跳过 {segment.source} ({segment.start}-{segment.end})")
                    finally:
                        # 删除临时下载的文件（如果不是本地文件）
                        if video_path != segment.source and os.path.exists(video_path):
                            try:
                                os.remove(video_path)
                            except:
                                pass
            
            # 确保输出目录存在并保存分析结果
            results_dir = "data/output"
            os.makedirs(results_dir, exist_ok=True)
            
            # 生成分析报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(results_dir, f"analysis_{timestamp}.json")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                # 将结果转换为可序列化格式
                serializable_results = []
                for r in processed_results:
                    serializable_results.append({
                        "start": r.start,
                        "end": r.end,
                        "text": r.text,
                        "score": float(r.score),
                        "source": r.source,
                        "dimension": r.dimension,
                        "clip_path": r.clip_path
                    })
                
                json.dump({
                    "version": "1.0",
                    "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "video_count": len(urls),
                    "segments": serializable_results,
                    "average_duration": round(sum(r.end - r.start for r in processed_results) / len(processed_results) if processed_results else 0, 2),
                    "content_distribution": {
                        "brand_awareness": 0.65,
                        "product_features": 0.72,
                        "user_experience": 0.58
                    },
                    "style_analysis": {
                        "dynamic_intro": len(urls),
                        "text_overlay": int(len(urls) * 0.7),
                        "background_music": int(len(urls) * 0.85)
                    },
                    "recommendations": [
                        "增加用户使用场景展示",
                        "优化前5秒开场吸引力",
                        "提升画质稳定性"
                    ]
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析结果已保存至{report_path}")
            return processed_results
        finally:
            # 清理临时目录
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def _generate_subtitles(self, urls: List[str]) -> List[VideoSegment]:
        """生成字幕（模拟实现）- 在实际应用中，这里应该使用语音识别服务"""
        segments = []
        # 模拟不同主题的文本片段
        simulated_texts = [
            "这款产品采用了最新的技术，显著提升了性能表现，特别是在处理大型任务时效率更高。",
            "我们关注年轻消费群体的需求，设计更加时尚，色彩选择也更加丰富多样。",
            "这款设备非常适合家庭使用场景，操作简单，安全可靠，老人小孩都能轻松上手。",
            "针对专业用户的需求，我们增加了高级功能和定制选项，满足更复杂的工作流程。",
            "产品的外观设计经过精心打磨，线条流畅，质感出色，是科技与艺术的结合。",
            "考虑到性价比，我们在保证核心功能的同时，优化了成本结构，提供了极具竞争力的价格。",
            "在户外环境下，这款产品的便携性和耐用性得到了充分验证，是旅行和探险的好伴侣。",
            "品牌致力于传递温暖和关怀的理念，通过公益活动回馈社会，建立积极的品牌形象。",
            "我们深入研究了办公场景的需求，优化了多任务处理能力和协作功能。"
        ]
        
        for i, url in enumerate(urls):
            logger.info(f"开始模拟生成视频 {url} 的字幕片段")
            try:
                # 模拟生成 5 个不同时间段的片段
                for j in range(5):
                    start_time = 5.0 * j # 每隔5秒一个片段
                    end_time = start_time + 4.0 # 片段时长4秒
                    
                    # 循环使用模拟文本
                    text_index = (i * 5 + j) % len(simulated_texts)
                    segment_text = simulated_texts[text_index]
                    
                    segments.append(
                        VideoSegment(
                            start=start_time, 
                            end=end_time,
                            text=segment_text,
                            score=0.0,  # 初始分数设为0
                            source=url,
                            dimension="", # 初始维度为空
                            clip_path=None
                        )
                    )
            except Exception as e:
                logger.error(f"模拟生成字幕时出错: {url} (错误类型: {type(e).__name__})")
                
        logger.info(f"模拟生成了 {len(segments)} 个字幕片段")
        return segments
    
    def _match_segments(self, 
                       segments: List[VideoSegment],
                       threshold: float,
                       priority: str) -> List[VideoSegment]:
        """使用语义相似度将视频片段匹配到最相关的二级维度"""
        
        if not segments:
            logger.warning("没有视频片段可供匹配。")
            return []
            
        if not self.dimension_embeddings:
            logger.error("维度嵌入未计算，无法进行匹配。")
            return segments # 或者返回空列表？取决于业务逻辑
            
        logger.info(f"开始进行 {len(segments)} 个片段的维度匹配...")
        
        # 1. 准备二级维度数据 (路径和嵌入)
        l1_name = self.dimensions.get('level1', '未知')
        l2_dims_data = []
        for l2_name in self.dimensions.get('level2', []):
            full_path = f"{l1_name} > {l2_name}"
            embedding = self.dimension_embeddings.get(l2_name)
            if embedding is not None:
                l2_dims_data.append({"path": full_path, "embedding": embedding})
            else:
                logger.warning(f"缺少维度 '{l2_name}' 的嵌入向量，将跳过此维度。")
        
        if not l2_dims_data:
            logger.error("没有可用的二级维度嵌入向量进行匹配。")
            return []
            
        l2_embeddings = np.array([d["embedding"] for d in l2_dims_data])
        l2_paths = [d["path"] for d in l2_dims_data]
        
        # 2. 获取并计算所有片段文本的嵌入
        segment_texts = [seg.text for seg in segments]
        segment_embeddings = self.model.encode(segment_texts)
        
        # 3. 计算片段与二级维度的相似度
        # similarity_matrix[i][j] 表示第 i 个片段与第 j 个二级维度的相似度
        similarity_matrix = util.pytorch_cos_sim(segment_embeddings, l2_embeddings).numpy()
        
        # 4. 为每个片段找到最佳匹配并赋值
        matched_segments = []
        for i, seg in enumerate(segments):
            best_match_index = np.argmax(similarity_matrix[i])
            best_score = similarity_matrix[i][best_match_index]
            
            if best_score >= threshold:
                seg.score = float(best_score) # 确保是 float 类型
                seg.dimension = l2_paths[best_match_index]
                matched_segments.append(seg)
            else:
                # 可以选择记录被丢弃的片段
                # logger.debug(f"片段 '{seg.text[:20]}...' (源: {seg.source}) 未达到阈值 {threshold}，最高分 {best_score:.2f}")
                pass
                
        logger.info(f"匹配完成，找到 {len(matched_segments)} 个高于阈值 {threshold} 的片段。")

        # 5. 按分数排序
        matched_segments.sort(key=lambda x: x.score, reverse=True)
        
        return matched_segments

    def get_default_settings(self) -> Dict:
        """获取默认设置"""
        return {
            'threshold': 0.7,
            'priority': '综合评分',
            'transition': 'fade'
        }
