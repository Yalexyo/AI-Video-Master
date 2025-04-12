import numpy as np
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import re

logger = logging.getLogger(__name__)

class KeywordSearchTool:
    """视频内容关键词搜索工具"""
    
    def __init__(self):
        """初始化搜索工具"""
        self.model = None  # 延迟加载模型
    
    def _load_model(self):
        """加载语义搜索模型"""
        try:
            if self.model is None:
                logger.info("正在加载语义搜索模型...")
                self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("语义搜索模型加载完成")
        except Exception as e:
            logger.error(f"加载模型时出错: {str(e)}")
            raise
    
    def search_by_keywords(self, 
                         segments: List[Dict], 
                         keywords: List[str], 
                         threshold: float = 0.7) -> List[Dict]:
        """
        根据关键词搜索视频片段中的相关内容
        
        参数:
            segments: 视频片段列表，每个片段必须包含'text'字段
            keywords: 关键词列表
            threshold: 相似度阈值，默认0.7
            
        返回:
            匹配结果列表，按相似度排序
        """
        try:
            # 确保输入有效
            if not segments or not keywords:
                logger.warning("输入片段或关键词为空")
                return []
            
            # 过滤掉没有文本内容的片段
            valid_segments = [s for s in segments if s.get('text')]
            if not valid_segments:
                logger.warning("所有片段均无有效文本内容")
                return []
            
            # 加载模型
            self._load_model()
            
            # 编码关键词
            keyword_embeddings = self.model.encode(keywords)
            
            # 编码所有片段文本
            texts = [s['text'] for s in valid_segments]
            segment_embeddings = self.model.encode(texts)
            
            # 计算相似度并匹配
            results = []
            for i, segment in enumerate(valid_segments):
                # 计算与每个关键词的相似度
                best_score = -1
                best_keyword = None
                
                for j, keyword in enumerate(keywords):
                    # 计算余弦相似度
                    similarity = np.dot(segment_embeddings[i], keyword_embeddings[j]) / (
                        np.linalg.norm(segment_embeddings[i]) * np.linalg.norm(keyword_embeddings[j])
                    )
                    
                    # 更新最佳匹配
                    if similarity > best_score:
                        best_score = similarity
                        best_keyword = keyword
                
                # 如果相似度超过阈值，加入结果
                if best_score >= threshold:
                    match = segment.copy()
                    match['score'] = float(best_score)  # 确保分数可JSON序列化
                    match['keyword'] = best_keyword
                    results.append(match)
            
            # 排序结果
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results
        
        except Exception as e:
            logger.error(f"关键词搜索失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def highlight_keywords(self, text: str, keyword: str) -> str:
        """
        在文本中高亮显示与关键词语义相关的部分
        
        参数:
            text: 文本内容
            keyword: 关键词
            
        返回:
            带有HTML高亮标记的文本
        """
        # 简单实现：检测关键词或相似词的直接出现
        if not text or not keyword:
            return text
        
        # 获取关键词及其变体形式
        keyword_variants = [keyword]
        
        # 添加关键词的一些常见变体（简单模拟）
        # 在实际应用中，应该使用更复杂的NLP技术生成真正的语义相关词
        keyword_variants.extend([
            f"{keyword}的",
            f"关于{keyword}",
            f"{keyword}相关",
            f"与{keyword}有关"
        ])
        
        # 高亮所有变体
        result = text
        for variant in keyword_variants:
            # 使用正则表达式进行大小写不敏感匹配
            pattern = re.compile(re.escape(variant), re.IGNORECASE)
            result = pattern.sub(f'<span style="background-color: #FFEB3B; font-weight: bold;">{variant}</span>', result)
        
        return result
    
    def batch_process(self, video_urls: List[str], keywords: List[str], threshold: float = 0.7) -> Dict[str, List[Dict]]:
        """
        批量处理多个视频的关键词搜索
        
        参数:
            video_urls: 视频URL列表
            keywords: 关键词列表
            threshold: 相似度阈值
            
        返回:
            按视频分组的搜索结果
        """
        try:
            # 实际应用中，这里应该从视频中提取字幕或转录文本
            # 这里使用示例实现
            
            all_results = {}
            
            for url in video_urls:
                # 生成示例片段（在实际应用中应该处理真实视频）
                segments = []
                for i in range(5):  # 每个视频生成5个片段
                    segments.append({
                        'start': float(i * 5),
                        'end': float(i * 5 + 3),
                        'text': f"这是一个演示片段，包含关于产品功能、用户体验和市场反馈的内容。",
                        'source': url
                    })
                
                # 对当前视频执行搜索
                url_results = self.search_by_keywords(segments, keywords, threshold)
                
                # 存储结果
                all_results[url] = url_results
            
            return all_results
        
        except Exception as e:
            logger.error(f"批量处理失败: {str(e)}")
            raise 