import streamlit as st
import json
import logging
import time
import os
from typing import Dict, List, Any
import urllib.parse

logger = logging.getLogger(__name__)

def render_dimension_editor(initial_dimensions: Dict = None):
    """
    维度编辑器，使用纯函数方式实现
    
    参数:
        initial_dimensions: 初始维度结构，格式为 {"title": "标题", "level1": ["一级维度1", "一级维度2"], "level2": {"一级维度1": ["二级维度1", "二级维度2"]}}
    """
    # 初始化会话状态
    if 'dimensions' not in st.session_state:
        if initial_dimensions and isinstance(initial_dimensions, dict):
            st.session_state.dimensions = initial_dimensions
            # 确保dimensions包含必要的结构
            if 'title' not in st.session_state.dimensions:
                st.session_state.dimensions['title'] = "品牌认知"
            if 'level1' not in st.session_state.dimensions:
                st.session_state.dimensions['level1'] = []
            if 'level2' not in st.session_state.dimensions:
                st.session_state.dimensions['level2'] = {}
        else:
            # 默认维度结构
            st.session_state.dimensions = {
                'title': "品牌认知",
                'level1': [],
                'level2': {}
            }
    
    # 初始化权重
    if 'weights' not in st.session_state:
        st.session_state.weights = initialize_weights(st.session_state.dimensions)
    
    # 初始化模板字典
    if 'templates' not in st.session_state:
        st.session_state.templates = {}
        load_default_templates()
    
    # 渲染维度编辑器界面
    st.subheader("维度结构管理")
    
    # 初始化删除维度的存储（如果需要）
    if 'deleted_dimensions' not in st.session_state:
        st.session_state.deleted_dimensions = {'level1': [], 'level2': {}}
        
    # 显示当前维度结构
    if st.session_state.dimensions.get('level1'):
        # 获取未删除的一级维度列表
        active_level1_dims = [dim1 for dim1 in st.session_state.dimensions['level1'] 
                              if dim1 not in st.session_state.deleted_dimensions['level1']]
        
        # 遍历每个一级维度
        for i, dim1 in enumerate(active_level1_dims):
            # 创建一个可折叠区域显示每个一级维度
            with st.expander(f"**{dim1}**", expanded=True):
                # 删除当前一级维度的按钮
                delete_key = f"delete_dim1_{i}"
                if st.button(f"删除维度 '{dim1}'", key=delete_key):
                    # 在点击处理中删除维度
                    delete_level1_dimension(dim1)
                
                # 显示此一级维度下的二级维度
                if dim1 in st.session_state.dimensions.get('level2', {}) and st.session_state.dimensions['level2'][dim1]:
                    # 获取未删除的二级维度列表
                    active_level2_dims = []
                    if dim1 in st.session_state.dimensions['level2']:
                        # 过滤掉已删除的二级维度
                        deleted_dim2s = st.session_state.deleted_dimensions.get('level2', {}).get(dim1, [])
                        active_level2_dims = [dim2 for dim2 in st.session_state.dimensions['level2'][dim1] 
                                             if dim2 not in deleted_dim2s]
                    
                    if active_level2_dims:
                        # 创建表头
                        cols = st.columns([1, 3, 1])
                        cols[0].markdown("**序号**")
                        cols[1].markdown("**二级维度**")
                        cols[2].markdown("**操作**")
                        
                        st.markdown("---")  # 分隔线
                        
                        # 显示每个二级维度并添加删除按钮
                        for j, dim2 in enumerate(active_level2_dims):
                            # 使用行布局展示二级维度和删除按钮
                            row_cols = st.columns([1, 3, 1])
                            row_cols[0].text(f"{j+1}")
                            row_cols[1].text(dim2)
                            
                            # 删除二级维度的按钮
                            delete_key = f"delete_dim2_{i}_{j}"
                            if row_cols[2].button("删除", key=delete_key):
                                # 在点击处理中删除二级维度
                                delete_level2_dimension(dim1, dim2)
                else:
                    st.info(f"在 '{dim1}' 下还没有定义任何二级维度")
                
                # 添加二级维度的按钮
                st.markdown("---")
                st.write(f"添加二级维度到 '{dim1}'")
                add_cols = st.columns([4, 1])
                
                # 输入框和按钮
                input_key = f"add_dim2_input_{i}"
                button_key = f"add_dim2_button_{i}"
                
                # 如果之前没有设置输入状态，初始化为空字符串
                if input_key not in st.session_state:
                    st.session_state[input_key] = ""
                
                new_dim2 = add_cols[0].text_input("二级维度名称", key=input_key, 
                                                 placeholder=f"输入要添加到'{dim1}'的二级维度名称",
                                                 label_visibility="collapsed")
                if add_cols[1].button("添加", key=button_key):
                    add_level2_dimension(dim1, new_dim2, input_key)
    else:
        st.info("还没有定义任何维度。请使用模板或添加新维度。", key="no_dims_info")
    
    # 添加新的一级维度
    st.subheader("添加新的一级维度")
    
    # 使用常规输入和按钮
    add_dim1_cols = st.columns([3, 1])
    
    # 设置唯一键
    input_key = "add_dim1_input"
    button_key = "add_dim1_button"
    
    # 如果之前没有设置输入状态，初始化为空字符串
    if input_key not in st.session_state:
        st.session_state[input_key] = ""
    
    # 输入框和按钮
    new_dim1 = add_dim1_cols[0].text_input("一级维度名称", key=input_key, 
                                         placeholder="输入一级维度名称", 
                                         label_visibility="collapsed")
    if add_dim1_cols[1].button("添加", key=button_key, type="primary"):
        add_level1_dimension(new_dim1, input_key)
    
    # 返回当前维度结构和权重
    return {
        'dimensions': st.session_state.dimensions,
        'weights': st.session_state.weights
    }

