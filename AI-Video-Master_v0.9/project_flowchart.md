# AI视频分析系统流程图

本项目是一个用于视频内容分析、片段提取和合成的系统，采用了模块化设计。以下是系统的主要组件及其交互关系：

## 系统架构图

```mermaid
graph TD
    A[app.py - 主应用入口] --> B[config.py - 配置管理]
    A --> C[session/state.py - 会话状态管理]
    
    %% 核心处理逻辑
    A --> D[core/processor.py - 视频处理流水线]
    A --> E[core/composer.py - 视频合成引擎]
    A --> F[core/wordlist.py - 热词管理]
    
    %% UI组件
    A --> G[ui/components/dimension_editor.py]
    A --> H[ui/components/video_preview.py]
    
    %% 依赖关系
    D --> B
    E --> B
    F --> B
    G --> C
    H --> E
    D --> F
```

## 主要处理流程

```mermaid
sequenceDiagram
    participant U as 用户界面
    participant P as 处理器
    participant W as 热词管理
    participant D as 维度分析
    participant V as 视频合成
    
    U->>W: 1. 设置热词
    U->>D: 2. 配置维度结构
    U->>P: 3. 提交视频URL
    
    P->>W: 3.1 应用热词
    P->>P: 3.2 提取字幕
    P->>D: 3.3 进行维度分析
    P->>P: 3.4 匹配片段
    
    P->>V: 4. 传递匹配片段
    V->>V: 4.1 应用转场效果
    V->>V: 4.2 添加字幕
    V->>V: 4.3 合成最终视频
    
    V->>U: 5. 返回结果
    U->>U: 6. 展示预览和结果
```

## 数据流图

```mermaid
flowchart TB
    Input[视频URL输入] --> SubGen[字幕生成]
    HotWords[热词管理] --> SubGen
    
    SubGen --> TextAnalysis[文本分析]
    Dimensions[维度设置] --> TextAnalysis
    
    TextAnalysis --> Matching[片段匹配]
    TextAnalysis -->|关键维度| Matching
    Matching --> |匹配片段| Extraction[片段提取]
    
    Extraction --> Composition[视频合成]
    Settings[用户设置] --> |转场和效果| Composition
    
    Composition --> Output[最终视频]
    
    style Input fill:#f9f,stroke:#333,stroke-width:2px
    style Output fill:#9ff,stroke:#333,stroke-width:2px
```

## 组件关系详解

### 1. 主应用入口 (app.py)

应用的中心组件，负责初始化其他所有组件并连接UI与后端处理逻辑。主要功能：

- 配置Streamlit应用
- 管理导航和页面切换
- 初始化和管理会话状态
- 连接用户交互与处理逻辑

### 2. 配置管理 (config.py)

管理整个应用的配置参数，包括：

- 处理流程步骤配置
- 默认维度结构
- 转场效果参数
- 文件路径配置

### 3. 会话状态管理 (session/state.py)

管理用户会话状态，实现：

- 设置保存与加载
- 项目状态持久化
- 处理结果缓存
- 页面导航历史

### 4. 视频处理流水线 (core/processor.py)

核心处理逻辑，实现：

- 视频字幕生成
- 维度分析
- 片段匹配
- 结果排序和过滤

### 5. 视频合成引擎 (core/composer.py)

负责将匹配片段合成最终视频，功能包括：

- 片段裁剪和拼接
- 转场效果应用
- 字幕叠加
- 片尾标语处理

### 6. 热词管理 (core/wordlist.py)

管理语音识别热词，提供：

- 热词创建和管理
- 与云服务API交互
- 热词权重调整
- 本地热词缓存

### 7. UI组件

系统包含多个专用UI组件，如：

- 维度编辑器 (dimension_editor.py)：提供可视化维度编辑
- 视频预览 (video_preview.py)：展示片段和效果预览

## 工作流程说明

1. **初始设置**
   - 用户配置热词和维度结构
   - 系统保存这些设置到会话状态

2. **视频分析**
   - 用户提供视频URL
   - 处理器使用热词进行字幕提取
   - 应用维度分析确定片段相关性
   - 根据匹配阈值筛选片段

3. **结果处理**
   - 视频合成引擎处理匹配片段
   - 应用用户指定的转场效果
   - 生成最终视频

4. **结果展示**
   - 用户界面展示分析结果和预览
   - 提供导出和进一步处理的选项
