import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 处理流程配置
    PROCESS_STEPS = [
        'subtitles',
        'analysis', 
        'matching',
        'compilation'
    ]
    
    # 视频参数
    TRANSITION_TYPES = {
        'fade': {'duration': 1.0},
        'slide': {'direction': 'right', 'duration': 0.8},
        'zoom': {'factor': 1.2, 'duration': 1.2}
    }
    
    # 默认维度结构
    DEFAULT_DIMENSIONS = {
        'level1': '品牌认知',
        'level2': ['产品特性', '用户需求'],
        'level3': {
            '产品特性': ['功能', '外观', '性能'],
            '用户需求': ['场景', '痛点', '期望']
        }
    }
    
    # API配置
    @property
    def DASHSCOPE_API_KEY(self):
        return os.getenv('DASHSCOPE_API_KEY', '')
    
    # 路径配置
    INPUT_DIR = 'data/input'
    OUTPUT_DIR = 'data/output'
    CACHE_DIR = 'data/cache'

config = Config()