def delete_level1_dimension(dim1):
    """删除一级维度"""
    logger.info(f"尝试删除一级维度: '{dim1}'")
    
    # 初始化已删除的维度列表（如果不存在）
    if 'deleted_dimensions' not in st.session_state:
        st.session_state.deleted_dimensions = {'level1': [], 'level2': {}}
    
    # 将维度标记为已删除
    if dim1 not in st.session_state.deleted_dimensions['level1']:
        st.session_state.deleted_dimensions['level1'].append(dim1)
    
    # 从一级维度列表中删除
    if dim1 in st.session_state.dimensions['level1']:
        st.session_state.dimensions['level1'].remove(dim1)
    
    # 移除相关的权重设置和二级维度
    if dim1 in st.session_state.weights['level1']:
        del st.session_state.weights['level1'][dim1]
    if dim1 in st.session_state.weights['level2']:
        del st.session_state.weights['level2'][dim1]
    if dim1 in st.session_state.dimensions['level2']:
        del st.session_state.dimensions['level2'][dim1]
    
    # 持久化维度结构
    persist_dimensions()
    
    # 显示成功消息
    st.success(f"已删除维度: {dim1}")
    
    # 设置标志，表示需要在下一次渲染时重新加载页面
    st.session_state.need_dimension_refresh = True
    
    # 强制重新运行应用以刷新界面
    st.rerun()

def delete_level2_dimension(dim1, dim2):
    """删除二级维度"""
    logger.info(f"尝试删除二级维度 '{dim2}' 从 '{dim1}'")
    
    # 初始化已删除的维度列表（如果不存在）
    if 'deleted_dimensions' not in st.session_state:
        st.session_state.deleted_dimensions = {'level1': [], 'level2': {}}
    
    # 初始化此一级维度下的已删除二级维度列表
    if dim1 not in st.session_state.deleted_dimensions['level2']:
        st.session_state.deleted_dimensions['level2'][dim1] = []
    
    # 将维度标记为已删除
    if dim2 not in st.session_state.deleted_dimensions['level2'][dim1]:
        st.session_state.deleted_dimensions['level2'][dim1].append(dim2)
    
    # 确保一级维度存在
    if dim1 in st.session_state.dimensions['level2']:
        # 确保二级维度存在
        if dim2 in st.session_state.dimensions['level2'][dim1]:
            # 删除二级维度
            st.session_state.dimensions['level2'][dim1].remove(dim2)
            
            # 删除相关的权重设置
            if dim1 in st.session_state.weights['level2'] and dim2 in st.session_state.weights['level2'][dim1]:
                del st.session_state.weights['level2'][dim1][dim2]
            
            # 持久化维度结构
            persist_dimensions()
            
            # 显示成功消息
            st.success(f"已删除维度: {dim2}")
            
            # 设置标志，表示需要在下一次渲染时重新加载页面
            st.session_state.need_dimension_refresh = True
            
            # 强制重新运行应用以刷新界面
            st.rerun()

