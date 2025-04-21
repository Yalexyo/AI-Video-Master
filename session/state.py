import streamlit as st
import json
import os
import glob
from typing import Dict, Any, Optional, List
import logging
import time
import dashscope
from dashscope import audio
import math
from pathlib import Path
import traceback
import tempfile
import shutil
from datetime import datetime
from moviepy.editor import VideoFileClip
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 导入正确的VideoProcessor和VideoSegment类
from core.processor import VideoProcessor, VideoSegment

logger = logging.getLogger(__name__)

class SessionState:
    """会话状态管理类：处理Streamlit会话状态和持久化"""
    
    def __init__(self, storage_path: str = "data/session"):
        """初始化会话状态管理器"""
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def initialize_session(self):
        """初始化会话，设置默认值"""
        try:
            if 'initialized' not in st.session_state:
                st.session_state.initialized = True
                st.session_state.settings = self.get_default_settings()
                st.session_state.current_project = None
                st.session_state.results = []
                st.session_state.page_history = ["home"]
                logger.info("Session initialized with default values")
        except Exception as e:
            logger.error(f"Failed to initialize session: {str(e)}")
            st.error("会话初始化失败，请刷新页面重试")
    
    def get_default_settings(self) -> Dict[str, Any]:
        """获取默认设置"""
        # 尝试加载initial_key_dimensions作为默认维度
        try:
            import os
            import json
            template_path = os.path.join('/Users/apple/Desktop/AI video/videoAnalysis_v1.0/data/dimensions', 'initial_key_dimensions.json')
            initial_dimensions = None
            weights = {}  # 初始化默认权重字典
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    initial_template = json.load(f)
                    
                    # 设置维度数据结构
                    initial_dimensions = {
                        'level1': '品牌认知',
                        'level2': list(initial_template.keys())
                    }
                    
                    # 生成权重设置
                    weights = {
                        'level1': 1.0,
                        'level2': {}
                    }
                    
                    # 为二级维度设置权重
                    for dim2 in initial_dimensions['level2']:
                        weights['level2'][dim2] = 0.5
                    
                    logger.info("已加载initial key dimensions作为默认维度设置")
        except Exception as e:
            logger.error(f"加载initial key dimensions失败: {str(e)}")
            initial_dimensions = None
            weights = None
        
        # 返回默认设置
        return {
            'urls': [],
            'threshold': 0.7,
            'priority': '综合评分',
            'transition': '淡入淡出',
            'transition_duration': 1.0,
            'custom_dimensions': initial_dimensions is not None,  # 如果成功加载了维度，则标记为自定义
            'dimensions': initial_dimensions,
            'weights': weights,
            'hot_words': []
        }
    
    def save_settings(self, project_name: str = "default"):
        """保存当前设置到文件"""
        # 处理 project_name 为 None 的情况
        effective_project_name = project_name if project_name is not None else "default"
        if not effective_project_name: # 如果仍然是空字符串，则强制为 'default'
            effective_project_name = "default"
            logger.warning("项目名称为空，已强制使用 'default'")

        # 移除之前错误的条件判断
        # if 'settings' in st.session_state and st.session_state.settings.get('某个设置项') != 期望的值:
        if 'settings' in st.session_state: # 恢复原始的检查，只检查 settings 是否存在
            file_path = os.path.join(self.storage_path, f"{effective_project_name}_settings.json") # 使用处理过的项目名
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.settings, f, ensure_ascii=False, indent=2)
                logger.info(f"Settings saved to {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to save settings: {str(e)}")
                return False
        return False
    
    def load_settings(self, project_name: str = "default") -> bool:
        """加载设置"""
        file_path = os.path.join(self.storage_path, f"{project_name}_settings.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    st.session_state.settings = json.load(f)
                st.session_state.current_project = project_name
                logger.info(f"Settings loaded from {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to load settings: {str(e)}")
                return False
        return False
    
    def save_results(self, results: list, project_name: Optional[str] = None):
        """保存分析结果"""
        if project_name is None:
            project_name = st.session_state.get('current_project', 'default')
        
        file_path = os.path.join(self.storage_path, f"{project_name}_results.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 将结果转换为可序列化的字典
                serializable_results = []
                for r in results:
                    if hasattr(r, '__dict__'):
                        serializable_results.append(r.__dict__)
                    else:
                        serializable_results.append(r)
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
            return False
    
    def load_results(self, project_name: Optional[str] = None) -> list:
        """加载分析结果"""
        if project_name is None:
            project_name = st.session_state.get('current_project', 'default')
        
        file_path = os.path.join(self.storage_path, f"{project_name}_results.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                logger.info(f"Results loaded from {file_path}")
                return results
            except Exception as e:
                logger.error(f"Failed to load results: {str(e)}")
        return []
    
    def navigate_to(self, page: str):
        """导航到指定页面并记录历史"""
        if page != st.session_state.page_history[-1]:
            st.session_state.page_history.append(page)
        st.session_state.current_page = page
    
    def go_back(self):
        """返回上一页"""
        if len(st.session_state.page_history) > 1:
            st.session_state.page_history.pop()  # 移除当前页
            st.session_state.current_page = st.session_state.page_history[-1]
    
    def get_project_list(self) -> List[str]:
        """获取所有可用项目的列表"""
        try:
            # 每次都重新扫描目录，确保获取最新的项目列表
            # 查找所有项目设置文件
            pattern = os.path.join(self.storage_path, "*_settings.json")
            files = glob.glob(pattern)
            
            # 提取项目名称
            projects = []
            for file in files:
                base_name = os.path.basename(file)
                # 从文件名 "project_name_settings.json" 中提取项目名
                project_name = base_name.replace("_settings.json", "")
                projects.append(project_name)
            
            # 更新缓存
            st.session_state["project_list"] = sorted(projects)
            
            logger.info(f"Found {len(projects)} projects")
            return sorted(projects)
        except Exception as e:
            logger.error(f"Failed to get project list: {str(e)}")
            return []
    
    def delete_project(self, project_name: str) -> bool:
        """删除项目及其相关文件"""
        if not project_name:
            logger.error("尝试删除空项目名")
            return False
        
        try:
            # 计数删除的文件数
            deleted_count = 0
            
            # 删除项目设置文件
            settings_file = os.path.join(self.storage_path, f"{project_name}_settings.json")
            if os.path.exists(settings_file):
                os.remove(settings_file)
                logger.info(f"已删除设置文件: {settings_file}")
                deleted_count += 1
            else:
                logger.warning(f"设置文件不存在: {settings_file}")
            
            # 删除项目结果文件
            results_file = os.path.join(self.storage_path, f"{project_name}_results.json")
            if os.path.exists(results_file):
                os.remove(results_file)
                logger.info(f"已删除结果文件: {results_file}")
                deleted_count += 1
            
            # 确保在会话中清除该项目的任何引用
            if st.session_state.get('current_project') == project_name:
                st.session_state.pop('current_project', None)
                logger.info(f"从会话状态中移除项目: {project_name}")
            
            # 清除项目列表缓存
            if 'project_list' in st.session_state:
                st.session_state.pop('project_list', None)
                logger.info("已清除项目列表缓存")
            
            # 给文件系统一些时间来完成操作
            time.sleep(0.5)
            
            # 再次检查文件是否真的被删除
            if os.path.exists(settings_file) or os.path.exists(results_file):
                logger.error(f"文件删除后仍存在: {project_name}")
                return False
            
            logger.info(f"项目 {project_name} 删除成功，共删除 {deleted_count} 个文件")
            return True
        except Exception as e:
            logger.error(f"删除项目 {project_name} 时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

# 全局会话状态实例
session_state = SessionState()
