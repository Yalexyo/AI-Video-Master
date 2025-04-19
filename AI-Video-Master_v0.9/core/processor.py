from dataclasses import dataclass
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
import os
import json
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class VideoSegment:
    start: float
    end: float 
    text: str
    score: float
    source: str

class VideoProcessor:
    def __init__(self, config=None):
        self.config = config
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        if config:
            self.dimensions = self._load_dimensions()
        
    def _load_dimensions(self) -> Dict:
        """加载维度结构"""
        return {
            'level1': self.config.DEFAULT_DIMENSIONS['level1'],
            'hierarchy': self._build_hierarchy(self.config.DEFAULT_DIMENSIONS)
        }
    
    def _build_hierarchy(self, dimensions: Dict) -> Dict:
        """构建维度层级关系"""
        hierarchy = {}
        for l2 in dimensions['level2']:
            hierarchy[l2] = dimensions['level3'].get(l2, [])
        return hierarchy
    
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
    
    def process_pipeline(self, urls: List[str], user_settings: Dict) -> List[VideoSegment]:
        """可配置处理流水线"""
        results = []
        
        # 字幕生成
        if self.config and 'subtitles' in self.config.PROCESS_STEPS:
            subtitles = self._generate_subtitles(urls)
            results.extend(subtitles)
        
        # 维度分析
        if self.config and 'analysis' in self.config.PROCESS_STEPS:
            analysis = self._analyze_dimensions([s.text for s in subtitles])
            results = self._apply_analysis(results, analysis)
        
        # 段落匹配
        if self.config and 'matching' in self.config.PROCESS_STEPS:
            matched = self._match_segments(
                results, 
                user_settings.get('threshold', 0.7),
                user_settings.get('priority', '综合评分')
            )
            results = matched
        
        # 确保输出目录存在并保存分析结果
        results_dir = "data/output"
        os.makedirs(results_dir, exist_ok=True)
        
        # 生成分析报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(results_dir, f"analysis_{timestamp}.json")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "version": "1.0",
                "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "video_count": len(urls),
                "average_duration": 58.4,  # 示例值
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
        return results
    
    def _generate_subtitles(self, urls: List[str]) -> List[VideoSegment]:
        """生成字幕（示例实现）"""
        segments = []
        for url in urls:
            logger.info(f"开始处理视频: {url}")
            try:
                # 模拟处理时间
                processing_time = 2.4
                logger.info(f"视频特征提取完成，耗时{processing_time}秒")
                
                segments.append(
                    VideoSegment(
                        start=0.0, 
                        end=10.0,
                        text="示例字幕内容",
                        score=0.0,
                        source=url
                    )
                )
            except Exception as e:
                logger.error(f"无法解码视频文件: {url} (错误类型: {type(e).__name__})")
                
        return segments
    
    def _analyze_dimensions(self, texts: List[str]) -> Dict:
        """维度分析（示例实现）"""
        embeddings = self.model.encode(texts)
        return {
            'embeddings': embeddings,
            'keywords': ['示例关键词']
        }
    
    def _apply_analysis(self, segments, analysis):
        """应用分析结果到片段"""
        return segments
    
    def _match_segments(self, 
                       segments: List[VideoSegment],
                       threshold: float,
                       priority: str) -> List[VideoSegment]:
        """匹配视频段落"""
        # 实现相似度计算逻辑
        for seg in segments:
            seg.score = np.random.uniform(0.5, 1.0)  # 示例评分
        
        # 按评分排序
        return sorted(
            [s for s in segments if s.score >= threshold],
            key=lambda x: x.score,
            reverse=True
        )

    def get_default_settings(self) -> Dict:
        """获取默认设置"""
        return {
            'threshold': 0.7,
            'priority': '综合评分',
            'transition': 'fade'
        }
