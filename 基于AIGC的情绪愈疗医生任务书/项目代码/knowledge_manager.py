"""
知识库管理工具 - CPU友好版本
支持：文本导入、书籍路径导入、文本分析（无需GPU）
"""

import os
import json
import re
from typing import List, Dict, Optional
from pathlib import Path
import requests
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from datetime import datetime

# 配置 - 低内存优化版本
# 使用更小的模型以适应2GB内存限制
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # 超轻量级模型（约80MB）
VECTOR_DB_PATH = './knowledge_vector_db'
TEXT_CHUNK_SIZE = 500
TEXT_CHUNK_OVERLAP = 100
MAX_DOCUMENTS_IN_MEMORY = 500  # 限制内存中保存的文档数量

# 阿里云百炼API配置（用于文本分析）
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'sk-cd1941be1ff64ce58eddb6e7bb69de71')
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


class TextAnalyzer:
    """文本分析器 - 使用LLM API分析文本"""

    def __init__(self, api_key: str = DASHSCOPE_API_KEY):
        self.api_key = api_key
        self.api_url = DASHSCOPE_API_URL

    def extract_entities(self, text: str) -> Dict:
        """从文本中提取实体"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""请从以下心理学文本中提取关键实体信息。

文本内容：
{text[:2000]}

请按JSON格式输出：
{{
    "emotions": ["情绪1", "情绪2"],
    "symptoms": ["症状1", "症状2"],
    "treatments": ["治疗方法1", "治疗方法2"],
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "summary": "文本摘要（不超过100字）"
}}

只输出JSON，不要其他内容。"""

            data = {
                "model": "qwen-plus",
                "messages": [
                    {"role": "system", "content": "你是文本分析专家，只输出JSON格式。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1500
            }

            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            return {'error': 'API调用失败'}

        except Exception as e:
            return {'error': str(e)}

    def analyze_text(self, text: str) -> Dict:
        """综合分析文本"""
        entities = self.extract_entities(text)

        if 'error' in entities:
            return entities

        # 添加时间戳
        entities['analyzed_at'] = datetime.now().isoformat()
        return entities


class VectorStore:
    """向量存储 - 使用CPU友好的SentenceTransformer"""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        print(f"[INFO] 正在加载嵌入模型: {model_name}...")
        print(f"[INFO] 使用低内存模式，适合2GB内存服务器")
        # 优化：限制CPU线程数
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'

        self.model = SentenceTransformer(model_name)
        print("[OK] 模型加载完成")

        self.documents = []
        self.embeddings = []
        self.metadata = []

    def add_text(self, text: str, metadata: Optional[Dict] = None) -> bool:
        """添加文本到向量库（带内存限制）"""
        try:
            # 检查内存使用情况
            if len(self.documents) >= MAX_DOCUMENTS_IN_MEMORY:
                print(f"[WARNING] 已达到最大文档数限制 ({MAX_DOCUMENTS_IN_MEMORY})")
                print("[INFO] 建议定期保存和清空向量库")
                return False

            # 生成向量
            embedding = self.model.encode([text], show_progress_bar=False)[0]

            self.documents.append(text)
            self.embeddings.append(embedding)
            self.metadata.append(metadata or {})

            return True
        except Exception as e:
            print(f"[ERROR] 添加文本失败: {e}")
            return False

    def add_text(self, text: str, metadata: Optional[Dict] = None) -> bool:
        """添加文本到向量库"""
        try:
            # 生成向量
            embedding = self.model.encode([text], show_progress_bar=False)[0]

            self.documents.append(text)
            self.embeddings.append(embedding)
            self.metadata.append(metadata or {})

            return True
        except Exception as e:
            print(f"[ERROR] 添加文本失败: {e}")
            return False

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """搜索相似文档"""
        if not self.embeddings:
            return []

        try:
            # 查询向量
            query_embedding = self.model.encode([query], show_progress_bar=False)[0]

            # 计算相似度
            similarities = cosine_similarity(
                [query_embedding],
                self.embeddings
            )[0]

            # 获取top-k结果
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            results = []
            for idx in top_indices:
                results.append({
                    'text': self.documents[idx],
                    'score': float(similarities[idx]),
                    'metadata': self.metadata[idx]
                })

            return results

        except Exception as e:
            print(f"[ERROR] 搜索失败: {e}")
            return []

    def save(self, path: str = VECTOR_DB_PATH):
        """保存向量库"""
        os.makedirs(path, exist_ok=True)

        data = {
            'documents': self.documents,
            'embeddings': self.embeddings,
            'metadata': self.metadata,
            'model_name': EMBEDDING_MODEL
        }

        with open(os.path.join(path, 'vector_db.pkl'), 'wb') as f:
            pickle.dump(data, f)

        print(f"[OK] 向量库已保存到 {path}")

    def load(self, path: str = VECTOR_DB_PATH):
        """加载向量库"""
        file_path = os.path.join(path, 'vector_db.pkl')

        if not os.path.exists(file_path):
            print("[WARNING] 向量库文件不存在")
            return False

        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)

            self.documents = data['documents']
            self.embeddings = data['embeddings']
            self.metadata = data['metadata']

            print(f"[OK] 向量库已加载，共 {len(self.documents)} 条文档")
            return True

        except Exception as e:
            print(f"[ERROR] 加载向量库失败: {e}")
            return False


class TextProcessor:
    """文本处理器 - 分块和预处理"""

    @staticmethod
    def split_text(text: str, chunk_size: int = TEXT_CHUNK_SIZE,
                  overlap: int = TEXT_CHUNK_OVERLAP) -> List[str]:
        """将文本分割成块"""
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size

            if end > text_len:
                end = text_len

            chunk = text[start:end]

            # 如果不是最后一块，尝试在句号、换行符等位置断开
            if end < text_len:
                # 优先在句号处断开
                last_period = chunk.rfind('。')
                last_newline = chunk.rfind('\n')
                break_pos = max(last_period, last_newline)

                if break_pos > chunk_size // 2:  # 确保不会截断太多
                    chunk = chunk[:break_pos + 1]
                    end = start + break_pos + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """从文件中提取文本"""
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif file_ext == '.pdf':
                # 需要安装: pip install pypdf
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text

            elif file_ext in ['.doc', '.docx']:
                # 需要安装: pip install python-docx
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text

            elif file_ext in ['.md', '.markdown']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            else:
                return f"[ERROR] 不支持的文件类型: {file_ext}"

        except Exception as e:
            return f"[ERROR] 文件读取失败: {str(e)}"


class KnowledgeManager:
    """知识库管理器"""

    def __init__(self):
        self.vector_store = VectorStore()
        self.text_analyzer = TextAnalyzer()
        self.text_processor = TextProcessor()
        self.import_history = []

    def import_text(self, text: str, title: str = '',
                   source: str = '', analyze: bool = True) -> Dict:
        """导入文本到知识库"""
        try:
            if not text.strip():
                return {'success': False, 'error': '文本内容不能为空'}

            # 文本分块
            chunks = self.text_processor.split_text(text)

            # 文本分析
            analysis_result = None
            if analyze:
                analysis_result = self.text_analyzer.analyze_text(text)

                if 'error' in analysis_result:
                    return {
                        'success': False,
                        'error': f'文本分析失败: {analysis_result["error"]}'
                    }

            # 添加到向量库
            added_count = 0
            for i, chunk in enumerate(chunks):
                metadata = {
                    'title': title,
                    'source': source,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'analyzed': analyze
                }

                if analysis_result:
                    metadata['analysis'] = analysis_result

                if self.vector_store.add_text(chunk, metadata):
                    added_count += 1

            # 保存向量库
            self.vector_store.save()

            # 记录历史
            history_item = {
                'title': title or '未命名',
                'source': source,
                'chunk_count': len(chunks),
                'analyzed': analyze,
                'imported_at': datetime.now().isoformat()
            }
            self.import_history.append(history_item)

            return {
                'success': True,
                'message': f'成功导入 {len(chunks)} 个文本块',
                'data': {
                    'chunks': len(chunks),
                    'analyzed': analyze,
                    'analysis': analysis_result
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def import_file(self, file_path: str, title: str = '',
                    analyze: bool = True) -> Dict:
        """从文件导入"""
        if not os.path.exists(file_path):
            return {'success': False, 'error': '文件不存在'}

        # 提取文本
        text = self.text_processor.extract_text_from_file(file_path)

        if text.startswith('[ERROR]'):
            return {'success': False, 'error': text}

        # 设置标题
        if not title:
            title = os.path.basename(file_path)

        # 设置来源
        source = file_path

        # 导入
        return self.import_text(text, title=title, source=source, analyze=analyze)

    def import_directory(self, dir_path: str, analyze: bool = True) -> Dict:
        """批量导入目录中的所有文本文件"""
        if not os.path.exists(dir_path):
            return {'success': False, 'error': '目录不存在'}

        success_count = 0
        fail_count = 0
        errors = []

        # 支持的文件扩展名
        supported_exts = ['.txt', '.pdf', '.doc', '.docx', '.md', '.markdown']

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)

                # 检查文件类型
                if Path(file_path).suffix.lower() not in supported_exts:
                    continue

                # 导入文件
                result = self.import_file(file_path, analyze=analyze)

                if result['success']:
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"{file}: {result['error']}")

        return {
            'success': True,
            'message': f'批量导入完成：成功 {success_count} 个，失败 {fail_count} 个',
            'data': {
                'success_count': success_count,
                'fail_count': fail_count,
                'errors': errors
            }
        }

    def search_knowledge(self, query: str, top_k: int = 3) -> Dict:
        """搜索知识"""
        try:
            results = self.vector_store.search(query, top_k=top_k)

            return {
                'success': True,
                'data': {
                    'query': query,
                    'results': results,
                    'count': len(results)
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'success': True,
            'data': {
                'total_documents': len(self.vector_store.documents),
                'total_imports': len(self.import_history),
                'last_import': self.import_history[-1] if self.import_history else None
            }
        }

    def load_vector_db(self, path: str = VECTOR_DB_PATH) -> bool:
        """加载向量库"""
        return self.vector_store.load(path)


# ==================== 命令行接口 ====================

if __name__ == '__main__':
    import sys

    manager = KnowledgeManager()

    # 尝试加载已有向量库
    manager.load_vector_db()

    if len(sys.argv) < 2:
        print("""
知识库管理工具 - CPU友好版本

使用方法:
  python knowledge_manager.py import_text "文本内容" "标题"
  python knowledge_manager.py import_file 文件路径
  python knowledge_manager.py import_dir 目录路径
  python knowledge_manager.py search "查询关键词"
  python knowledge_manager.py stats

示例:
  python knowledge_manager.py import_text "焦虑症是一种常见的精神障碍..." "焦虑症介绍"
  python knowledge_manager.py import_file ./data/book.pdf
  python knowledge_manager.py import_dir ./data/books
  python knowledge_manager.py search "焦虑症状"
  python knowledge_manager.py stats
        """)
        sys.exit(0)

    command = sys.argv[1]

    if command == 'import_text':
        if len(sys.argv) < 4:
            print("用法: python knowledge_manager.py import_text '文本' '标题'")
            sys.exit(1)

        text = sys.argv[2]
        title = sys.argv[3]
        result = manager.import_text(text, title=title)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'import_file':
        if len(sys.argv) < 3:
            print("用法: python knowledge_manager.py import_file 文件路径")
            sys.exit(1)

        file_path = sys.argv[2]
        result = manager.import_file(file_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'import_dir':
        if len(sys.argv) < 3:
            print("用法: python knowledge_manager.py import_dir 目录路径")
            sys.exit(1)

        dir_path = sys.argv[2]
        result = manager.import_directory(dir_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'search':
        if len(sys.argv) < 3:
            print("用法: python knowledge_manager.py search '查询关键词'")
            sys.exit(1)

        query = sys.argv[2]
        result = manager.search_knowledge(query)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == 'stats':
        result = manager.get_stats()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        print(f"未知命令: {command}")
        sys.exit(1)