def add_level1_dimension(new_dim1, input_key):
    """添加一级维度"""
    logger.info(f"尝试添加一级维度: '{new_dim1}'")
    if new_dim1:
        if new_dim1 not in st.session_state.dimensions.get('level1', []):
            if 'level1' not in st.session_state.dimensions:
                st.session_state.dimensions['level1'] = []
            st.session_state.dimensions['level1'].append(new_dim1)
            
            # 初始化这个一级维度的权重和二级维度
            st.session_state.weights['level1'][new_dim1] = 0.8
            st.session_state.weights['level2'][new_dim1] = {}
            st.session_state.dimensions['level2'][new_dim1] = []
            
            # 标记维度已修改
            st.session_state.has_dimension_changes = True
            
            # 不再尝试直接修改输入框的值
            # st.session_state[input_key] = ""  # 会导致错误
            
            logger.info(f"成功添加一级维度: '{new_dim1}'")
            st.success(f"已添加一级维度: {new_dim1}")
            
            # 持久化维度结构
            persist_dimensions()
            
            # 设置需要刷新页面的标志
            st.session_state.need_dimension_refresh = True
            
            # 使用st.rerun()重新加载页面，这样输入框会被重置
            st.rerun()
        else:
            st.warning(f"维度 '{new_dim1}' 已存在")
    else:
        st.warning("请输入维度名称")

def add_level2_dimension(dim1, new_dim2, input_key):
    """添加二级维度"""
    logger.info(f"尝试添加二级维度到 '{dim1}': '{new_dim2}'")
    if new_dim2:
        if dim1 not in st.session_state.dimensions.get('level2', {}):
            st.session_state.dimensions['level2'][dim1] = []
        
        # 检查是否已存在
        if new_dim2 in st.session_state.dimensions['level2'][dim1]:
            st.warning(f"维度 '{new_dim2}' 已存在")
        else:
            st.session_state.dimensions['level2'][dim1].append(new_dim2)
            
            # 更新权重
            if dim1 not in st.session_state.weights['level2']:
                st.session_state.weights['level2'][dim1] = {}
            st.session_state.weights['level2'][dim1][new_dim2] = 0.5
            
            # 标记维度已修改
            st.session_state.has_dimension_changes = True
            
            # 不再尝试直接修改输入框的值
            # st.session_state[input_key] = ""  # 会导致错误
            
            logger.info(f"成功添加二级维度 '{new_dim2}' 到 '{dim1}'")
            st.success(f"已添加新维度: {new_dim2}")
            
            # 持久化维度结构
            persist_dimensions()
            
            # 设置需要刷新页面的标志
            st.session_state.need_dimension_refresh = True
            
            # 使用st.rerun()重新加载页面，这样输入框会被重置
            st.rerun()
    else:
        st.warning("请输入维度名称")

def initialize_weights(dimensions: Dict) -> Dict:
    """初始化维度权重"""
    weights = {
        'title': 1.0,
        'level1': {},
        'level2': {}
    }
    
    # 为一级维度设置权重
    for dim1 in dimensions['level1']:
        weights['level1'][dim1] = 0.8
        weights['level2'][dim1] = {}
        
        # 为二级维度设置权重
        if dim1 in dimensions['level2']:
            for dim2 in dimensions['level2'][dim1]:
                weights['level2'][dim1][dim2] = 0.5
                
    return weights

def load_default_templates():
    """从磁盘加载默认模板"""
    try:
        # 使用相对路径构建模板目录路径
        template_dir = os.path.join('data', 'dimensions')
        
        # 检查目录是否存在
        if os.path.exists(template_dir) and os.path.isdir(template_dir):
            # 遍历目录中的所有JSON文件
            files_loaded = 0
            for filename in os.listdir(template_dir):
                if filename.endswith('.json'):
                    template_path = os.path.join(template_dir, filename)
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                        
                        # 使用文件名作为模板名称（去除.json后缀并将下划线替换为空格）
                        template_name = os.path.splitext(filename)[0].replace('_', ' ')
                        st.session_state.templates[template_name] = template_data
                        files_loaded += 1
                        logger.info(f"成功加载模板: {template_path}")
                    except Exception as e:
                        logger.error(f"加载模板 {template_path} 时出错: {str(e)}")
            
            if files_loaded == 0:
                logger.warning(f"在目录 {template_dir} 中未找到JSON模板文件")
                # 添加内置模板
                add_builtin_templates()
            else:
                logger.info(f"共加载了 {files_loaded} 个模板文件")
        else:
            logger.warning(f"模板目录不存在: {template_dir}")
            # 添加内置模板
            add_builtin_templates()
    except Exception as e:
        logger.error(f"加载默认模板时出错: {str(e)}")
        # 加载失败时添加内置模板
        add_builtin_templates()

