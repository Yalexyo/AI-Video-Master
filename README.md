# AI视频分析系统

## 系统简介
AI视频分析系统是一个强大的智能视频处理工具，能够基于预设维度结构和关键词分析视频内容，自动提取匹配的视频片段，并合成精简版视频。系统特别适用于品牌分析、营销内容筛选、用户研究等场景，帮助用户从大量视频素材中快速提取有价值的内容。

## 用户操作指南

### 环境准备

1. **安装依赖**
   首次使用需要安装所需依赖库：
   ```bash
   # 在项目根目录下运行
   pip install -r requirements.txt
   ```

2. **启动系统**
   ```bash
   # 在项目根目录下运行
   streamlit run app.py
   ```
   运行命令后，系统会自动在浏览器中打开界面（通常是http://localhost:8501）

### 使用流程

#### 1. 项目管理
系统启动后，在左侧导航栏可以：
- 选择已有项目
- 创建新项目
- 删除不需要的项目

每个项目可以保存独立的视频分析设置和结果，方便对比和管理。

#### 2. 热词管理
在热词管理页面，您可以：
- 创建和维护热词表
- 导入/导出热词
- 设置热词权重和语言

热词用于增强视频内容的匹配精度，对重要概念赋予更高的权重。

#### 3. 维度设置
在维度设置页面，您可以：
- 使用预设维度模板（系统会自动加载"initial key dimensions"模板）
- 创建自定义维度结构
- 管理三级维度体系

维度结构是视频分析的核心，定义了内容分类体系。例如：
- 一级维度：品牌认知
- 二级维度：产品特性、用户需求
- 三级维度：产品特性下有功能、外观、性能等

#### 4. 视频分析
在视频分析页面，您可以：
- 输入视频URL或上传本地视频
- 选择分析维度
- 设置分析参数（相似度阈值、维度优先级等）
- 执行视频分析

系统将自动：
1. 提取视频字幕
2. 根据维度结构分析内容
3. 匹配相关片段
4. 生成分析结果

#### 5. 结果管理
在结果管理页面，您可以：
- 查看匹配的视频片段
- 预览合成效果
- 调整片段选择
- 导出最终视频

## 系统处理逻辑与核心模块

### 1. 数据流架构

用户输入 → 视频处理 → 内容分析 → 片段筛选 → 视频合成 → 结果展示

### 2. 核心模块功能

#### `session/state.py` - 会话状态管理
负责管理用户设置、项目配置和分析结果的保存与加载。
```python
# 系统启动时自动加载初始维度
def get_default_settings(self):
    # 加载initial_key_dimensions作为默认维度
    try:
        template_path = '...initial_key_dimensions.json'
        with open(template_path, 'r') as f:
            initial_template = json.load(f)
            # 设置维度数据结构...
    except Exception as e:
        logger.error(f"加载维度模板失败: {str(e)}")
    # 返回默认设置...
```

#### `core/processor.py` - 视频处理引擎
处理视频内容提取、分析和匹配的核心逻辑。
```python
def process_pipeline(urls, config):
    """处理视频的主要流水线"""
    # 提取字幕
    # 分析内容
    # 匹配维度
    # 返回匹配片段
```

#### `core/composer.py` - 视频合成引擎
根据分析结果和用户参数合成最终视频。
```python
def compose_video(segments, settings):
    """合成最终视频"""
    # 提取原始片段
    # 应用转场效果
    # 添加字幕和标注
    # 输出合成视频
```

#### `ui/components/dimension_editor.py` - 维度编辑器组件
提供维度结构的可视化编辑界面。
```python
def render(self):
    """渲染维度编辑器界面"""
    # 显示维度结构
    # 提供编辑功能
    # 返回更新后的维度数据
```

#### `keyword_search.py` - 关键词搜索模块
实现基于关键词的语义搜索功能，在视频内容中查找匹配片段。
```python
def semantic_search(query, corpus, threshold=0.7):
    """语义搜索功能"""
    # 计算查询词嵌入
    # 计算语料库嵌入
    # 计算相似度
    # 返回匹配结果
```

### 3. 维度分析原理

系统使用预训练的语言模型计算视频内容与维度描述之间的语义相似性：

1. 将视频字幕分割为句子或段落
2. 使用MiniLM等模型将文本转换为高维向量
3. 计算文本与维度描述的余弦相似度
4. 根据相似度阈值筛选匹配片段
5. 综合考虑维度优先级和权重排序结果

## 高级用法

### 自定义维度模板
在`data/dimensions/`目录下创建新的JSON文件，格式参考`initial_key_dimensions.json`。

### 批量处理
使用core模块的API可以实现批量视频处理：
```python
from core.processor import VideoProcessor
processor = VideoProcessor()
results = processor.batch_process(video_list, settings)
```

## 常见问题解答

1. **Q: 系统支持哪些视频格式?**  
   A: 系统支持大多数常见视频格式，包括MP4, AVI, MOV等。

2. **Q: 如何提高匹配精度?**  
   A: 可以调整相似度阈值、优化维度描述、添加相关热词。

3. **Q: 如何处理长视频?**  
   A: 系统会自动分割长视频，也可以在设置中调整片段处理策略。

## 安装环境要求

- Python 3.8或更高版本
- 足够的存储空间用于视频处理
- 建议使用GPU加速（用于视频处理和语义匹配）

系统在以下虚拟环境中运行:
```
/Users/apple/Desktop/AI video/videoAnalysis_v1.0/.venv/
```

## 更新日志

最近更新:
- 优化维度设置功能，自动加载初始维度模板
- 修复了维度分析页面的问题，允许用户只设置一级维度也能进行分析 
- 修复了UI组件重复key的问题
- 添加关键词搜索功能

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

## 安装运行
```bash
# 安装依赖
pip install -r requirements.txt

# 启动前端
streamlit run app.py

# 启动API服务
uvicorn api:app --reload
