import streamlit as st
import os
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import sys
import asyncio
import requests
import json
import time
import uuid
from typing import Dict, List, Any, Optional
import nest_asyncio
import platform
import subprocess
import glob  # 添加glob导入
import shutil
from manage_projects import delete_project as manage_delete_project
import re

# 阿里云DashScope热词管理API接口
def create_vocabulary(prefix, target_model, vocabulary):
    """创建热词表"""
    api_key = os.getenv('DASHSCOPE_API_KEY', '')
    if not api_key:
        logger.error("缺少DASHSCOPE_API_KEY环境变量")
        raise ValueError("缺少DASHSCOPE_API_KEY环境变量")
        
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/customization"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "speech-biasing",
        "input": {
            "action": "create_vocabulary",
            "target_model": target_model,
            "prefix": prefix,
            "vocabulary": vocabulary
        }
    }
    
    logger.info(f"准备发送热词表创建请求，前缀: {prefix}, 模型: {target_model}, 热词数量: {len(vocabulary)}")
    
    try:
        # 设置合理的超时时间，添加更健壮的错误处理
        response = requests.post(url, headers=headers, json=data, timeout=(5, 30))
        response.raise_for_status()
        result = response.json()
        
        if 'output' in result and 'task_id' in result['output']:
            logger.info(f"热词表创建任务已提交，任务ID: {result['output']['task_id']}")
        else:
            error_code = result.get('code', '未知错误码')
            error_message = result.get('message', '未知错误')
            logger.error(f"热词表创建失败, 错误码: {error_code}, 错误信息: {error_message}")
            
            # 记录特定错误码的详细信息
            if error_code == 'InvalidApiKey':
                logger.error("API密钥无效，请检查DASHSCOPE_API_KEY环境变量")
            elif error_code == 'QuotaExceeded':
                logger.error("已超出API配额限制，请联系阿里云客服")
            elif error_code == 'AccessDenied':
                logger.error("没有访问权限，请确认账户是否开通了相关服务")
            elif error_code == 'InvalidParameter':
                logger.error(f"参数错误: {error_message}")
            
        return result
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP错误: {http_err}")
        status_code = getattr(http_err.response, 'status_code', None)
        logger.error(f"状态码: {status_code}")
        try:
            error_json = http_err.response.json()
            logger.error(f"错误详情: {error_json}")
            return error_json
        except:
            return {"code": "HTTPError", "message": str(http_err)}
            
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"连接错误: {conn_err}")
        return {"code": "ConnectionError", "message": "无法连接到阿里云服务，请检查网络连接"}
        
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"请求超时: {timeout_err}")
        return {"code": "TimeoutError", "message": "请求超时，请稍后再试"}
        
    except requests.exceptions.ProxyError as proxy_err:
        logger.error(f"代理错误: {proxy_err}")
        return {"code": "ProxyError", "message": "代理服务器错误，请检查网络设置或禁用代理"}
        
    except requests.exceptions.SSLError as ssl_err:
        logger.error(f"SSL错误: {ssl_err}")
        return {"code": "SSLError", "message": "SSL证书验证失败，请检查网络环境"}
        
    except requests.exceptions.JSONDecodeError as json_err:
        logger.error(f"JSON解析错误: {json_err}")
        return {"code": "JSONDecodeError", "message": "无法解析API响应"}
        
    except Exception as e:
        logger.error(f"创建热词表时发生未知错误: {str(e)}", exc_info=True)
        return {"code": "UnknownError", "message": str(e)}

def list_vocabulary(prefix=None, page_index=0, page_size=10):
    """查询所有热词表"""
    api_key = os.getenv('DASHSCOPE_API_KEY', '')
    if not api_key:
        logger.error("缺少DASHSCOPE_API_KEY环境变量")
        raise ValueError("缺少DASHSCOPE_API_KEY环境变量")
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/customization"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "speech-biasing",
        "input": {
            "action": "list_vocabulary",
            "prefix": prefix,
            "page_index": page_index,
            "page_size": page_size
        }
    }
    
    logger.info(f"准备获取热词表列表，前缀: {prefix}, 页码: {page_index}, 每页数量: {page_size}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if 'output' in result and 'vocabulary_list' in result['output']:
            logger.info(f"成功获取热词表列表，共 {len(result['output']['vocabulary_list'])} 个热词表")
        else:
            error_code = result.get('code', '未知错误码')
            error_message = result.get('message', '未知错误')
            logger.error(f"获取热词表列表失败, 错误码: {error_code}, 错误信息: {error_message}")
            
        return result
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP错误: {http_err}")
        try:
            error_json = http_err.response.json()
            logger.error(f"错误详情: {error_json}")
            return error_json
        except:
            return {"code": "HTTPError", "message": str(http_err)}
            
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"连接错误: {conn_err}")
        return {"code": "ConnectionError", "message": "无法连接到阿里云服务，请检查网络连接"}
        
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"请求超时: {timeout_err}")
        return {"code": "TimeoutError", "message": "请求超时，请稍后再试"}
        
    except requests.exceptions.JSONDecodeError as json_err:
        logger.error(f"JSON解析错误: {json_err}")
        return {"code": "JSONDecodeError", "message": "无法解析API响应"}
        
    except Exception as e:
        logger.error(f"获取热词表列表时发生未知错误: {str(e)}", exc_info=True)
        return {"code": "UnknownError", "message": str(e)}

def query_vocabulary(vocabulary_id):
    """查询指定热词表"""
    api_key = os.getenv('DASHSCOPE_API_KEY', '')
    if not api_key:
        logger.error("缺少DASHSCOPE_API_KEY环境变量")
        raise ValueError("缺少DASHSCOPE_API_KEY环境变量")
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/customization"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "speech-biasing",
        "input": {
            "action": "query_vocabulary",
            "vocabulary_id": vocabulary_id
        }
    }
    
    logger.info(f"准备查询热词表详情，词汇表ID: {vocabulary_id}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if 'output' in result:
            logger.info(f"成功获取热词表详情，词汇表ID: {vocabulary_id}")
            
            # 记录热词数量等关键信息
            if 'vocabulary' in result['output']:
                hot_words_count = len(result['output'].get('vocabulary', []))
                logger.info(f"热词表包含 {hot_words_count} 个热词")
        else:
            error_code = result.get('code', '未知错误码')
            error_message = result.get('message', '未知错误')
            logger.error(f"获取热词表详情失败, 词汇表ID: {vocabulary_id}, 错误码: {error_code}, 错误信息: {error_message}")
            
        return result
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP错误: {http_err}")
        try:
            error_json = http_err.response.json()
            logger.error(f"错误详情: {error_json}")
            return error_json
        except:
            return {"code": "HTTPError", "message": str(http_err)}
            
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"连接错误: {conn_err}")
        return {"code": "ConnectionError", "message": "无法连接到阿里云服务，请检查网络连接"}
        
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"请求超时: {timeout_err}")
        return {"code": "TimeoutError", "message": "请求超时，请稍后再试"}
        
    except requests.exceptions.JSONDecodeError as json_err:
        logger.error(f"JSON解析错误: {json_err}")
        return {"code": "JSONDecodeError", "message": "无法解析API响应"}
        
    except Exception as e:
        logger.error(f"查询热词表详情时发生未知错误: {str(e)}", exc_info=True)
        return {"code": "UnknownError", "message": str(e)}

def update_vocabulary(vocabulary_id, vocabulary):
    """更新热词表"""
    api_key = os.getenv('DASHSCOPE_API_KEY', '')
    if not api_key:
        logger.error("缺少DASHSCOPE_API_KEY环境变量")
        raise ValueError("缺少DASHSCOPE_API_KEY环境变量")
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/customization"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "speech-biasing",
        "input": {
            "action": "update_vocabulary",
            "vocabulary_id": vocabulary_id,
            "vocabulary": vocabulary
        }
    }
    
    logger.info(f"准备更新热词表，词汇表ID: {vocabulary_id}, 热词数量: {len(vocabulary)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if 'output' in result and 'task_id' in result['output']:
            logger.info(f"热词表更新任务已提交，任务ID: {result['output']['task_id']}")
        else:
            error_code = result.get('code', '未知错误码')
            error_message = result.get('message', '未知错误')
            logger.error(f"更新热词表失败, 词汇表ID: {vocabulary_id}, 错误码: {error_code}, 错误信息: {error_message}")
            
        return result
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP错误: {http_err}")
        try:
            error_json = http_err.response.json()
            logger.error(f"错误详情: {error_json}")
            return error_json
        except:
            return {"code": "HTTPError", "message": str(http_err)}
            
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"连接错误: {conn_err}")
        return {"code": "ConnectionError", "message": "无法连接到阿里云服务，请检查网络连接"}
        
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"请求超时: {timeout_err}")
        return {"code": "TimeoutError", "message": "请求超时，请稍后再试"}
        
    except requests.exceptions.JSONDecodeError as json_err:
        logger.error(f"JSON解析错误: {json_err}")
        return {"code": "JSONDecodeError", "message": "无法解析API响应"}
        
    except Exception as e:
        logger.error(f"更新热词表时发生未知错误: {str(e)}", exc_info=True)
        return {"code": "UnknownError", "message": str(e)}

