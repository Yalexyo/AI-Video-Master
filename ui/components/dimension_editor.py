import streamlit as st
import json
import logging
import time
import os
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class DimensionEditor:
    """维度结构编辑器：管理维度结构的显示和编辑"""

    def __init__(self, initial_dimensions: Dict = None):
        """初始化维度编辑器"""
        self.dimensions = initial_dimensions or {
            'level1': '品牌认知',
            'level2': ['产品特性', '用户需求'],
            'level3': {
                '产品特性': ['功能', '外观', '性能'],
                '用户需求': ['场景', '痛点', '期望']
            }
        }
        self.weights = self._initialize_weights()
        
        # 初始化会话状态
        if 'dimension_state' not in st.session_state:
            st.session_state.dimension_state = {
                'expanded_level2': [],  # 存储已展开的二级维度列表
                'deleted_level2': []    # 存储已删除的二级维度列表
            }
        
        # 初始化模板列表
        if 'templates' not in st.session_state:
            st.session_state.templates = {}
            
            # 从本地文件加载默认模板
            self._load_default_templates()
                
    def _initialize_weights(self) -> Dict:
        """初始化维度权重"""
        weights = {
            'level1': 1.0,
            'level2': {},
            'level3': {}
        }
        
        # 为二级维度设置权重
        for dim2 in self.dimensions['level2']:
            weights['level2'][dim2] = 0.5
            weights['level3'][dim2] = {}
            
            # 为三级维度设置权重
            if dim2 in self.dimensions['level3']:
                for dim3 in self.dimensions['level3'][dim2]:
                    weights['level3'][dim2][dim3] = 0.5
                    
        return weights
    
    def _load_default_templates(self):
        """从磁盘加载默认模板"""
        try:
            # 构建模板文件路径
            template_path = os.path.join('data', 'dimensions', 'initial_key_dimensions.json')
            
            # 检查文件是否存在
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                # 添加奶粉产品维度分析模板
                st.session_state.templates["奶粉产品维度分析"] = template_data
                logger.info(f"成功加载默认模板: {template_path}")
            else:
                logger.warning(f"模板文件不存在: {template_path}")
                
                # 添加一些内置模板
                self._add_builtin_templates()
        except Exception as e:
            logger.error(f"加载默认模板时出错: {str(e)}")
            # 加载失败时添加内置模板
            self._add_builtin_templates()
    
    def _add_builtin_templates(self):
        """添加内置模板"""
        default_templates = {
            "品牌认知分析": {
                "品牌属性": {
                    "视觉形象": [],
                    "品牌价值": [],
                    "市场定位": []
                },
                "用户感知": {
                    "情感联系": [],
                    "使用体验": [],
                    "忠诚度": []
                }
            },
            "产品功能评估": {
                "核心功能": {
                    "基础特性": [],
                    "操作便捷性": [],
                    "稳定性": []
                },
                "创新点": {
                    "差异化": [],
                    "技术优势": [],
                    "未来潜力": []
                }
            }
        }
        
        for name, data in default_templates.items():
            st.session_state.templates[name] = data
    
    def render(self):
        """渲染维度编辑器列表界面"""
        st.subheader("维度结构管理")
        
        # 显示当前维度结构
        if self.dimensions['level2']:
            # 创建表头
            cols = st.columns([1, 3, 1, 1])
            cols[0].markdown("**序号**")
            cols[1].markdown("**二级维度**")
            cols[2].markdown("**查询**")
            cols[3].markdown("**操作**")
            
            st.markdown("---")  # 表头与内容分隔线
            
            # 保存当前显示的维度名称列表，用于删除操作
            visible_dimensions = []
            
            # 显示每个二级维度行
            for i, dim2 in enumerate(self.dimensions['level2']):
                # 如果此维度已被删除，则跳过
                if dim2 in st.session_state.dimension_state['deleted_level2']:
                    continue
                
                visible_dimensions.append(dim2)
                
                # 创建行
                row_cols = st.columns([1, 3, 1, 1])
                row_cols[0].text(f"{i+1}")
                row_cols[1].text(dim2)
                
                # 查询按钮 - 切换展开/折叠状态
                if row_cols[2].button("查询", key=f"query_btn_{i}_{dim2.replace(' ', '_')}", use_container_width=True):
                    if dim2 in st.session_state.dimension_state['expanded_level2']:
                        st.session_state.dimension_state['expanded_level2'].remove(dim2)
                    else:
                        st.session_state.dimension_state['expanded_level2'].append(dim2)
                    st.rerun()
                
                # 删除按钮
                if row_cols[3].button("删除", key=f"delete_btn_{i}_{dim2.replace(' ', '_')}", use_container_width=True):
                    self._delete_dimension(dim2)
                    st.success(f"已删除维度: {dim2}")
                    time.sleep(0.5)  # 短暂延迟以显示成功消息
                    st.rerun()
                
                # 如果维度已展开，显示三级维度
                if dim2 in st.session_state.dimension_state['expanded_level2']:
                    with st.container():
                        st.markdown("---")  # 详情与行的分隔线
                        
                        # 创建详情区域
                        st.markdown(f"""
                        <div style="background-color:#f0f2f6;padding:10px;border-radius:5px;margin-bottom:10px;">
                            <h5 style="color:#0068c9;">{dim2} 详情</h5>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 获取该二级维度下的所有三级维度
                        level3_dims = self.dimensions['level3'].get(dim2, [])
                        
                        if level3_dims:
                            # 创建三级维度表格
                            level3_data = []
                            for j, dim3 in enumerate(level3_dims):
                                level3_data.append({"序号": j+1, "三级维度": dim3})
                            
                            if level3_data:
                                # 显示三级维度表格
                                st.dataframe(
                                    level3_data,
                                    column_config={
                                        "序号": st.column_config.NumberColumn(width="small"),
                                        "三级维度": st.column_config.TextColumn(width="medium")
                                    },
                                    use_container_width=True,
                                    hide_index=True
                                )
                        else:
                            st.info(f"维度 '{dim2}' 下没有三级维度")
                    
                    st.markdown("---")  # 详情区的结束分隔线
                else:
                    # 简单的分隔线
                    st.markdown("---")
            
            # 提供总计信息
            st.caption(f"共 {len(visible_dimensions)} 个维度")
        else:
            st.info("还没有定义任何维度。请使用模板或添加新维度。")
        
        # 添加新维度按钮
        if st.button("添加新维度", key="add_new_dimension_btn"):
            new_dim = f"新维度{len(self.dimensions['level2'])+1}"
            self.dimensions['level2'].append(new_dim)
            self.dimensions['level3'][new_dim] = []
            self.weights['level2'][new_dim] = 0.5
            st.success(f"已添加新维度: {new_dim}")
            time.sleep(0.5)
            st.rerun()
        
        # 返回当前维度结构和权重
        return {
            'dimensions': self.dimensions,
            'weights': self.weights
        }
    
    def _delete_dimension(self, dim2: str):
        """删除指定的二级维度及其所有三级维度"""
        # 标记为已删除
        if dim2 not in st.session_state.dimension_state['deleted_level2']:
            st.session_state.dimension_state['deleted_level2'].append(dim2)
        
        # 从会话状态中移除展开状态
        if dim2 in st.session_state.dimension_state['expanded_level2']:
            st.session_state.dimension_state['expanded_level2'].remove(dim2)
        
        # 从二级维度列表中移除
        if dim2 in self.dimensions['level2']:
            self.dimensions['level2'].remove(dim2)
        
        # 移除相关的三级维度
        if dim2 in self.dimensions['level3']:
            del self.dimensions['level3'][dim2]
        
        # 移除相关的权重设置
        if dim2 in self.weights['level2']:
            del self.weights['level2'][dim2]
        if dim2 in self.weights['level3']:
            del self.weights['level3'][dim2]
    
    def apply_template(self, template_data: Dict):
        """应用模板数据到当前维度结构"""
        # 重置维度结构
        self.dimensions['level2'] = []
        self.dimensions['level3'] = {}
        
        # 添加模板中的维度
        for dim2, level3_dict in template_data.items():
            self.dimensions['level2'].append(dim2)
            self.dimensions['level3'][dim2] = []
            
            # 添加三级维度
            for dim3, level4_list in level3_dict.items():
                self.dimensions['level3'][dim2].append(dim3)
        
        # 重新初始化权重
        self.weights = self._initialize_weights()
        
        # 清空已删除列表
        st.session_state.dimension_state['deleted_level2'] = []
        
    def save_template(self, template_name: str, template_data: Dict):
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
        
    def delete_template(self, template_name: str):
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
    
    def get_template_names(self) -> List[str]:
        """获取所有模板名称列表"""
        return list(st.session_state.templates.keys())
