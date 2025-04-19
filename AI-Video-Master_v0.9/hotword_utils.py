import os
import json
import logging
import pandas as pd
import streamlit as st

# 配置日志
logger = logging.getLogger(__name__)

def import_hotwords_from_file(upload_file, append_mode=False, has_existing_data=False):
    """
    从上传的文件中导入热词
    
    参数:
        upload_file: Streamlit上传的文件对象
        append_mode: 是否追加模式
        has_existing_data: 是否已有现有热词
        
    返回:
        成功导入的热词列表和列表名称
    """
    try:
        # 解析文件名和扩展名
        filename = upload_file.name
        file_extension = filename.split('.')[-1].lower()
        list_name = os.path.splitext(filename)[0]
        if '_hotwords' in list_name:
            list_name = list_name.replace('_hotwords', '')
        
        # 根据文件类型处理
        if file_extension == 'json':
            return import_from_json(upload_file, list_name, append_mode, has_existing_data)
        elif file_extension == 'csv':
            return import_from_csv(upload_file, list_name, append_mode, has_existing_data)
        elif file_extension == 'txt':
            return import_from_txt(upload_file, list_name, append_mode, has_existing_data)
        else:
            st.error(f"不支持的文件格式: {file_extension}")
            return None, None
    except Exception as e:
        st.error(f"导入失败: {str(e)}")
        logger.error(f"导入热词失败: {str(e)}")
        return None, None

def import_from_json(upload_file, list_name, append_mode, has_existing_data):
    """从JSON文件导入热词"""
    try:
        content = upload_file.getvalue().decode('utf-8')
        json_data = json.loads(content)
        
        # 检查是否是直接保存的热词列表格式
        if isinstance(json_data, list) and all('text' in item for item in json_data):
            imported = json_data
            
            # 如果选择了追加模式且有现有数据
            if append_mode and has_existing_data:
                # 创建现有热词的集合以避免重复
                existing_texts = {hw['text'] for hw in st.session_state.settings['hot_words']}
                # 只添加不存在的热词
                new_items = [hw for hw in imported if hw['text'] not in existing_texts]
                # 合并两个列表
                st.session_state.settings['hot_words'].extend(new_items)
                imported_count = len(new_items)
                total_count = len(st.session_state.settings['hot_words'])
                st.success(f"已追加 {imported_count} 个新热词，当前共有 {total_count} 个热词")
                return st.session_state.settings['hot_words'], list_name
            else:
                # 替换模式
                st.success(f"已导入 {len(imported)} 个热词")
                return imported, list_name
        else:
            st.error("JSON文件格式不兼容，请确保文件包含正确的热词列表格式")
            return None, None
    except Exception as json_err:
        st.error(f"JSON解析失败: {str(json_err)}")
        return None, None

def import_from_csv(upload_file, list_name, append_mode, has_existing_data):
    """从CSV文件导入热词"""
    try:
        df_import = pd.read_csv(upload_file)
        if 'text' in df_import.columns:
            imported = []
            for _, row in df_import.iterrows():
                text = row.get('text', '')
                if text and len(text) <= 10:
                    imported.append({
                        'text': text,
                        'weight': int(row.get('weight', 4)),
                        'lang': row.get('lang', 'zh')
                    })
            
            # 如果选择了追加模式且有现有数据
            if append_mode and has_existing_data:
                # 创建现有热词的集合以避免重复
                existing_texts = {hw['text'] for hw in st.session_state.settings['hot_words']}
                # 只添加不存在的热词
                new_items = [hw for hw in imported if hw['text'] not in existing_texts]
                # 合并两个列表
                st.session_state.settings['hot_words'].extend(new_items)
                imported_count = len(new_items)
                total_count = len(st.session_state.settings['hot_words'])
                st.success(f"已追加 {imported_count} 个新热词，当前共有 {total_count} 个热词")
                return st.session_state.settings['hot_words'], list_name
            else:
                # 替换模式
                st.success(f"已导入 {len(imported)} 个热词")
                return imported, list_name
        else:
            st.error("CSV文件缺少'text'列")
            return None, None
    except Exception as csv_err:
        st.error(f"CSV解析失败: {str(csv_err)}")
        return None, None

def import_from_txt(upload_file, list_name, append_mode, has_existing_data):
    """从文本文件导入热词"""
    try:
        # 作为文本文件处理，每行一个热词
        content = upload_file.getvalue().decode('utf-8')
        lines = [line.strip() for line in content.split('\n')]
        imported = []
        for line in lines:
            if line and len(line) <= 10:
                imported.append({
                    'text': line,
                    'weight': 4,
                    'lang': 'zh'
                })
        
        # 如果选择了追加模式且有现有数据
        if append_mode and has_existing_data:
            # 创建现有热词的集合以避免重复
            existing_texts = {hw['text'] for hw in st.session_state.settings['hot_words']}
            # 只添加不存在的热词
            new_items = [hw for hw in imported if hw['text'] not in existing_texts]
            # 合并两个列表
            st.session_state.settings['hot_words'].extend(new_items)
            imported_count = len(new_items)
            total_count = len(st.session_state.settings['hot_words'])
            st.success(f"已追加 {imported_count} 个新热词，当前共有 {total_count} 个热词")
            return st.session_state.settings['hot_words'], list_name
        else:
            # 替换模式
            st.success(f"已导入 {len(imported)} 个热词")
            return imported, list_name
    except Exception as txt_err:
        st.error(f"文本解析失败: {str(txt_err)}")
        return None, None 