def delete_vocabulary(vocabulary_id):
    """删除热词表"""
    api_key = os.getenv('DASHSCOPE_API_KEY', '')
    if not api_key:
        logger.error("缺少DASHSCOPE_API_KEY环境变量")
        raise ValueError("缺少DASHSCOPE_API_KEY环境变量")
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/customization"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "speech-biasing",
        "input": {
            "action": "delete_vocabulary",
            "vocabulary_id": vocabulary_id
        }
    }
    
    logger.info(f"准备删除热词表，词汇表ID: {vocabulary_id}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if 'output' in result:
            logger.info(f"成功删除热词表，词汇表ID: {vocabulary_id}")
        else:
            error_code = result.get('code', '未知错误码')
            error_message = result.get('message', '未知错误')
            logger.error(f"删除热词表失败, 词汇表ID: {vocabulary_id}, 错误码: {error_code}, 错误信息: {error_message}")
            
            # 记录特定错误码的详细信息
            if error_code == 'ResourceNotFound':
                logger.error(f"找不到指定的热词表: {vocabulary_id}")
            elif error_code == 'InvalidApiKey':
                logger.error("API密钥无效，请检查DASHSCOPE_API_KEY环境变量")
            elif error_code == 'AccessDenied':
                logger.error("没有访问权限，请确认账户是否开通了相关服务")
            
        return result
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP错误: {http_err}")
        try:
            error_json = http_err.response.json()
            logger.error(f"错误详情: {error_json}")
            return error_json
        except:
            return {"code": "HTTPError", "message": str(http_err)}
            
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"连接错误: {conn_err}")
        return {"code": "ConnectionError", "message": "无法连接到阿里云服务，请检查网络连接"}
        
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"请求超时: {timeout_err}")
        return {"code": "TimeoutError", "message": "请求超时，请稍后再试"}
        
    except requests.exceptions.JSONDecodeError as json_err:
        logger.error(f"JSON解析错误: {json_err}")
        return {"code": "JSONDecodeError", "message": "无法解析API响应"}
        
    except Exception as e:
        logger.error(f"删除热词表时发生未知错误: {str(e)}", exc_info=True)
        return {"code": "UnknownError", "message": str(e)}

# 设置事件循环策略
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:
    # 使用nest_asyncio允许嵌套使用同一个事件循环
    nest_asyncio.apply()
    
    # 更健壮的事件循环设置
    try:
        # 尝试获取当前事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 如果事件循环已关闭，创建一个新的
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except Exception as e:
        # 出现任何错误都重新创建事件循环
        logger.error(f"设置事件循环时出错: {str(e)}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # 设置退出处理以确保正确关闭
    import atexit
    def cleanup_resources():
        """清理应用程序资源"""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                logger.info("关闭事件循环...")
                loop.close()
        except Exception as e:
            logger.error(f"关闭事件循环时出错: {str(e)}")
    
    # 注册退出处理函数
    atexit.register(cleanup_resources)

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入项目组件
from session.state import session_state
from ui.components.dimension_editor import DimensionEditor
from ui.components.video_preview import VideoPreview
from core.processor import VideoProcessor
from core.composer import VideoComposer, VideoSegment
from config import config

# 配置日志
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'app.log'))
    ]
)

logger = logging.getLogger(__name__)

# 添加直接从磁盘获取项目列表的函数
def get_projects_from_disk():
    """直接从磁盘获取项目列表，不依赖缓存"""
    try:
        # 确保每次都获取最新的项目列表
        # 使用绝对路径确保找到正确的文件
        abs_path = os.path.abspath(os.path.join('data', 'session'))
        logger.info(f"正在扫描目录: {abs_path}")
        
        # 首先列出目录内容
        files = os.listdir(abs_path)
        settings_files = [f for f in files if f.endswith('_settings.json')]
        
        # 提取项目名称
        projects = []
        for file in settings_files:
            # 从文件名 "project_name_settings.json" 中提取项目名
            project_name = file.replace("_settings.json", "")
            projects.append(project_name)
        
        logger.info(f"找到 {len(projects)} 个项目: {', '.join(projects)}")
        return sorted(projects)
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

