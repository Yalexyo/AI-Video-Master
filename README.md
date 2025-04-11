# AI视频分析系统精简版

## 项目结构

```
videosynth/
├── api.py                      # FastAPI服务入口
├── app.py                      # Streamlit前端入口
├── config.py                   # 配置管理
├── requirements.txt            # 依赖列表
│
├── core/                       # 核心处理模块
│   ├── __init__.py
│   ├── wordlist.py             # 热词管理
│   ├── processor.py            # 视频处理流水线
│   └── composer.py             # 视频合成
│
├── frontend/                   # 前端界面
│   ├── pages/
│   │   ├── words.py           # 热词管理
│   │   ├── setup.py           # 参数设置
│   │   └── output.py          # 输出管理
│   └── static/                # 静态资源
│
├── data/                       # 数据目录
│   ├── input/                 # 输入文件
│   └── output/                # 输出结果
│
├── tests/                      # 测试用例
└── docs/                       # 文档
```

## 核心模块说明

### processor.py
```python
from dataclasses import dataclass
from typing import List
from sentence_transformers import SentenceTransformer

@dataclass
class VideoSegment:
    start: float
    end: float 
    text: str
    score: float

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def process_pipeline(urls: List[str], config: dict) -> List[VideoSegment]:
    """可配置处理流水线"""
    steps = config.get('PROCESS_STEPS', ['subtitles', 'analysis', 'matching'])
    
    results = []
    if 'subtitles' in steps:
        # 字幕生成逻辑
        ...
    
    if 'analysis' in steps:
        # 维度分析逻辑
        ...
    
    if 'matching' in steps:
        # 使用MiniLM模型计算相似度
        embeddings = model.encode(texts)
        ...
    
    return results
```

### frontend/pages/setup.py
```python
import streamlit as st

def show_settings():
    """用户设置界面"""
    settings = {}
    
    with st.expander("⚙️ 高级设置", expanded=True):
        cols = st.columns(3)
        
        # 维度设置
        with cols[0]:
            st.subheader("维度配置")
            settings['dimensions'] = st.text_area(
                "维度结构", 
                value="品牌认知\n  产品特性\n    功能\n    外观\n用户需求",
                height=150
            )
        
        # 匹配规则
        with cols[1]:
            st.subheader("匹配规则")
            settings['threshold'] = st.slider(
                "相似度阈值", 
                0.5, 1.0, 0.7
            )
            settings['priority'] = st.selectbox(
                "优先维度",
                ["一级维度", "二级维度", "综合评分"]
            )
        
        # 转场效果
        with cols[2]:
            st.subheader("视频效果")
            settings['transition'] = st.selectbox(
                "转场效果",
                ["淡入淡出", "滑动", "缩放", "无"]
            )
            settings['duration'] = st.number_input(
                "转场时长(秒)", 
                0.5, 2.0, 1.0
            )
    
    return settings
```

## 安装运行
```bash
# 安装依赖
pip install -r requirements.txt

# 启动前端
streamlit run app.py

# 启动API服务
uvicorn api:app --reload
