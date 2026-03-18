# -*- coding: utf-8 -*-
"""
文档处理工具模块
支持读取 PDF、Word、TXT 等文档格式
"""
import os
import io
import hashlib
import json
from typing import List, Dict, Any, Optional

# 文档处理
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# 文本分割
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class DocumentLoader:
    """文档加载器基类"""
    
    @staticmethod
    def load_txt(file_content: bytes, encoding: str = 'utf-8') -> str:
        """加载TXT文本"""
        return file_content.decode(encoding)
    
    @staticmethod
    def load_pdf(file_content: bytes) -> str:
        """加载PDF文档"""
        if not PDF_AVAILABLE:
            raise ImportError("请安装 PyPDF2: pip install PyPDF2")
        
        text = ""
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    
    @staticmethod
    def load_docx(file_content: bytes) -> str:
        """加载Word文档"""
        if not DOCX_AVAILABLE:
            raise ImportError("请安装 python-docx: pip install python-docx")
        
        doc_file = io.BytesIO(file_content)
        doc = Document(doc_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        # 提取表格内容
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
        
        return text
    
    @classmethod
    def load_document(cls, file_content: bytes, file_type: str) -> str:
        """根据文件类型加载文档"""
        file_type = file_type.lower()
        
        if file_type in ['.txt', 'text']:
            return cls.load_txt(file_content)
        elif file_type in ['.pdf', 'pdf']:
            return cls.load_pdf(file_content)
        elif file_type in ['.docx', '.doc', 'word']:
            return cls.load_docx(file_content)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")


class TextSplitter:
    """文本分割器"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[str]:
        """分割文本为块"""
        if LANGCHAIN_AVAILABLE:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", "。", "！", "？", " ", ""]
            )
            return splitter.split_text(text)
        else:
            # 简单的备用分割方法
            return self._simple_split(text)
    
    def _simple_split(self, text: str) -> List[str]:
        """简单分割方法"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap
        
        return chunks


class DocumentProcessor:
    """文档处理器 - 完整流程"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.loader = DocumentLoader()
        self.splitter = TextSplitter(chunk_size, chunk_overlap)
    
    def process_document(self, file_content: bytes, file_type: str, 
                        file_name: str = "document") -> Dict[str, Any]:
        """
        处理文档的完整流程
        
        Returns:
            {
                "file_name": str,
                "file_type": str,
                "total_chars": int,
                "total_chunks": int,
                "chunks": [
                    {"index": 0, "content": "...", "char_count": 100},
                    ...
                ]
            }
        """
        # 1. 加载文档
        text = self.loader.load_document(file_content, file_type)
        total_chars = len(text)
        
        # 2. 分割文本
        chunks = self.splitter.split_text(text)
        
        # 3. 构建结果
        result_chunks = []
        for i, chunk in enumerate(chunks):
            result_chunks.append({
                "index": i,
                "content": chunk,
                "char_count": len(chunk)
            })
        
        # 4. 生成文档ID
        doc_id = self._generate_doc_id(file_name, text)
        
        return {
            "doc_id": doc_id,
            "file_name": file_name,
            "file_type": file_type,
            "total_chars": total_chars,
            "total_chunks": len(chunks),
            "chunks": result_chunks
        }
    
    def _generate_doc_id(self, file_name: str, content: str) -> str:
        """生成文档唯一ID"""
        unique_str = f"{file_name}_{len(content)}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]


class EmbeddingProcessor:
    """向量化处理器 - 需要配置嵌入模型"""
    
    def __init__(self, embedding_model: str = "nomic-embed-text"):
        self.embedding_model = embedding_model
        self.embeddings = None
        self._init_embeddings()
    
    def _init_embeddings(self):
        """初始化嵌入模型"""
        try:
            from langchain_ollama import OllamaEmbeddings
            self.embeddings = OllamaEmbeddings(model=self.embedding_model)
            print(f"[OK] 嵌入模型已加载: {self.embedding_model}")
        except ImportError:
            try:
                from langchain_openai import OpenAIEmbeddings
                # 使用OpenAI嵌入（需要API Key）
                self.embeddings = OpenAIEmbeddings()
                print("[OK] OpenAI嵌入模型已加载")
            except ImportError:
                print("[WARNING] 未找到嵌入模型，将使用关键词匹配作为后备")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """将文本转为向量"""
        if self.embeddings:
            return self.embeddings.embed_documents(texts)
        else:
            # 返回空向量作为后备
            return [[0.0] * 384 for _ in texts]
    
    def embed_query(self, query: str) -> List[float]:
        """将查询转为向量"""
        if self.embeddings:
            return self.embeddings.embed_query(query)
        else:
            return [0.0] * 384


class VectorStore:
    """简单的向量存储（基于内存）"""
    
    def __init__(self):
        self.documents = []  # 存储文档块
        self.embeddings = []  # 存储对应的向量
        self.metadata = []  # 存储元数据
    
    def add_documents(self, chunks: List[str], metadata: Dict[str, Any], 
                     embedding_processor: EmbeddingProcessor):
        """添加文档到向量存储"""
        # 生成向量
        vectors = embedding_processor.embed_texts(chunks)
        
        # 存储
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            self.documents.append(chunk)
            self.embeddings.append(vector)
            self.metadata.append({
                **metadata,
                "chunk_index": i
            })
    
    def similarity_search(self, query_vector: List[float], top_k: int = 3) -> List[Dict]:
        """相似度搜索（简单的余弦相似度）"""
        if not self.embeddings:
            return []
        
        # 计算相似度
        similarities = []
        for i, doc_vector in enumerate(self.embeddings):
            sim = self._cosine_similarity(query_vector, doc_vector)
            similarities.append((i, sim))
        
        # 排序并返回top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, sim in similarities[:top_k]:
            results.append({
                "content": self.documents[idx],
                "score": sim,
                "metadata": self.metadata[idx]
            })
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def save_to_file(self, filepath: str):
        """保存到文件"""
        data = {
            "documents": self.documents,
            "metadata": self.metadata
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.documents = data.get("documents", [])
            self.metadata = data.get("metadata", [])


# 测试代码
if __name__ == "__main__":
    # 测试文本分割
    test_text = """
    这是一个测试文档。它包含多个段落。
    
    这是第二个段落的内容。我们可以从中提取有用的信息。
    
    这是第三个段落，展示了文档处理的强大功能。
    """
    
    processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
    
    # 模拟文件处理
    result = processor.process_document(
        test_text.encode('utf-8'),
        '.txt',
        'test.txt'
    )
    
    print("文档处理结果:")
    print(f"总字符数: {result['total_chars']}")
    print(f"总块数: {result['total_chunks']}")
    print("\n文本块:")
    for chunk in result['chunks']:
        print(f"  块{chunk['index']}: {chunk['content'][:50]}...")
