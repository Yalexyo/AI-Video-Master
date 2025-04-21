import streamlit as st
from typing import Dict, List
import json
import logging

# 获取logger
logger = logging.getLogger(__name__)

class DimensionEditor:
    """维度编辑器组件 - 用于可视化编辑维度结构"""
    
    def __init__(self, initial_dimensions: Dict = None):
        """
        初始化维度编辑器
        
        参数:
            initial_dimensions: 初始维度结构，格式为 {"title": "标题", "level1": ["一级维度1", "一级维度2"], "level2": {"一级维度1": ["二级维度1", "二级维度2"]}}
        """
        if 'dimensions' not in st.session_state:
            if initial_dimensions and isinstance(initial_dimensions, dict):
                st.session_state.dimensions = initial_dimensions
            else:
                # 默认维度结构
                st.session_state.dimensions = {
                    'title': "品牌认知",
                    'level1': [],
                    'level2': {}
                }
        
        # 初始化权重结构
        if 'weights' not in st.session_state:
            self._initialize_weights()
    
    def _initialize_weights(self):
        """初始化权重设置"""
        weights = {
            'title': 1.0,
            'level1': {},
            'level2': {}
        }
        
        # 设置一级维度权重
        for dim1 in st.session_state.dimensions.get('level1', []):
            weights['level1'][dim1] = 0.8
            weights['level2'][dim1] = {}
            
            # 设置二级维度权重
            for dim2 in st.session_state.dimensions.get('level2', {}).get(dim1, []):
                weights['level2'][dim1][dim2] = 0.5
        
        st.session_state.weights = weights
    
    def get_template_names(self) -> List[str]:
        """获取所有可用的模板名称"""
        from fixed_dimension_editor import get_template_names
        return get_template_names()
    
    def apply_template(self, template_data: Dict):
        """应用模板数据到当前维度结构"""
        from fixed_dimension_editor import apply_template
        return apply_template(template_data)
    
    def render(self):
        """渲染维度编辑器"""
        from fixed_dimension_editor import render_dimension_editor
        return render_dimension_editor(st.session_state.dimensions) 