def add_builtin_templates():
    """添加内置模板"""
    default_templates = {
        "品牌认知分析": {
            "品牌属性": [
                "视觉形象",
                "品牌价值",
                "市场定位"
            ],
            "用户感知": [
                "情感联系",
                "使用体验",
                "忠诚度"
            ]
        },
        "产品功能评估": {
            "核心功能": [
                "基础特性",
                "操作便捷性",
                "稳定性"
            ],
            "创新点": [
                "差异化",
                "技术优势",
                "未来潜力"
            ]
        }
    }
    
    for name, data in default_templates.items():
        st.session_state.templates[name] = data

def persist_dimensions():
    """将当前维度结构持久化到磁盘"""
    try:
        # 创建维度数据目录（如果不存在）
        data_dir = os.path.join('data', 'dimensions')
        os.makedirs(data_dir, exist_ok=True)
        
        # 保存当前维度结构
        current_dimensions_path = os.path.join(data_dir, 'current_dimensions.json')
        with open(current_dimensions_path, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.dimensions, f, ensure_ascii=False, indent=2)
            
        # 保存当前权重设置
        current_weights_path = os.path.join(data_dir, 'current_weights.json')
        with open(current_weights_path, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.weights, f, ensure_ascii=False, indent=2)
            
        logger.info("成功持久化维度结构和权重设置")
    except Exception as e:
        logger.error(f"持久化维度结构时出错: {str(e)}")

def apply_template(template_data: Dict):
    """
    应用模板数据到当前维度结构
    
    参数:
        template_data: 模板数据，格式为 {"一级维度1": ["二级维度1", "二级维度2"], ...}
    """
    if not template_data:
        return
    
    # 重置维度结构
    st.session_state.dimensions = {
        'title': "品牌认知",  # 可以使用可配置的标题
        'level1': [],
        'level2': {}  # 使用字典存储每个一级维度下的二级维度
    }
    
    # 重置已删除的维度列表，避免加载新模板时遗留旧的删除状态
    st.session_state.deleted_dimensions = {'level1': [], 'level2': {}}
    
    # 将模板中的键作为一级维度，值作为二级维度
    for key, value in template_data.items():
        st.session_state.dimensions['level1'].append(key)
        st.session_state.dimensions['level2'][key] = value if isinstance(value, list) else []
    
    # 重置权重
    st.session_state.weights = initialize_weights(st.session_state.dimensions)
    
    return st.session_state.dimensions

def save_template(template_name: str, template_data: Dict):
    """保存当前维度结构为模板"""
    st.session_state.templates[template_name] = template_data
    
    # 尝试将模板保存到磁盘
    try:
        template_dir = os.path.join('data', 'dimensions')
        os.makedirs(template_dir, exist_ok=True)
        
        template_path = os.path.join(template_dir, f"{template_name.replace(' ', '_')}.json")
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"已将模板保存到磁盘: {template_path}")
    except Exception as e:
        logger.error(f"保存模板到磁盘时出错: {str(e)}")
    
def delete_template(template_name: str):
    """删除指定名称的模板"""
    if template_name in st.session_state.templates:
        del st.session_state.templates[template_name]
        
        # 尝试从磁盘删除模板
        try:
            template_path = os.path.join('data', 'dimensions', f"{template_name.replace(' ', '_')}.json")
            if os.path.exists(template_path):
                os.remove(template_path)
                logger.info(f"已从磁盘删除模板: {template_path}")
        except Exception as e:
            logger.error(f"从磁盘删除模板时出错: {str(e)}")

def get_template_names() -> List[str]:
    """获取所有模板名称列表，包含文件名信息"""
    template_names = list(st.session_state.templates.keys())
    
    # 创建模板目录（如果不存在）
    template_dir = os.path.join('data', 'dimensions')
    os.makedirs(template_dir, exist_ok=True)
    
    # 获取目录中实际存在的文件
    existing_files = []
    if os.path.exists(template_dir):
        existing_files = [f for f in os.listdir(template_dir) if f.endswith('.json')]
    
    # 最终结果列表
    final_template_names = []
    
    # 处理会话状态中的模板
    for name in template_names:
        if name.startswith('@'):
            # 对于以@开头的特殊模板，检查文件是否实际存在
            file_name = name[1:]  # 去掉@前缀
            if file_name in existing_files:
                final_template_names.append(name)
        else:
            # 普通模板，检查对应的文件是否存在
            file_name = f"{name.replace(' ', '_')}.json"
            if file_name in existing_files:
                final_template_names.append(name)
    
    # 特别处理core_templates.json
    if 'core_templates.json' in existing_files and '@core_templates.json' not in final_template_names:
        if '@core_templates' in template_names:
            final_template_names.append('@core_templates.json')
    
    return final_template_names
