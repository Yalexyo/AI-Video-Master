import os
import json
import requests
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HotWord:
    """热词类：表示一个热词及其权重"""
    word: str
    weight: float = 4.0
    category: str = "默认"

class WordlistManager:
    """热词管理类：管理热词库的创建、查询和删除"""
    
    def __init__(self, config: Dict):
        """初始化热词管理器"""
        self.config = config
        self.api_key = config.get('DASHSCOPE_API_KEY', os.environ.get('DASHSCOPE_API_KEY', ''))
        self.api_base = "https://dashscope.aliyuncs.com/api/v1"
        self.wordlist_path = os.path.join(config.get('INPUT_DIR', 'data/input'), 'wordlists')
        os.makedirs(self.wordlist_path, exist_ok=True)
        
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """发送API请求"""
        if not self.api_key:
            raise ValueError("DashScope API密钥未设置")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_base}/{endpoint}"
        
        try:
            if method.lower() == 'get':
                response = requests.get(url, headers=headers, params=data or {})
            elif method.lower() == 'post':
                response = requests.post(url, headers=headers, json=data or {})
            elif method.lower() == 'delete':
                response = requests.delete(url, headers=headers, params=data or {})
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            raise
            
    def create_wordlist(self, name: str, words: List[HotWord], model: str = "asr") -> Optional[str]:
        """创建热词库"""
        # 转换热词列表为API格式
        hot_words = []
        for hw in words:
            hot_words.append({
                "text": hw.word,
                "weight": hw.weight
            })
            
        data = {
            "model": model,
            "name": name,
            "hot_words": hot_words
        }
        
        try:
            result = self._make_request('post', 'asr/vocabulary/generic', data)
            vocabulary_id = result.get('vocabulary_id')
            
            # 保存到本地
            if vocabulary_id:
                self._save_local_wordlist(vocabulary_id, name, words)
                logger.info(f"成功创建热词库: {name} (ID: {vocabulary_id})")
                
            return vocabulary_id
            
        except Exception as e:
            logger.error(f"创建热词库失败: {str(e)}")
            return None
            
    def list_wordlists(self) -> List[Dict]:
        """列出所有热词库"""
        try:
            result = self._make_request('get', 'asr/vocabulary/generic')
            return result.get('vocabularies', [])
            
        except Exception as e:
            logger.error(f"获取热词库列表失败: {str(e)}")
            return []
            
    def get_wordlist(self, vocabulary_id: str) -> Optional[Dict]:
        """获取热词库详情"""
        try:
            result = self._make_request('get', f'asr/vocabulary/generic/{vocabulary_id}')
            return result
            
        except Exception as e:
            logger.error(f"获取热词库详情失败 (ID: {vocabulary_id}): {str(e)}")
            return None
            
    def delete_wordlist(self, vocabulary_id: str) -> bool:
        """删除热词库"""
        try:
            self._make_request('delete', f'asr/vocabulary/generic/{vocabulary_id}')
            
            # 删除本地存储
            self._delete_local_wordlist(vocabulary_id)
            logger.info(f"成功删除热词库 (ID: {vocabulary_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"删除热词库失败 (ID: {vocabulary_id}): {str(e)}")
            return False
            
    def _save_local_wordlist(self, vocabulary_id: str, name: str, words: List[HotWord]) -> None:
        """保存热词库到本地文件"""
        # 保存词汇列表
        words_data = []
        for hw in words:
            words_data.append({
                "word": hw.word,
                "weight": hw.weight,
                "category": hw.category
            })
            
        wordlist_data = {
            "vocabulary_id": vocabulary_id,
            "name": name,
            "words": words_data,
            "created_at": os.path.getmtime(self.wordlist_path) if os.path.exists(self.wordlist_path) else None
        }
        
        # 本地保存逻辑已移除，仅通过阿里云API创建热词库
        pass
            
        # 更新ID映射文件
        id_mapping_file = os.path.join(self.wordlist_path, "saved_vocabulary_ids.json")
        id_mapping = {}
        
        if os.path.exists(id_mapping_file):
            try:
                with open(id_mapping_file, 'r', encoding='utf-8') as f:
                    id_mapping = json.load(f)
            except:
                pass
                
        id_mapping[name] = vocabulary_id
        
        with open(id_mapping_file, 'w', encoding='utf-8') as f:
            json.dump(id_mapping, f, ensure_ascii=False, indent=2)
            
    def _delete_local_wordlist(self, vocabulary_id: str) -> None:
        """从本地文件删除热词库"""
        file_path = os.path.join(self.wordlist_path, f"{vocabulary_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # 更新ID映射文件
        id_mapping_file = os.path.join(self.wordlist_path, "saved_vocabulary_ids.json")
        if os.path.exists(id_mapping_file):
            try:
                with open(id_mapping_file, 'r', encoding='utf-8') as f:
                    id_mapping = json.load(f)
                    
                # 找到并删除对应的键值对
                for name, vid in list(id_mapping.items()):
                    if vid == vocabulary_id:
                        del id_mapping[name]
                        break
                        
                with open(id_mapping_file, 'w', encoding='utf-8') as f:
                    json.dump(id_mapping, f, ensure_ascii=False, indent=2)
                    
            except Exception as e:
                logger.error(f"更新ID映射文件失败: {str(e)}")
                
    def load_local_wordlists(self) -> Dict[str, Dict]:
        """加载本地保存的热词库"""
        wordlists = {}
        
        if not os.path.exists(self.wordlist_path):
            return wordlists
            
        for filename in os.listdir(self.wordlist_path):
            if filename.endswith('.json') and filename != "saved_vocabulary_ids.json":
                try:
                    # 本地读取逻辑已移除，所有热词库通过阿里云API获取
                    continue
                except Exception as e:
                    logger.error(f"加载热词库文件失败 ({filename}): {str(e)}")
                    
        return wordlists
        
    def convert_to_hotwords(self, words_data: List[Dict]) -> List[HotWord]:
        """将原始数据转换为HotWord对象列表"""
        result = []
        for wd in words_data:
            result.append(HotWord(
                word=wd.get('word', ''),
                weight=float(wd.get('weight', 1.0)),
                category=wd.get('category', '默认')
            ))
        return result