# 在 get_projects_from_disk 函数后添加一个强制删除函数
def force_delete_project(project_name):
    """直接使用系统命令强制删除项目文件"""
    try:
        # 获取绝对路径
        abs_path = os.path.abspath(os.path.join('data', 'session'))
        settings_file = os.path.join(abs_path, f"{project_name}_settings.json")
        results_file = os.path.join(abs_path, f"{project_name}_results.json")
        
        logger.info(f"准备删除项目 '{project_name}'")
        logger.info(f"设置文件路径: {settings_file}")
        logger.info(f"结果文件路径: {results_file}")
        
        # 使用多种方法尝试删除
        success = False
        
        # 检查文件是否存在
        if not os.path.exists(settings_file):
            logger.warning(f"设置文件不存在: {settings_file}")
            # 如果设置文件不存在，我们认为这是成功的
            success = True
        else:
            # 记录文件属性以便调试
            try:
                file_stat = os.stat(settings_file)
                logger.info(f"文件权限: {oct(file_stat.st_mode)}, 拥有者: {file_stat.st_uid}")
            except Exception as stat_err:
                logger.error(f"无法获取文件属性: {str(stat_err)}")
            
            # 尝试方法1: 使用os.remove
            try:
                logger.info("尝试使用os.remove删除设置文件")
                os.remove(settings_file)
                if not os.path.exists(settings_file):
                    logger.info("成功删除设置文件")
                    success = True
                else:
                    logger.warning("文件仍然存在，尝试其他方法")
            except PermissionError as perm_err:
                logger.error(f"权限错误: {str(perm_err)}")
                # 尝试更改文件权限后再次删除
                try:
                    logger.info("尝试更改文件权限后删除")
                    os.chmod(settings_file, 0o777)
                    os.remove(settings_file)
                    if not os.path.exists(settings_file):
                        logger.info("权限更改后成功删除设置文件")
                        success = True
                    else:
                        logger.warning("更改权限后，文件仍然存在")
                except Exception as chmod_err:
                    logger.error(f"更改权限并删除失败: {str(chmod_err)}")
            except FileNotFoundError:
                logger.info("文件已不存在，视为删除成功")
                success = True
            except Exception as e:
                logger.error(f"使用os.remove删除设置文件失败: {str(e)}")
        
        # 尝试方法2: 使用系统命令(如果文件仍然存在)
        if os.path.exists(settings_file):
            try:
                logger.info("尝试使用系统命令删除设置文件")
                # 使用subprocess而不是os.system以获取错误输出
                result = subprocess.run(["rm", "-f", settings_file], 
                                      capture_output=True, text=True, check=False)
                
                if result.returncode != 0:
                    logger.error(f"系统命令删除失败: {result.stderr}")
                    logger.debug(f"命令输出: {result.stdout}")
                else:
                    logger.info("系统命令删除成功")
                    if os.path.exists(settings_file):
                        logger.warning("尽管命令成功执行，文件仍然存在")
                    else:
                        success = True
            except Exception as e:
                logger.error(f"执行系统命令失败: {str(e)}")
                
            # 如果仍然存在，尝试使用shell=True参数
            if os.path.exists(settings_file):
                try:
                    logger.info("尝试使用shell=True方式删除设置文件")
                    result = subprocess.run(f"rm -f '{settings_file}'", 
                                          shell=True, capture_output=True, text=True, check=False)
                    
                    if result.returncode != 0:
                        logger.error(f"shell命令删除失败: {result.stderr}")
                        logger.debug(f"命令输出: {result.stdout}")
                    else:
                        logger.info("shell命令删除成功")
                        if os.path.exists(settings_file):
                            logger.warning("尽管shell命令成功执行，文件仍然存在")
                        else:
                            success = True
                except Exception as e:
                    logger.error(f"执行shell命令失败: {str(e)}")
        
        # 最后尝试使用sudo（如果可用）
        if os.path.exists(settings_file):
            try:
                logger.info("尝试使用sudo命令删除设置文件")
                # 注意：这需要用户有sudo权限，而且可能会要求输入密码
                result = subprocess.run(f"sudo rm -f '{settings_file}'", 
                                      shell=True, capture_output=True, text=True, check=False)
                
                if result.returncode != 0:
                    logger.error(f"sudo命令删除失败: {result.stderr}")
                else:
                    logger.info("sudo命令删除成功")
                    success = not os.path.exists(settings_file)
            except Exception as e:
                logger.error(f"执行sudo命令失败: {str(e)}")
        
        # 尝试删除结果文件（如果存在）
        if os.path.exists(results_file):
            try:
                logger.info("尝试删除结果文件")
                os.remove(results_file)
                logger.info("成功删除结果文件")
            except PermissionError:
                logger.warning("删除结果文件时出现权限错误，尝试其他方法")
                try:
                    # 尝试使用系统命令删除
                    subprocess.run(["rm", "-f", results_file], check=False)
                    if not os.path.exists(results_file):
                        logger.info("使用系统命令成功删除结果文件")
                    else:
                        logger.warning("结果文件删除失败，但这不影响主要功能")
                except Exception as rm_err:
                    logger.error(f"使用系统命令删除结果文件失败: {str(rm_err)}")
            except Exception as e:
                logger.error(f"删除结果文件失败: {str(e)}")
                logger.warning("结果文件删除失败，但这不影响主要功能")
        
        # 检查最终结果
        if success or not os.path.exists(settings_file):
            logger.info(f"成功删除项目 '{project_name}'")
            return True
        else:
            logger.error(f"无法删除项目 '{project_name}'，文件仍然存在: {settings_file}")
            return False
            
    except Exception as e:
        logger.error(f"删除项目过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主应用入口"""
    # 页面配置
    st.set_page_config(
        page_title="AI视频分析系统",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 初始化会话状态
    session_state.initialize_session()
    
    # 初始化UI状态变量
    if 'show_delete_confirm' not in st.session_state:
        st.session_state['show_delete_confirm'] = False
    if 'show_delete_dialog' not in st.session_state:
        st.session_state['show_delete_dialog'] = False
    if 'deleted_project_name' not in st.session_state:
        st.session_state['deleted_project_name'] = ""
    
    # 检查是否有已存在的项目，如果没有则创建默认项目
    project_list = get_projects_from_disk()
    if not project_list:
        logger.info("没有找到任何项目，正在创建默认项目...")
        default_project_name = "default"
        # 保存默认设置到新项目
        if session_state.save_settings(default_project_name):
            logger.info(f"已自动创建默认项目: {default_project_name}")
            # 设置当前项目为默认项目
            st.session_state['current_project'] = default_project_name
            # 显示一次性提示
            st.session_state['show_default_project_created'] = True
        else:
            logger.error("创建默认项目失败")
    
    # 显示默认项目创建的提示
    if st.session_state.get('show_default_project_created', False):
        st.info("已自动创建默认项目 'default'，可以开始使用系统功能了！您也可以在侧边栏创建自定义项目。")
        # 只显示一次提示
        st.session_state['show_default_project_created'] = False
    
    # 侧边栏导航
    with st.sidebar:
        st.title("AI视频分析系统")
        st.caption("本系统用于智能分析视频内容，提取关键片段并合成宣传视频。")
        
        # 导航菜单
        page = st.radio(
            "导航菜单",
            ["热词管理", "维度设置", "视频分析", "结果管理"]
        )
        
        # 项目管理区域 - 减少上方间距
        st.subheader("项目管理")
        
        # 加载项目部分 - 更精简的界面
        st.write("**加载项目**")
        
        # 获取可用项目列表 - 直接从磁盘读取，不用缓存
        project_list = get_projects_from_disk()
        
        # 布局：下拉框、加载按钮和刷新按钮在同一行
        col_select, col_load, col_refresh = st.columns([3, 1, 1])
        with col_select:
            selected_project = st.selectbox(
                "请选择要加载的项目",
                options=project_list,
                index=0 if project_list else 0,
                placeholder="选择项目...",
                label_visibility="collapsed"
            )
        
        # 加载按钮
        with col_load:
            load_clicked = st.button("加载", key="load_project")
            
        # 刷新按钮
        with col_refresh:
            refresh_clicked = st.button("🔄", key="refresh_projects", help="刷新项目列表")
            if refresh_clicked:
                # 强制刷新项目列表
                st.rerun()
        
        # 处理加载逻辑并显示提示
        if load_clicked:
            if session_state.load_settings(selected_project):
                st.success(f"项目 '{selected_project}' 已加载")
                st.session_state['current_project'] = selected_project
            else:
                st.error(f"未找到项目 '{selected_project}'")
                    
# 显示当前项目 - 更紧凑的布局
        if 'current_project' in st.session_state and st.session_state['current_project']:
            current_project = st.session_state['current_project']
            
            # 使用一行显示项目名和删除按钮
            project_row = st.container()
            
            with project_row:
                cols = st.columns([0.85, 0.15])
                
                with cols[0]:
                    # 显示项目名称
                    st.markdown(f"**当前项目：** {current_project}")
                
                with cols[1]:
                    # 添加删除按钮，默认透明度低
                    st.markdown("""
                    <style>
                    .delete-btn-wrapper button {
                        opacity: 0.2;
                        transition: opacity 0.3s ease;
                    }
                    .stButton:hover button {
                        opacity: 1 !important;
                    }
                    </style>
                    <div class="delete-btn-wrapper">
                    """, unsafe_allow_html=True)
                    delete_btn = st.button("❌", key="delete_project", help="删除该项目")
                    st.markdown("</div>", unsafe_allow_html=True)
            
            if delete_btn:
                # 设置删除确认状态
                st.session_state['show_delete_confirm'] = True
            
            # 显示删除确认
            if st.session_state.get('show_delete_confirm', False):
                # 使用最直接的方式删除
                st.warning(f"确定要删除项目 '{current_project}' 吗？此操作不可撤销。")
                confirm_col1, confirm_col2 = st.columns(2)
                
                with confirm_col1:
                    if st.button("确认删除", key="confirm_delete"):
                        # 直接强制删除
                        success = force_delete_project(current_project)
                        
                        if success:
                            # 清理会话状态
                            if 'current_project' in st.session_state:
                                deleted_project = st.session_state['current_project']
                                st.session_state.pop('current_project', None)
                                
                                # 设置状态标记删除成功
                                st.session_state['show_delete_dialog'] = True
                                st.session_state['deleted_project_name'] = deleted_project
                                st.session_state.pop('show_delete_confirm', None)
                            
                            # 彻底刷新页面
                            st.session_state.force_refresh = True
                            st.rerun()
                        else:
                            st.error(f"删除项目失败，请尝试重启应用或手动删除文件")
                
                with confirm_col2:
                    if st.button("取消", key="cancel_delete"):
                        # 取消删除操作，重置状态
                        st.session_state.pop('show_delete_confirm', None)
                        st.rerun()
        
        # 显示删除成功对话框
        if st.session_state.get('show_delete_dialog', False):
            deleted_name = st.session_state.get('deleted_project_name', '')
            
            # 使用一个普通的Streamlit容器来显示弹窗
            delete_dialog = st.container()
            with delete_dialog:
                # 创建一个简单的卡片式对话框
                dialog_col1, dialog_col2, dialog_col3 = st.columns([1, 3, 1])
                
                with dialog_col2:
                    # 显示成功消息的卡片
                    with st.container():
                        st.success("✓ 删除成功")
                        st.markdown(f"### 项目 \"{deleted_name}\" 已成功删除！")
                        
                        # 添加间距
                        st.write("")
                        
                        # 知道了按钮
                        if st.button("知道了", key="ok_btn", use_container_width=True, type="primary"):
                            # 关闭对话框
                            st.session_state.pop('show_delete_dialog', None)
                            st.session_state.pop('deleted_project_name', None)
                            st.rerun()
        
        # 使用空白而不是分割线
        st.write("")
        
        # 创建项目部分 - 更紧凑
        st.write("**创建项目**")
        create_col1, create_col2 = st.columns([3, 1])
        with create_col1:
            new_project = st.text_input(
                "创建新项目",
                value="",
                placeholder="输入新项目名称",
                label_visibility="collapsed"
            )
        
        # 布局：按钮在右
        with create_col2:
            save_clicked = st.button("保存", key="save_project")
        
        # 处理创建逻辑并显示提示
        if save_clicked:
            if new_project:
                if session_state.save_settings(new_project):
                    st.success(f"项目 '{new_project}' 已创建")
                    st.session_state['current_project'] = new_project
                    # 重新加载页面以更新项目列表
                    st.rerun()
            else:
                st.error("请输入项目名称")
        
        # 在侧边栏底部显示版本信息，使用空白垫底
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        # 版本信息移到最底部
        st.caption("AI视频分析系统 v1.0.0")
    
    # 根据导航加载对应页面
    if page == "热词管理":
        show_wordlist_page()
    elif page == "维度设置":
        show_dimension_page()
    elif page == "视频分析":
        show_analysis_page()
    elif page == "结果管理":
        show_results_page()

def show_wordlist_page():
    """显示热词管理页面"""
    st.header("热词管理")
    st.markdown("创建和管理用于语音识别的热词库，提高关键词识别准确率。")
    
    # 确保settings存在
    if 'settings' not in st.session_state:
        st.session_state.settings = session_state.get_default_settings()
    
    # 热词列表
    st.subheader("热词列表")
    
    # 初始化热词列表（如果不存在）
    if 'hot_words' not in st.session_state.settings:
        st.session_state.settings['hot_words'] = []
    
    # 创建热词数据框
    if st.session_state.settings['hot_words']:
        hot_words_data = []
        for hw in st.session_state.settings['hot_words']:
            # 移除类别信息，只保留基本字段
            hot_words_data.append({
                '热词': hw.get('text', ''),
                '权重': hw.get('weight', 4),
                '语言': hw.get('lang', 'zh')
            })
        
        df = pd.DataFrame(hot_words_data)
    else:
        df = pd.DataFrame(columns=['热词', '权重', '语言'])
    
    # 防御性检查：确保df是DataFrame而不是dict
    if not isinstance(df, pd.DataFrame):
        logger.warning(f"预期df为DataFrame，实际为{type(df)}")
        df = pd.DataFrame(df) if isinstance(df, dict) else pd.DataFrame()
    
    # 顶部添加批量操作区域
    st.subheader("批量操作", divider="gray")
    bulk_col1, bulk_col2, bulk_col3 = st.columns([1, 1, 1])
    
    with bulk_col1:
        default_weight = 4
        bulk_weight = st.number_input(
            "批量设置权重", 
            min_value=1, 
            max_value=5, 
            value=default_weight,
            step=1,
            help="同时设置选定热词的权重值"
        )
    
    with bulk_col2:
        bulk_lang = st.selectbox(
            "批量设置语言",
            options=["zh", "en"],
            index=0,
            help="同时设置选定热词的语言(zh:中文, en:英文)"
        )
    
    with bulk_col3:
        bulk_apply = st.button("应用到选中行", use_container_width=True)
        bulk_clear = st.button("清空所有", use_container_width=True)
    
    # 如果点击清空按钮，提示确认
    if bulk_clear:
        clear_confirm = st.warning("确定要清空所有热词吗？此操作不可撤销。", icon="⚠️")
        clear_col1, clear_col2 = st.columns([1, 1])
        with clear_col1:
            if st.button("确认清空", type="primary", use_container_width=True):
                df = pd.DataFrame(columns=['热词', '权重', '语言'])
                st.success("已清空所有热词")
                st.rerun()
        with clear_col2:
            if st.button("取消", type="secondary", use_container_width=True):
                st.rerun()
    
    st.subheader("热词列表编辑", divider="gray")
    
    # 可编辑表格 - 增强版本，支持语言选择
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "热词": st.column_config.TextColumn(
                "热词",
                width="large",
                help="每个词语最长10个汉字或英文单词"
            ),
            "权重": st.column_config.NumberColumn(
                "权重", 
                min_value=1,
                max_value=5,
                step=1,
                format="%d",
                width="small",
                default=4,
                help="取值范围为[1, 5]之间的整数，常用值：4"
            ),
            "语言": st.column_config.SelectboxColumn(
                "语言",
                width="small",
                options=["zh", "en"],
                default="zh",
                help="zh: 中文, en: 英文"
            )
        },
        use_container_width=True,
        key="hot_words_editor",
        hide_index=True,
        height=400
    )
    
    # 应用批量操作到选中行
    if bulk_apply and edited_df is not None and len(edited_df) > 0:
        selection = st.session_state.get("hot_words_editor_selected_rows", [])
        if selection:
            # 获取选中行的索引
            selected_indices = [int(idx) for idx in selection]
            
            # 应用批量操作
            for idx in selected_indices:
                if idx < len(edited_df):
                    edited_df.at[idx, '权重'] = bulk_weight
                    edited_df.at[idx, '语言'] = bulk_lang
            
            st.success(f"已将权重 {bulk_weight} 和语言 {bulk_lang} 应用到 {len(selected_indices)} 个选中热词")
    
    # 显示选择的行数和总行数统计
    if edited_df is not None and len(edited_df) > 0:
        total_rows = len(edited_df)
        valid_rows = edited_df['热词'].notna().sum()
        st.caption(f"共有 {valid_rows} 个有效热词 (总计 {total_rows} 行)")
    
    # 添加热词列表名称输入框
    hotword_list_name = st.text_input("热词列表名称", value="", placeholder="请输入热词列表名称", help="此名称将用作保存文件的文件名")
    
    # 添加保存按钮，只有在用户点击时才处理数据
    save_btn_col1, save_btn_col2, save_btn_col3 = st.columns([1, 2, 3])
    with save_btn_col1:
        if st.button("保存热词列表", key="save_hot_words", type="secondary", use_container_width=True):
            try:
                # 检查列表名称
                if not hotword_list_name:
                    st.error("请先输入热词列表名称")
                    st.stop()
                
                # 清空现有热词
                new_hot_words = []
                
                # 处理编辑后的数据
                for _, row in edited_df.iterrows():
                    # 跳过空行
                    if pd.isna(row.get('热词')):
                        continue
                        
                    text = str(row.get('热词', '')).strip()
                    if text and len(text) <= 10:
                        # 确保权重是有效的整数
                        try:
                            weight = int(row.get('权重', 4))
                            weight = max(1, min(5, weight))  # 确保在1-5之间
                        except:
                            weight = 4  # 默认值
                        
                        # 获取语言设置
                        lang = row.get('语言', 'zh')
                        if not lang or lang not in ['zh', 'en']:
                            lang = 'zh'  # 默认使用中文
                            
                new_hot_words.append({
                            'text': text,
                            'weight': weight,
                            'lang': lang
                        })
                
                # 更新设置
                st.session_state.settings['hot_words'] = new_hot_words
                st.session_state.settings['hot_words_name'] = hotword_list_name
                
                # 使用指定的列表名称作为文件名
                save_path = os.path.abspath(os.path.join('data', 'session', f"{hotword_list_name}_hotwords.json"))
                
                # 保存热词列表到单独的文件
                try:
                    # 确保目录存在
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    # 保存到文件
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(new_hot_words, f, ensure_ascii=False, indent=2)
                    
                    # 同时保存设置到当前项目
                    try:
                        current_project = st.session_state.get('current_project', 'default')
                        if current_project is None:
                            current_project = 'default'  # 确保项目名称不为None
                        
                        # 使用当前项目名称保存设置
                        session_state.save_settings(current_project)
                    except Exception as e:
                        logger.error(f"保存项目设置失败: {str(e)}")
                    
                    # 保存成功后，将信息显示在按钮右侧的两个列中
                    with save_btn_col2:
                        st.markdown(f"<div style='background-color:#d4edda; padding:10px; border-radius:5px;'>✅ 成功保存热词列表\"{hotword_list_name}\"，共 {len(new_hot_words)} 个热词</div>", unsafe_allow_html=True)
                    with save_btn_col3:
                        # 显示路径时使用更简洁的相对路径
                        short_path = os.path.join('data/session', f"{hotword_list_name}_hotwords.json")
                        st.markdown(f"<div style='background-color:#d1ecf1; padding:10px; border-radius:5px;'>ℹ️ 保存路径: {short_path}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"保存文件失败: {str(e)}")
            except Exception as e:
                st.error(f"保存热词失败: {str(e)}")
    
    # 添加一些间距
    st.write("")
    
    # 直接添加创建阿里云热词列表按钮
    create_hotwords_col1, create_hotwords_col2 = st.columns([1, 3])
    with create_hotwords_col1:
        create_cloud_btn = st.button("创建阿里云热词列表", key="create_dashscope_vocab", type="primary", use_container_width=True)
    
    with create_hotwords_col2:
        # 显示信息提示
        st.markdown("""
        <div style='background-color:#f8f9fa; padding:10px; border-radius:5px; font-size:0.9em;'>
            ℹ️ <b>创建阿里云热词列表</b> 将当前热词提交到阿里云语音识别服务，提高关键词识别准确率。
            创建成功后，词汇表ID将被自动保存，可用于语音识别。
        </div>
        """, unsafe_allow_html=True)
    
    if create_cloud_btn:
        if not st.session_state.settings['hot_words']:
            st.error("请先添加热词")
        elif not hotword_list_name:
            st.error("请先输入热词列表名称")
        else:
            # 创建进度条和状态容器
            progress_container = st.container()
            status_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            try:
                # 确保前缀不超过10个字符（阿里云API限制）并且只包含英文字母和数字
                # 先移除非法字符
                prefix_name = re.sub(r'[^a-zA-Z0-9]', '', hotword_list_name)
                
                # 如果前缀名称超过6个字符，取前6个字符
                if len(prefix_name) > 6:
                    prefix_name = prefix_name[:6]
                
                # 使用短时间戳（最后4位数字）生成唯一标识
                time_suffix = str(int(time.time()))[-4:]
                auto_prefix = f"{prefix_name}{time_suffix}"
                
                # 如果前缀仍然超过10个字符，进一步截断
                if len(auto_prefix) > 10:
                    auto_prefix = auto_prefix[:10]
                
                # 确保前缀不为空
                if not auto_prefix:
                    auto_prefix = f"hw{time_suffix}"
                
                # 默认使用最常用的模型
                default_model = "paraformer-v2"
                
                # 更新进度条
                status_text.text("正在检查环境配置...")
                progress_bar.progress(10)
                
                # 检查API密钥是否设置
                api_key = os.getenv('DASHSCOPE_API_KEY', '')
                if not api_key:
                    with status_container:
                        st.error("缺少DASHSCOPE_API_KEY环境变量，无法创建热词列表")
                        st.info("请在.env文件中添加以下内容：\n```\nDASHSCOPE_API_KEY=您的阿里云API密钥\n```")
                        # 显示设置环境变量的帮助链接
                        st.markdown("[点击此处了解如何获取阿里云API密钥](https://help.aliyun.com/document_detail/175553.html)")
                    logger.error("缺少DASHSCOPE_API_KEY环境变量")
                    progress_bar.progress(100)
                    status_text.text("环境配置检查失败")
                    st.stop()
                
                # 更新进度条
                status_text.text("正在准备热词数据...")
                progress_bar.progress(30)
                
                # 对热词进行格式化，确保符合阿里云API要求
                formatted_hotwords = []
                for hw in st.session_state.settings['hot_words']:
                    # 确保传递正确格式
                    formatted_hw = {
                        'text': hw['text'],
                        'weight': hw['weight'],
                        'lang': hw.get('lang', 'zh')
                    }
                    formatted_hotwords.append(formatted_hw)
                
                # 记录API调用信息
                logger.info(f"准备创建阿里云热词列表，前缀:{auto_prefix}, 模型:{default_model}, 热词数量:{len(formatted_hotwords)}")
                
                # 更新进度条
                status_text.text("正在提交到阿里云...")
                progress_bar.progress(50)
                
                # 使用格式化后的热词调用API
                try:
                    # 调用前确认热词数量不为0
                    if len(formatted_hotwords) == 0:
                        with status_container:
                            st.error("无法创建热词列表：热词数量为0")
                            logger.error("热词数量为0，无法创建热词列表")
                            progress_bar.progress(100)
                            status_text.text("创建失败")
                            st.stop()
                    
                    # 检查前缀长度
                    if len(auto_prefix) > 10:
                        old_prefix = auto_prefix
                        auto_prefix = auto_prefix[:10]
                        with status_container:
                            st.warning(f"前缀 '{old_prefix}' 超过10个字符，已自动截断为 '{auto_prefix}'")
                            logger.warning(f"前缀过长，已截断: {old_prefix} -> {auto_prefix}")
                    
                    # 检查热词文本长度，过滤掉超长热词
                    invalid_hotwords = [hw['text'] for hw in formatted_hotwords if len(hw['text']) > 10]
                    if invalid_hotwords:
                        # 过滤掉超长热词
                        valid_hotwords = [hw for hw in formatted_hotwords if len(hw['text']) <= 10]
                        formatted_hotwords = valid_hotwords
                        
                        with status_container:
                            st.warning(f"已自动过滤 {len(invalid_hotwords)} 个超长热词(最大10个字符): {', '.join(invalid_hotwords[:5])}" + 
                                    ("..." if len(invalid_hotwords) > 5 else ""))
                            logger.warning(f"已过滤超长热词: {invalid_hotwords}")
                            
                        # 如果过滤后没有合法热词，显示错误并停止
                        if len(formatted_hotwords) == 0:
                            with status_container:
                                st.error("所有热词都超出长度限制，无法创建热词列表")
                                progress_bar.progress(100)
                                status_text.text("创建失败")
                                st.stop()
                        else:
                            # 显示过滤后的合法热词数量
                            st.info(f"将使用 {len(formatted_hotwords)} 个合法热词创建热词列表")
                    
                    # 添加网络请求超时设置
                    result = create_vocabulary(auto_prefix, default_model, formatted_hotwords)
                    logger.info(f"API响应: {result}")
                    
                    # 更新进度条
                    progress_bar.progress(80)
                    
                    with status_container:
                        if 'output' in result:
                            if 'task_id' in result['output']:
                                task_id = result['output']['task_id']
                                message = f"词汇表创建任务已提交，任务ID: {task_id}"
                                logger.info(message)
                                
                                # 更新进度条
                                progress_bar.progress(100)
                                status_text.text("创建任务已成功提交")
                                
                                # 显示成功消息
                                st.success(message)
                                st.info("请在「词汇表列表」标签中查看结果，可能需要等待1-2分钟后刷新列表")
                            
                            elif 'vocabulary_id' in result['output']:
                                vocabulary_id = result['output']['vocabulary_id']
                                message = f"词汇表创建成功，ID: {vocabulary_id}"
                                logger.info(message)
                                
                                # 更新进度条
                                progress_bar.progress(100)
                                status_text.text("创建成功")
                                
                                # 显示成功消息
                                st.success(message)
                                
                                # 将新创建的词汇表添加到会话状态
                                if 'vocabulary_ids' not in st.session_state.settings:
                                    st.session_state.settings['vocabulary_ids'] = []
                                
                                # 提取前缀
                                prefix = ''
                                if '-' in vocabulary_id:
                                    parts = vocabulary_id.split('-')
                                    if len(parts) > 1:
                                        prefix = parts[1]
                                
                                # 添加到词汇表列表
                                st.session_state.settings['vocabulary_ids'].append({
                                    'vocabulary_id': vocabulary_id,
                                    'prefix': prefix,
                                    'gmt_create': time.strftime("%Y-%m-%d %H:%M:%S"),
                                    'gmt_modified': time.strftime("%Y-%m-%d %H:%M:%S"),
                                    'status': 'OK',
                                    'target_model': default_model
                                })
                                
                                # 显示创建详情
                                st.json({
                                    "词汇表ID": vocabulary_id,
                                    "前缀": auto_prefix,
                                    "模型": default_model,
                                    "热词数量": len(formatted_hotwords),
                                    "创建时间": time.strftime("%Y-%m-%d %H:%M:%S")
                                })
                                
                                st.info("热词列表已添加到词汇表列表中，可以在「词汇表列表」标签查看")
                            else:
                                error_code = result.get('code', 'UNKNOWN')
                                error_message = result.get('message', '未知错误')
                                
                                # 更新进度条
                                progress_bar.progress(100)
                                status_text.text("创建失败")
                                
                                error_msg = f"创建失败: {error_message}"
                                if error_code != 'UNKNOWN':
                                    error_msg += f" (错误代码: {error_code})"
                                
                                logger.error(error_msg)
                                st.error(error_msg)
                                
                                # 提供更具体的错误指导和解决方案
                                if error_code == 'InvalidApiKey':
                                    st.error("API密钥无效，请检查DASHSCOPE_API_KEY环境变量")
                                    st.info("请在阿里云官网获取正确的API密钥，并更新您的环境变量")
                                elif error_code == 'QuotaExceeded':
                                    st.error("已超出API配额限制")
                                    st.info("请前往阿里云控制台检查您的账户余额或提高API使用限额")
                                elif error_code == 'AccessDenied':
                                    st.error("没有访问权限")
                                    st.info("请确认您的阿里云账户已开通DashScope服务，并具有相应的访问权限")
                                elif error_code == 'InvalidParameter':
                                    st.error(f"参数错误: {error_message}")
                                    if "prefix should not be longer than 10 characters" in error_message:
                                        st.info("热词列表名称过长，应保持在10个字符以内。请使用更短的前缀重试。")
                                    elif "prefix should be english letter and number" in error_message:
                                        st.info("热词列表前缀只能包含英文字母和数字。已自动修正，请重试。")
                                    elif "vocabulary is too large" in error_message:
                                        st.info("热词表过大，每个热词列表最多包含500个热词，请减少热词数量后重试。")
                                    elif "text should not be longer than 10 characters" in error_message:
                                        st.info("存在超过10个字符的热词，请确保每个热词不超过10个字符。")
                                    else:
                                        st.info("请检查参数是否符合阿里云API要求，详情可参考阿里云文档: https://help.aliyun.com/zh/model-studio/paraformer-recorded-speech-recognition-python-api")
                    
                    # 检查热词文本长度，过滤掉超长热词
                    invalid_hotwords = [hw['text'] for hw in formatted_hotwords if len(hw['text']) > 10]
                    if invalid_hotwords:
                        # 过滤掉超长热词
                        valid_hotwords = [hw for hw in formatted_hotwords if len(hw['text']) <= 10]
                        formatted_hotwords = valid_hotwords
                        
                        with status_container:
                            st.warning(f"已自动过滤 {len(invalid_hotwords)} 个超长热词(最大10个字符): {', '.join(invalid_hotwords[:5])}" + 
                                    ("..." if len(invalid_hotwords) > 5 else ""))
                            logger.warning(f"已过滤超长热词: {invalid_hotwords}")
                            
                        # 如果过滤后没有合法热词，显示错误并停止
                        if len(formatted_hotwords) == 0:
                            with status_container:
                                st.error("所有热词都超出长度限制，无法创建热词列表")
                                progress_bar.progress(100)
                                status_text.text("创建失败")
                                st.stop()
                        else:
                            # 显示过滤后的合法热词数量
                            st.info(f"将使用 {len(formatted_hotwords)} 个合法热词创建热词列表")
                except Exception as api_err:
                    # 更新进度条
                    progress_bar.progress(100)
                    status_text.text("API调用失败")
                    
                    with status_container:
                        st.error(f"API调用失败: {str(api_err)}")
                        logger.error(f"创建词汇表API调用失败: {str(api_err)}")
                        st.info("请检查网络连接和API参数设置")
            except Exception as e:
                # 更新进度条
                progress_bar.progress(100)
                status_text.text("处理失败")
                
                with status_container:
                    st.error(f"处理失败: {str(e)}")
                    logger.error(f"创建热词列表过程中出错: {str(e)}")
    
    # 批量操作
    st.subheader("批量操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.expander("导入热词"):
            upload_file = st.file_uploader(
                "上传CSV、JSON或文本文件", 
                type=["csv", "txt", "json"],
                help="CSV格式：包含'text'和'weight'列。JSON格式：直接导入保存的热词列表文件。文本格式：每行一个热词。"
            )
            
            # 检查当前是否已有热词数据
            has_existing_data = False
            if 'hot_words' in st.session_state.settings and st.session_state.settings['hot_words']:
                has_existing_data = True
                existing_count = len(st.session_state.settings['hot_words'])
                st.info(f"当前已有 {existing_count} 个热词。导入新热词会替换现有热词。")
            
            if upload_file:
                col_import1, col_import2 = st.columns([1, 1])
                with col_import1:
                    import_clicked = st.button("导入", key="btn_import_hotwords")
                
                
                if import_clicked:
                    # 导入hotword_utils模块处理热词导入
                    from hotword_utils import import_hotwords_from_file
                    
                    # 调用模块化的导入函数
                    imported_hotwords, list_name = import_hotwords_from_file(
                        upload_file, 
                        append_mode=append_mode, 
                        has_existing_data=has_existing_data
                    )
                    
                    # 处理导入结果
                    if imported_hotwords is not None:
                        # 替换或追加热词
                        if not append_mode or not has_existing_data:
                            # 替换模式
                            st.session_state.settings['hot_words'] = imported_hotwords
                        
                        # 设置热词列表名称
                        if list_name:
                            st.session_state.settings['hot_words_name'] = list_name
                        
                        # 保存当前设置，确保热词列表被持久化
                        try:
                            current_project = st.session_state.get('current_project', 'default')
                            if current_project is None:
                                current_project = 'default'
                            session_state.save_settings(current_project)
                            
                            # 触发页面重新加载以显示导入的热词
                            st.rerun()
                        except Exception as save_err:
                            st.error(f"保存设置失败: {str(save_err)}")
                            logger.error(f"保存热词设置失败: {str(save_err)}")
    
    with col2:
        with st.expander("导出热词"):
            export_format = st.radio(
                "导出格式",
                options=["CSV", "TXT"],
                horizontal=True
            )
            
            if st.button("导出"):
                if st.session_state.settings['hot_words']:
                    if export_format == "CSV":
                        # 确保导出热词时包含类别信息
                        export_data = []
                        for hw in st.session_state.settings['hot_words']:
                            export_item = {
                                'text': hw['text'],
                                'weight': hw['weight'],
                                'lang': hw.get('lang', 'zh')
                            }
                            export_data.append(export_item)
                            
                        df_export = pd.DataFrame(export_data)
                        csv = df_export.to_csv(index=False)
                        st.download_button(
                            "下载CSV",
                            csv,
                            "hotwords.csv",
                            "text/csv",
                            key="download_csv"
                        )
                    else:  # TXT
                        text = "\n".join([hw['text'] for hw in st.session_state.settings['hot_words']])
                        st.download_button(
                            "下载TXT",
                            text,
                            "hotwords.txt",
                            "text/plain",
                            key="download_txt"
                        )
                else:
                    st.warning("没有热词可导出")
    
    with col3:
        with st.expander("批量权重设置"):
            # 选择语言
            lang = st.selectbox(
                "选择语言",
                ["zh", "en"],
                index=0,
                help="选择要设置权重的热词语言"
            )
            
            # 权重设置
            weight = st.slider(
                "设置权重",
                min_value=1,
                max_value=5,
                value=4,
                step=1,
                help="取值范围为[1, 5]之间的整数，常用值：4"
            )
            
            if st.button("应用"):
                if st.session_state.settings['hot_words']:
                    count = 0
                    for hw in st.session_state.settings['hot_words']:
                        if hw.get('lang') == lang:
                            hw['weight'] = int(weight)
                            count += 1
                    
                    if count > 0:
                        st.success(f"已更新 {count} 个热词的权重")
                    else:
                        st.info(f"没有找到{lang}语言的热词")
                else:
                    st.warning("没有热词可设置")

    # 添加热词词汇表管理功能
    st.subheader("词汇表管理")
    
    # 初始化词汇表列表（如果不存在）
    if 'vocabulary_ids' not in st.session_state.settings:
        st.session_state.settings['vocabulary_ids'] = []
    
    # 自动从阿里云获取词汇表列表
    auto_refresh_placeholder = st.empty()
    
    try:
        with auto_refresh_placeholder.container():
            with st.spinner("正在从阿里云获取词汇表列表..."):
                # 检查API密钥是否设置
                api_key = os.getenv('DASHSCOPE_API_KEY', '')
                if not api_key:
                    st.error("缺少DASHSCOPE_API_KEY环境变量，无法获取词汇表列表")
                    st.info("请在环境变量或.env文件中设置DASHSCOPE_API_KEY")
                    logger.error("缺少DASHSCOPE_API_KEY环境变量")
                    
                else:
                    # 调用API获取词汇表列表
                    vocab_list = list_vocabulary()
                    
                    if 'output' in vocab_list and 'vocabulary_list' in vocab_list['output']:
                        # 清空现有列表
                        st.session_state.settings['vocabulary_ids'] = []
                        
                        # 添加新数据
                        for vocab in vocab_list['output']['vocabulary_list']:
                            # 提取前缀部分
                            vocab_id = vocab.get('vocabulary_id', '')
                            prefix = ''
                            if '-' in vocab_id:
                                parts = vocab_id.split('-')
                                if len(parts) > 1:
                                    prefix = parts[1]
                            
                            # 添加到词汇表列表
                            st.session_state.settings['vocabulary_ids'].append({
                                'vocabulary_id': vocab_id,
                                'prefix': prefix,
                                'gmt_create': vocab.get('gmt_create', ''),
                                'gmt_modified': vocab.get('gmt_modified', ''),
                                'status': vocab.get('status', ''),
                                'target_model': vocab.get('target_model', '未知')
                            })
                        
                        total_count = len(vocab_list['output']['vocabulary_list'])
                        success_count = sum(1 for v in vocab_list['output']['vocabulary_list'] if v.get('status') == 'OK')
                        
                        st.success(f"已从阿里云获取 {total_count} 个词汇表（其中 {success_count} 个状态正常）")
                        
                        # 如果有创建中的词汇表，提供提示
                        creating_count = sum(1 for v in vocab_list['output']['vocabulary_list'] if v.get('status') == 'CREATING')
                        if creating_count > 0:
                            st.info(f"有 {creating_count} 个词汇表正在创建中")
                        
                        # 如果有失败的词汇表，提供提示
                        failed_count = sum(1 for v in vocab_list['output']['vocabulary_list'] if v.get('status') == 'FAILED')
                        if failed_count > 0:
                            st.warning(f"有 {failed_count} 个词汇表创建失败，请检查参数后重试")
                        
                    else:
                        error_code = vocab_list.get('code', 'UNKNOWN')
                        error_message = vocab_list.get('message', '未知错误')
                        
                        error_msg = f"获取词汇表失败: {error_message}"
                        if error_code != 'UNKNOWN':
                            error_msg += f" (错误代码: {error_code})"
                        
                        logger.error(error_msg)
                        st.error(error_msg)
                        
                        # 提供更具体的错误指导
                        if error_code == 'InvalidApiKey':
                            st.error("API密钥无效，请检查DASHSCOPE_API_KEY环境变量")
                        elif error_code == 'QuotaExceeded':
                            st.error("已超出API配额限制")
                        elif error_code == 'AccessDenied':
                            st.error("没有访问权限")
                        elif error_code == 'ConnectionError':
                            st.error("无法连接到阿里云服务")
                        elif error_code == 'TimeoutError':
                            st.error("请求超时")
    except Exception as e:
        logger.error(f"刷新词汇表列表失败: {str(e)}", exc_info=True)
        auto_refresh_placeholder.error(f"刷新词汇表列表失败: {str(e)}")
    
    # 清空占位符内容，保持界面整洁
    auto_refresh_placeholder.empty()
    
    # 展示词汇表列表
    st.subheader("词汇表列表")
    
    if not st.session_state.settings['vocabulary_ids']:
        st.info('尚未创建任何词汇表。您可以使用"添加热词"功能添加热词后，通过"创建阿里云热词列表"按钮创建词汇表。')
    else:
        # 显示词汇表列表
        vocab_data = []
        for vocab in st.session_state.settings['vocabulary_ids']:
            # 处理时间显示格式
            create_time = vocab.get('gmt_create', '')
            if create_time:
                try:
                    # 尝试转换时间戳为可读格式
                    create_time_float = float(create_time) / 1000  # 假设时间戳是毫秒格式
                    create_time = datetime.fromtimestamp(create_time_float).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass  # 如果转换失败，保持原样
            
            # 生成状态标签
            status = vocab.get('status', '')
            if status == 'OK':
                status_display = "✅ 正常"
            elif status == 'CREATING':
                status_display = "⏱️ 创建中"
            elif status == 'FAILED':
                status_display = "❌ 失败"
            else:
                status_display = f"⚠️ {status}"
            
            vocab_data.append({
                "ID": vocab.get('vocabulary_id', ''),
                "名称": vocab.get('prefix', ''),
                "模型": vocab.get('target_model', '未知'),
                "创建时间": create_time,
                "状态": status_display
            })
        
        # 创建一个可搜索和排序的DataFrame
        vocab_df = pd.DataFrame(vocab_data)
        
        # 添加搜索框
        search_term = st.text_input("搜索词汇表", placeholder="输入ID或名称搜索", key="vocab_search")
        if search_term:
            # 过滤DataFrame
            vocab_df = vocab_df[
                vocab_df['ID'].str.contains(search_term, case=False, na=False) | 
                vocab_df['名称'].str.contains(search_term, case=False, na=False)
            ]
        
        # 显示带有样式的DataFrame
        # st.dataframe(
        #     vocab_df,
        #     use_container_width=True,
        #     height=300
        # )
        
        # 使用自定义表格展示，以便每行添加删除按钮
        st.markdown("##### 词汇表列表")
        
        # 创建表头
        cols = st.columns([3, 2, 2, 3, 2, 1, 1])
        headers = ["ID", "名称", "模型", "创建时间", "状态", "操作", "查询"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("---")  # 表头与内容分隔线
        
        # 用于存储被删除的词汇表ID
        if 'deleted_vocab_ids' not in st.session_state:
            st.session_state.deleted_vocab_ids = []
            
        # 用于存储已展开查询详情的词汇表ID
        if 'expanded_vocab_ids' not in st.session_state:
            st.session_state.expanded_vocab_ids = []
        
        # 为每行显示数据和操作按钮
        for i, row in vocab_df.iterrows():
            vocab_id = row["ID"]
            
            # 如果该ID已被删除，则跳过
            if vocab_id in st.session_state.deleted_vocab_ids:
                continue
                
            row_cols = st.columns([3, 2, 2, 3, 2, 1, 1])
            row_cols[0].text(row["ID"])
            row_cols[1].text(row["名称"])
            row_cols[2].text(row["模型"])
            row_cols[3].text(row["创建时间"])
            row_cols[4].markdown(row["状态"])
            
            # 删除按钮
            if row_cols[5].button("删除", key=f"delete_btn_{vocab_id}", use_container_width=True):
                try:
                    with st.spinner(f"正在删除词汇表 {vocab_id}..."):
                        result = delete_vocabulary(vocab_id)
                    
                    if 'output' in result:
                        # 从会话状态中移除
                        st.session_state.settings['vocabulary_ids'] = [
                            v for v in st.session_state.settings['vocabulary_ids'] 
                            if v.get('vocabulary_id') != vocab_id
                        ]
                        
                        # 添加到已删除列表
                        st.session_state.deleted_vocab_ids.append(vocab_id)
                        
                        # 显示成功消息
                        st.success(f"已成功删除词汇表 {vocab_id}")
                        time.sleep(1)  # 显示信息后短暂延迟
                        st.rerun()  # 重新加载页面更新列表
                    else:
                        error_code = result.get('code', 'UNKNOWN')
                        error_message = result.get('message', '未知错误')
                        
                        st.error(f"删除失败: {error_message}")
                        if error_code != 'UNKNOWN':
                            st.error(f"错误代码: {error_code}")
                            
                        # 提供错误处理建议
                        if error_code == 'ResourceNotFound':
                            st.warning("找不到指定的词汇表，可能已被删除")
                            # 从会话状态中移除
                            st.session_state.settings['vocabulary_ids'] = [
                                v for v in st.session_state.settings['vocabulary_ids'] 
                                if v.get('vocabulary_id') != vocab_id
                            ]
                            # 添加到已删除列表
                            st.session_state.deleted_vocab_ids.append(vocab_id)
                            st.info("已从本地列表移除")
                            time.sleep(1)
                            st.rerun()  # 重新加载页面更新列表
                except Exception as e:
                    st.error(f"删除失败: {str(e)}")
                    with st.expander("查看详细错误信息"):
                        import traceback
                        st.code(traceback.format_exc(), language="python")
            
            # 查询按钮
            if row_cols[6].button("查询", key=f"query_btn_{vocab_id}", use_container_width=True):
                # 切换展开/折叠状态
                if vocab_id in st.session_state.expanded_vocab_ids:
                    st.session_state.expanded_vocab_ids.remove(vocab_id)
                else:
                    st.session_state.expanded_vocab_ids.append(vocab_id)
                    
            # 如果该词汇表详情已展开，显示详情
            if vocab_id in st.session_state.expanded_vocab_ids:
                with st.container():
                    st.markdown("---")  # 详情与行的分隔线
                    
                    # 创建固定宽度的详情区
                    detail_col = st.container()
                    with detail_col:
                        try:
                            with st.spinner(f"正在查询词汇表 {vocab_id} 的详情..."):
                                result = query_vocabulary(vocab_id)
                            
                            if 'output' in result:
                                # 显示词汇表详情的关键信息
                                vocab_details = result['output']
                                
                                # 创建一个格式化的详情卡片
                                st.markdown(f"""
                                <div style="background-color:#f0f2f6;padding:10px;border-radius:5px;margin-bottom:10px;">
                                    <h5 style="color:#0068c9;">词汇表 {row["名称"]} 详情</h5>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if 'vocabulary' in vocab_details:
                                    hot_words = vocab_details['vocabulary']
                                    
                                    # 有热词数据时显示热词表格
                                    if hot_words:
                                        # 限制展示的热词数量
                                        display_words = hot_words[:10]  # 只展示前10个
                                        
                                        # 创建热词预览表格
                                        hot_words_preview = []
                                        for hw in display_words:
                                            hot_words_preview.append({
                                                "热词": hw.get('text', ''),
                                                "权重": hw.get('weight', 4),
                                                "语言": hw.get('lang', 'zh')
                                            })
                                        
                                        hot_words_count = len(hot_words)
                                        display_count = len(display_words)
                                        
                                        # 显示热词信息
                                        st.markdown(f"<p style='color:#555;'>包含 <b>{hot_words_count}</b> 个热词，显示前 {display_count} 个：</p>", unsafe_allow_html=True)
                                        
                                        # 显示热词表格
                                        st.dataframe(
                                            pd.DataFrame(hot_words_preview),
                                            use_container_width=True,
                                            height=min(200, 50 + 35 * len(display_words))  # 动态调整高度
                                        )
                                        
                                        # 提供导出功能
                                        export_json = json.dumps([
                                            {"text": hw.get('text', ''), "weight": hw.get('weight', 4), "lang": hw.get('lang', 'zh')}
                                            for hw in hot_words
                                        ], ensure_ascii=False, indent=2)
                                        
                                        download_col1, download_col2 = st.columns([1, 5])
                                        with download_col1:
                                            st.download_button(
                                                "导出热词",
                                                export_json,
                                                f"{vocab_id}_hotwords.json",
                                                "application/json",
                                                key=f"download_hw_{vocab_id}"
                                            )
                                        
                                        with download_col2:
                                            if hot_words_count > display_count:
                                                st.caption(f"* 导出的文件包含全部 {hot_words_count} 个热词")
                                    else:
                                        st.warning("该词汇表不包含任何热词")
                                
                                # 添加查看原始JSON的展开选项
                                with st.expander("查看API响应详情"):
                                    st.json(vocab_details)
                            else:
                                error_code = result.get('code', 'UNKNOWN')
                                error_message = result.get('message', '未知错误')
                                
                                st.error(f"查询失败: {error_message}")
                                if error_code != 'UNKNOWN':
                                    st.error(f"错误代码: {error_code}")
                                    
                                # 提供错误处理建议
                                if error_code == 'ResourceNotFound':
                                    st.warning("找不到指定的词汇表，可能已被删除")
                                    st.info("请刷新页面以获取最新状态")
                                    # 从展开列表中移除
                                    if vocab_id in st.session_state.expanded_vocab_ids:
                                        st.session_state.expanded_vocab_ids.remove(vocab_id)
                        except Exception as e:
                            st.error(f"查询失败: {str(e)}")
                            with st.expander("查看详细错误信息"):
                                import traceback
                                st.code(traceback.format_exc(), language="python")
                    
                    st.markdown("---")  # 详情区的结束分隔线
            
            # 行分隔线
            st.markdown("---")
        
        # 提供总计信息
        st.caption(f"共找到 {len(vocab_df) - len(st.session_state.deleted_vocab_ids)} 个词汇表")

def show_dimension_page():
    """显示维度设置页面"""
    st.header("维度设置")
    st.markdown("定义内容分析的主题维度和层级结构，构建个性化的内容筛选体系。")
    
    # 确保settings存在
    if 'settings' not in st.session_state:
        st.session_state.settings = session_state.get_default_settings()
    
    # 初始化维度编辑器
    initial_dimensions = None
    if st.session_state.settings.get('dimensions'):
        initial_dimensions = st.session_state.settings['dimensions']
    
    dimension_editor = DimensionEditor(initial_dimensions)
    
    # 模板管理区域
    st.subheader("模板管理")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 模板选择下拉框
        template_names = dimension_editor.get_template_names()
        selected_template = st.selectbox(
            "选择模板",
            options=template_names,
            index=0 if template_names else None,
            help="选择要应用的维度模板"
        )
    
    with col2:
        # 应用模板按钮
        if st.button("应用模板", type="primary"):
            if selected_template:
                template_data = st.session_state.templates[selected_template]
                dimension_editor.apply_template(template_data)
                # 更新会话状态
                dimensions_data = dimension_editor.render()
                st.session_state.settings['dimensions'] = dimensions_data['dimensions']
                st.session_state.settings['weights'] = dimensions_data['weights']
                st.session_state.settings['custom_dimensions'] = True
                st.success(f"已应用模板 '{selected_template}'")
                st.rerun()
    
    # 创建新模板区域
    with st.expander("创建新模板", expanded=False):
        st.markdown("""
        <style>
        .dimension-card {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #4CAF50;
        }
        .dimension-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .add-button {
            background-color: #f1f3f4; 
            padding: 5px 10px;
            border-radius: 4px;
            text-align: center;
            cursor: pointer;
            color: #333;
            border: 1px dashed #ccc;
            margin-top: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 模板名称输入
        st.markdown("### 步骤1: 输入模板名称")
        new_template_name = st.text_input("模板名称", key="template_name", 
                                         placeholder="请输入一个有意义的名称，例如：'产品营销维度'")
        
        # 初始化会话状态
        if 'template_dimensions' not in st.session_state:
            try:
                template_path = os.path.join('/Users/apple/Desktop/AI video/videoAnalysis_v1.0/data/dimensions', 'initial_key_dimensions.json')
                with open(template_path, 'r', encoding='utf-8') as f:
                    st.session_state.template_dimensions = json.load(f)
            except Exception as e:
                st.session_state.template_dimensions = {}
                st.error(f"加载参考模板时出错: {str(e)}")
        
        if 'template_structure' not in st.session_state:
            # 初始化模板结构
            st.session_state.template_structure = []
        
        # 一级维度区域
        st.markdown("### 步骤2: 添加一级维度")
        
        # 参考模板中的一级维度列表
        reference_dim1 = list(st.session_state.template_dimensions.keys())
        
        # 显示已添加的一级维度
        for i, dim_data in enumerate(st.session_state.template_structure):
            dim1_name = dim_data["dim1"]
            with st.container():
                st.markdown(f"""
                <div class="dimension-card">
                    <div class="dimension-title">一级维度: {dim1_name}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 二级维度列表
                st.markdown("二级维度:")
                col1, col2 = st.columns([3, 1])
                with col1:
                    # 显示当前二级维度列表
                    dim2_list = dim_data.get("dim2", [])
                    if dim2_list:
                        for dim2 in dim2_list:
                            st.markdown(f"- {dim2}")
                    else:
                        st.caption("暂无二级维度")
                
                # 添加二级维度
                with col2:
                    # 初始化清空标志
                    clear_key = f"clear_dim2_input_{i}"
                    if clear_key not in st.session_state:
                        st.session_state[clear_key] = False
                    
                    # 如果有清空标志，则重置输入框    
                    if st.session_state[clear_key]:
                        # 重置标志
                        st.session_state[clear_key] = False
                        custom_dim2 = st.text_input("添加二级维度", key=f"custom_dim2_{i}", value="", placeholder="输入自定义二级维度")
                    else:
                        custom_dim2 = st.text_input("添加二级维度", key=f"custom_dim2_{i}", placeholder="输入自定义二级维度")
                    
                    if st.button("添加", key=f"add_dim2_{i}"):
                        if custom_dim2 and custom_dim2 not in dim2_list:
                            dim2_list.append(custom_dim2)
                            # 设置清空标志，下次重新加载时会清空输入框
                            st.session_state[clear_key] = True
                            st.rerun()
                        elif custom_dim2 in dim2_list:
                            st.warning(f"维度 '{custom_dim2}' 已存在")
                        else:
                            st.warning("请输入维度名称")
                
                # 删除该一级维度的按钮
                if st.button("删除这个一级维度", key=f"del_dim1_{i}"):
                    st.session_state.template_structure.pop(i)
                    st.rerun()
        
        # 添加新的一级维度
        st.markdown("#### 添加新的一级维度")
        
        # 初始化添加模式状态
        if 'dim1_add_mode' not in st.session_state:
            st.session_state.dim1_add_mode = 'select'  # 默认为选择模式
        
        # 切换按钮行
        mode_col1, mode_col2 = st.columns([1, 3])
        with mode_col1:
            current_mode = st.session_state.dim1_add_mode
            if current_mode == 'select':
                if st.button("切换到自定义输入", key="switch_to_custom"):
                    st.session_state.dim1_add_mode = 'custom'
                    st.rerun()
            else:  # custom模式
                if st.button("返回选择模式", key="switch_to_select"):
                    st.session_state.dim1_add_mode = 'select'
                    st.rerun()
        
        # 根据当前模式显示不同的输入方式
        if st.session_state.dim1_add_mode == 'select':
            # 从参考模板中选择
            selected_dim1 = st.selectbox(
                "从参考模板选择一级维度", 
                [""] + reference_dim1,
                key="select_dim1"
            )
            
            if selected_dim1:
                if st.button("添加选定的一级维度"):
                    # 检查是否已存在
                    existing_dims = [item["dim1"] for item in st.session_state.template_structure]
                    if selected_dim1 not in existing_dims:
                        st.session_state.template_structure.append({
                            "dim1": selected_dim1,
                            "dim2": []
                        })
                        st.rerun()
                    else:
                        st.warning(f"维度 '{selected_dim1}' 已存在")
        else:  # custom模式
            # 添加自定义一级维度
            custom_dim1 = st.text_input("输入自定义一级维度", key="custom_dim1", placeholder="请输入新的维度名称")
            
            if custom_dim1:
                if st.button("添加自定义一级维度"):
                    # 检查是否已存在
                    existing_dims = [item["dim1"] for item in st.session_state.template_structure]
                    if custom_dim1 not in existing_dims:
                        st.session_state.template_structure.append({
                            "dim1": custom_dim1,
                            "dim2": []
                        })
                        st.rerun()
                    else:
                        st.warning(f"维度 '{custom_dim1}' 已存在")
        
        # 保存按钮
        st.markdown("### 步骤3: 保存模板")
        if st.button("保存模板", type="primary"):
            if not new_template_name:
                st.error("请输入模板名称")
            elif not st.session_state.template_structure:
                st.error("请至少添加一个一级维度")
            else:
                # 转换为模板格式
                template_data = {}
                for dim_data in st.session_state.template_structure:
                    dim1 = dim_data["dim1"]
                    dim2_list = dim_data.get("dim2", [])
                    
                    template_data[dim1] = {}
                    for dim2 in dim2_list:
                        template_data[dim1][dim2] = []
                
                # 保存模板
                dimension_editor.save_template(new_template_name, template_data)
                st.success(f"模板 '{new_template_name}' 保存成功！")
                
                # 清理会话状态
                st.session_state.template_structure = []
                time.sleep(1.5)
                st.rerun()
    
    # 渲染维度编辑器
    dimensions_data = dimension_editor.render()
    
    # 保存按钮
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("保存维度设置", type="primary"):
            st.session_state.settings['dimensions'] = dimensions_data['dimensions']
            st.session_state.settings['weights'] = dimensions_data['weights']
            st.session_state.settings['custom_dimensions'] = True
            st.success("维度设置已保存")
    
    # 自动应用奶粉产品模板（如果当前没有维度设置）
    if not st.session_state.settings.get('dimensions'):
        if '奶粉产品维度' in st.session_state.templates:
            template_data = st.session_state.templates['奶粉产品维度']
            dimension_editor.apply_template(template_data)
            dimensions_data = dimension_editor.render()
            st.session_state.settings['dimensions'] = dimensions_data['dimensions']
            st.session_state.settings['weights'] = dimensions_data['weights']
            st.session_state.settings['custom_dimensions'] = True
            st.rerun()

def show_analysis_page():
    """显示视频分析页面"""
    st.header("视频分析")
    st.markdown("处理视频，提取匹配指定维度的片段，自动生成宣传视频。")
    
    # 确保settings存在
    if 'settings' not in st.session_state:
        st.session_state.settings = session_state.get_default_settings()
    
    # 输入视频URL
    st.subheader("输入视频URL")
    
    # 将列表转换为文本
    default_urls = "\n".join(st.session_state.settings.get('urls', []))
    
    urls_text = st.text_area(
        "每行输入一个视频URL",
        value=default_urls,
        height=100,
        help="支持各种视频网站链接或直接的视频文件URL"
    )
    
    # 将文本转换回列表并保存
    if urls_text != default_urls:
        urls = [url.strip() for url in urls_text.split("\n") if url.strip()]
        st.session_state.settings['urls'] = urls
    
    # URL状态
    url_count = len(st.session_state.settings.get('urls', []))
    if url_count > 0:
        st.success(f"已添加 {url_count} 个视频URL")
    else:
        st.warning("请添加至少一个视频URL")
    
    # 分析设置
    st.subheader("分析设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 相似度阈值
        threshold = st.slider(
            "相似度阈值",
            0.5, 1.0, 
            value=st.session_state.settings.get('threshold', 0.7),
            step=0.05,
            help="较高的阈值将筛选出更相关的片段，但可能减少匹配数量"
        )
        st.session_state.settings['threshold'] = threshold
        
        # 匹配维度优先级
        priority = st.selectbox(
            "维度优先级",
            ["一级维度", "二级维度", "三级维度", "综合评分"],
            index=["一级维度", "二级维度", "三级维度", "综合评分"].index(
                st.session_state.settings.get('priority', '综合评分')
            ),
            help="选择在匹配过程中优先考虑的维度层级"
        )
        st.session_state.settings['priority'] = priority
    
    with col2:
        # 标语设置
        slogan = st.text_input(
            "视频片尾标语",
            value=st.session_state.settings.get('slogan', ''),
            help="将显示在视频末尾的文本"
        )
        st.session_state.settings['slogan'] = slogan
        
        # 片段数量限制
        max_clips = st.number_input(
            "最大片段数量",
            1, 20, 
            value=st.session_state.settings.get('max_clips', 5),
            help="最终视频中使用的最大片段数量"
        )
        st.session_state.settings['max_clips'] = max_clips
    
    # 处理按钮
    if st.button("开始分析", type="primary", disabled=url_count == 0):
        # 模拟处理逻辑（实际应用中需要连接到后端处理）
        with st.spinner("正在处理视频..."):
            try:
                # 在此处应该调用处理器进行实际处理
                # 暂时使用模拟数据
                sample_segments = []
                for i, url in enumerate(st.session_state.settings.get('urls', [])[:3]):
                    for j in range(2):  # 每个URL生成2个片段
                        sample_segments.append({
                            'start': float(i * 10 + j * 5),
                            'end': float(i * 10 + j * 5 + 3),
                            'text': f"示例文本内容 {i+1}-{j+1}，这是一个模拟的字幕片段，用于测试系统功能。",
                            'score': np.random.uniform(threshold, 1.0),
                            'source': url,
                            'clip_path': None  # 实际应用中应该有真实路径
                        })
                
                # 按分数排序
                sample_segments.sort(key=lambda x: x['score'], reverse=True)
                
                # 限制数量
                sample_segments = sample_segments[:max_clips]
                
                # 保存结果
                st.session_state.results = sample_segments
                session_state.save_results(sample_segments)
                
                st.success(f"分析完成！找到 {len(sample_segments)} 个匹配片段。")
                st.balloons()
                
            except Exception as e:
                st.error(f"处理失败: {str(e)}")
    
    # 如果有结果，显示预览
    if 'results' in st.session_state and st.session_state.results:
        st.subheader("分析结果预览")
        
        # 创建预览组件
        preview = VideoPreview()
        preview.render_preview(
            st.session_state.results,
            st.session_state.settings
        )
        
        # 跳转按钮
        if st.button("查看详细结果", key="goto_results"):
            st.rerun()

def show_results_page():
    """显示结果管理页面"""
    st.header("结果管理")
    st.markdown("查看和导出处理结果，管理生成的视频片段和分析数据。")
    
    # 检查是否有结果
    if 'results' not in st.session_state or not st.session_state.results:
        st.warning("尚未有分析结果，请先进行视频分析。")
        
        if st.button("前往视频分析"):
            st.session_state.current_page = "视频分析"
            st.rerun()
            
        return
    
    # 结果摘要
    st.subheader("结果摘要")
    
    results = st.session_state.results
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("匹配片段数", len(results))
    
    with col2:
        avg_score = np.mean([r.get('score', 0) for r in results])
        st.metric("平均匹配分数", f"{avg_score:.2f}")
    
    with col3:
        total_duration = sum([r.get('end', 0) - r.get('start', 0) for r in results])
        st.metric("总时长", f"{total_duration:.1f}秒")
    
    # 片段列表
    st.subheader("片段列表")
    
    # 准备表格数据
    table_data = []
    for i, seg in enumerate(results):
        table_data.append({
            "序号": i + 1,
            "时间段": f"{seg.get('start', 0):.1f}-{seg.get('end', 0):.1f}秒",
            "文本": seg.get('text', '')[:50] + ('...' if len(seg.get('text', '')) > 50 else ''),
            "分数": seg.get('score', 0),
            "来源": seg.get('source', '').split('/')[-1]  # 只显示URL的最后部分
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)
    
    # 详细预览
    st.subheader("详细预览")
    
    # 选择片段
    selected_idx = st.selectbox(
        "选择片段查看详情",
        range(len(results)),
        format_func=lambda i: f"片段 {i+1}: {results[i].get('text', '')[:30]}..."
    )
    
    if selected_idx is not None:
        seg = results[selected_idx]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"片段 {selected_idx+1}")
            st.write(f"**时间段**: {seg.get('start', 0):.1f}-{seg.get('end', 0):.1f}秒")
            st.write(f"**匹配分数**: {seg.get('score', 0):.2f}")
            st.write(f"**文本内容**:")
            st.info(seg.get('text', ''))
            
            # 显示视频预览（实际应用中应该有真实预览）
            st.write("**视频预览**:")
            
            # 创建预览组件
            preview = VideoPreview()
            preview_img = preview._generate_segment_preview(
                seg, 
                f"片段 {selected_idx+1}", 
                st.session_state.settings
            )
            
            if preview_img:
                st.image(preview_img, use_column_width=True)
        
        with col2:
            st.write("**来源**:")
            st.code(seg.get('source', ''))
            
            st.write("**维度匹配**:")
            
            # 假设的维度匹配数据（实际应用中应该有真实数据）
            dimension_match = {
                "一级维度": "品牌形象",
                "二级维度": ["产品特性", "用户需求"],
                "三级维度": ["功能", "体验", "场景"]
            }
            
            for level, dims in dimension_match.items():
                if isinstance(dims, list):
                    st.write(f"- {level}: {', '.join(dims)}")
                else:
                    st.write(f"- {level}: {dims}")
    
    # 导出结果
    st.subheader("导出结果")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 导出设置
        export_format = st.radio(
            "导出格式",
            ["CSV", "JSON"],
            horizontal=True
        )
        
        include_text = st.checkbox("包含文本内容", value=True)
    
    with col2:
        # 导出按钮
        if st.button("导出分析结果", type="primary"):
            # 准备导出数据
            export_data = []
            for seg in results:
                item = {
                    "start": seg.get('start', 0),
                    "end": seg.get('end', 0),
                    "score": seg.get('score', 0),
                    "source": seg.get('source', '')
                }
                
                if include_text:
                    item["text"] = seg.get('text', '')
                
                export_data.append(item)
            
            if export_format == "CSV":
                df_export = pd.DataFrame(export_data)
                csv = df_export.to_csv(index=False)
                st.download_button(
                    "下载CSV",
                    csv,
                    "analysis_results.csv",
                    "text/csv",
                    key="download_csv"
                )
            else:  # JSON
                json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                st.download_button(
                    "下载JSON",
                    json_str,
                    "analysis_results.json",
                    "application/json",
                    key="download_json"
                )

if __name__ == "__main__":
    main()
