# -*- coding: utf-8 -*-
"""
文档知识提取API服务
从PDF、Word、TXT等文档中提取知识并存储到Neo4j知识图谱
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime
import hashlib
import uuid

# 导入文档处理模块
from document_processor import DocumentProcessor, EmbeddingProcessor, VectorStore

# Neo4j
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("[WARNING] Neo4j驱动未安装")

app = Flask(__name__)
CORS(app, origins=['*'])

# ==================== 配置 ====================

# Neo4j配置
NEO4J_CONFIG = {
    'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    'username': os.getenv('NEO4J_USERNAME', 'neo4j'),
    'password': os.getenv('NEO4J_PASSWORD', 'root1234')
}

# 文档存储路径
DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), 'uploaded_docs')
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# 知识库存储路径
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), 'knowledge_base')
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

# ==================== Neo4j连接 ====================

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self._driver = None
        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            print(f"[OK] Neo4j连接成功: {uri}")
        except Exception as e:
            print(f"[ERROR] Neo4j连接失败: {e}")
    
    def close(self):
        if self._driver:
            self._driver.close()
    
    def run(self, query, parameters=None):
        with self._driver.session() as session:
            return session.run(query, parameters)
    
    def run_read(self, query, parameters=None):
        with self._driver.session() as session:
            return list(session.run(query, parameters))


# 初始化Neo4j
neo4j_conn = None
if NEO4J_AVAILABLE:
    try:
        neo4j_conn = Neo4jConnection(
            NEO4J_CONFIG['uri'],
            NEO4J_CONFIG['username'],
            NEO4J_CONFIG['password']
        )
        neo4j_conn.run_read("RETURN 1")
        print("[OK] Neo4j连接验证成功")
    except Exception as e:
        print(f"[WARNING] Neo4j连接失败: {e}")
        neo4j_conn = None

# 初始化处理器
doc_processor = DocumentProcessor(chunk_size=500, chunk_overlap=100)
embedding_processor = EmbeddingProcessor()
vector_store = VectorStore()

# ==================== 知识提取核心功能 ====================

def extract_keywords(text: str, top_k: int = 10) -> list:
    """简单的关键词提取（基于词频）"""
    # 常见停用词
    stopwords = {'的', '是', '在', '有', '和', '与', '了', '对', '为', '可以', 
                 '进行', '通过', '一个', '以及', '或者', '也', '等', '这', '那',
                 '能', '会', '将', '被', '要', '从', '到', '把', '用', '让', '给'}
    
    # 分词（简单处理）
    import re
    words = re.findall(r'[\u4e00-\u9fff]+', text)
    
    # 统计词频
    word_freq = {}
    for word in words:
        if len(word) >= 2 and word not in stopwords:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # 排序返回top_k
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0] for w in sorted_words[:top_k]]


def extract_sentences(text: str, max_sentences: int = 20) -> list:
    """提取重要句子"""
    import re
    # 按句号、感叹号、问号分割
    sentences = re.split(r'[。！？\n]', text)
    
    # 过滤短句
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    # 返回前N个句子
    return sentences[:max_sentences]


def extract_entities_to_kg(text: str, doc_name: str, category: str = "文档知识"):
    """从文本中提取实体并存储到Neo4j知识图谱"""
    if not neo4j_conn:
        return {"success": False, "message": "Neo4j未连接"}
    
    try:
        # 提取关键词
        keywords = extract_keywords(text, top_k=20)
        
        # 提取重要句子
        sentences = extract_sentences(text, max_sentences=30)
        
        # 创建文档节点
        doc_id = hashlib.md5(doc_name.encode()).hexdigest()[:16]
        cypher = """
        MERGE (d:Document {doc_id: $doc_id})
        SET d.name = $name,
            d.category = $category,
            d.content = $content,
            d.keywords = $keywords,
            d.updated_at = timestamp()
        """
        neo4j_conn.run(cypher, {
            "doc_id": doc_id,
            "name": doc_name,
            "category": category,
            "content": text[:5000],  # 限制内容长度
            "keywords": ",".join(keywords)
        })
        
        # 创建关键词节点并关联
        for keyword in keywords[:15]:
            kw_cypher = """
            MERGE (k:Keyword {name: $keyword})
            WITH k
            MATCH (d:Document {doc_id: $doc_id})
            MERGE (d)-[:HAS_KEYWORD]->(k)
            """
            neo4j_conn.run(kw_cypher, {"keyword": keyword, "doc_id": doc_id})
        
        # 存储文档块到向量库
        result = doc_processor.process_document(
            text.encode('utf-8'),
            '.txt',
            doc_name
        )
        
        chunks = [c['content'] for c in result['chunks']]
        vector_store.add_documents(
            chunks,
            {"doc_id": doc_id, "doc_name": doc_name},
            embedding_processor
        )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "doc_name": doc_name,
            "keywords_count": len(keywords),
            "sentences_count": len(sentences),
            "chunks_count": len(chunks),
            "keywords": keywords[:10]
        }
        
    except Exception as e:
        return {"success": False, "message": str(e)}


def search_knowledge(query: str, top_k: int = 5) -> list:
    """搜索知识库"""
    results = []
    
    # 1. Neo4j关键词搜索
    if neo4j_conn:
        try:
            cypher = """
            MATCH (d:Document)-[:HAS_KEYWORD]->(k:Keyword)
            WHERE toLower(k.name) CONTAINS toLower($query)
            RETURN d.name as doc_name, d.category as category, 
                   d.keywords as keywords, d.content as content
            LIMIT 5
            """
            kg_results = neo4j_conn.run_read(cypher, {"query": query})
            
            for record in kg_results:
                results.append({
                    "source": "knowledge_graph",
                    "doc_name": record['doc_name'],
                    "category": record['category'],
                    "content": record['content'][:300] if record['content'] else "",
                    "keywords": record['keywords']
                })
        except Exception as e:
            print(f"[ERROR] Neo4j搜索失败: {e}")
    
    # 2. 向量相似度搜索
    try:
        query_vector = embedding_processor.embed_query(query)
        vector_results = vector_store.similarity_search(query_vector, top_k=top_k)
        
        for r in vector_results:
            results.append({
                "source": "vector_store",
                "content": r['content'],
                "score": r['score'],
                "doc_name": r['metadata'].get('doc_name', 'unknown')
            })
    except Exception as e:
        print(f"[ERROR] 向量搜索失败: {e}")
    
    return results


# ==================== API接口 ====================

@app.route('/api/document/upload', methods=['POST'])
def upload_document():
    """上传并处理文档"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '请选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '文件名不能为空'}), 400
    
    # 获取文件类型
    file_ext = os.path.splitext(file.filename)[1].lower()
    category = request.form.get('category', '文档知识')
    
    # 支持的类型
    supported_types = ['.txt', '.pdf', '.docx']
    if file_ext not in supported_types:
        return jsonify({
            'success': False, 
            'error': f'不支持的文件类型: {file_ext}，支持: {supported_types}'
        }), 400
    
    try:
        # 读取文件内容
        file_content = file.read()
        
        # 处理文档
        result = doc_processor.process_document(file_content, file_ext, file.filename)
        
        # 提取知识到Neo4j
        full_text = " ".join([c['content'] for c in result['chunks']])
        kg_result = extract_entities_to_kg(full_text, file.filename, category)
        
        # 保存文件
        save_path = os.path.join(DOCUMENTS_DIR, file.filename)
        with open(save_path, 'wb') as f:
            f.write(file_content)
        
        return jsonify({
            'success': True,
            'data': {
                'file_name': file.filename,
                'file_type': file_ext,
                'total_chars': result['total_chars'],
                'total_chunks': result['total_chunks'],
                'knowledge_extracted': kg_result,
                'saved_path': save_path
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/document/process-text', methods=['POST'])
def process_text():
    """直接处理文本内容"""
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    doc_name = data.get('name', '文本知识')
    category = data.get('category', '文本知识')
    
    if not text:
        return jsonify({'success': False, 'error': '文本内容不能为空'}), 400
    
    try:
        # 处理文档
        result = doc_processor.process_document(
            text.encode('utf-8'), 
            '.txt', 
            doc_name
        )
        
        # 提取知识
        kg_result = extract_entities_to_kg(text, doc_name, category)
        
        # 提取关键词
        keywords = extract_keywords(text, top_k=20)
        
        # 提取摘要（取前3个句子）
        sentences = extract_sentences(text, max_sentences=3)
        summary = " ".join(sentences)
        
        return jsonify({
            'success': True,
            'data': {
                'doc_name': doc_name,
                'total_chars': result['total_chars'],
                'total_chunks': result['total_chunks'],
                'keywords': keywords[:10],
                'summary': summary,
                'knowledge_extracted': kg_result,
                'chunks': result['chunks'][:5]  # 返回前5个块作为预览
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/document/search', methods=['GET'])
def search():
    """搜索知识库"""
    query = request.args.get('q', '').strip()
    top_k = int(request.args.get('top_k', 5))
    
    if not query:
        return jsonify({'success': False, 'error': '搜索关键词不能为空'}), 400
    
    try:
        results = search_knowledge(query, top_k)
        
        return jsonify({
            'success': True,
            'query': query,
            'count': len(results),
            'data': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/document/list', methods=['GET'])
def list_documents():
    """列出所有已上传的文档"""
    if not neo4j_conn:
        return jsonify({'success': False, 'error': 'Neo4j未连接'}), 500
    
    try:
        cypher = """
        MATCH (d:Document)
        RETURN d.doc_id as doc_id, d.name as name, d.category as category,
               d.keywords as keywords, d.updated_at as updated_at
        ORDER BY d.updated_at DESC
        """
        results = neo4j_conn.run_read(cypher)
        
        documents = []
        for record in results:
            documents.append({
                'doc_id': record['doc_id'],
                'name': record['name'],
                'category': record['category'],
                'keywords': record['keywords'].split(',') if record['keywords'] else [],
                'updated_at': datetime.fromtimestamp(
                    record['updated_at'] / 1000
                ).strftime('%Y-%m-%d %H:%M') if record['updated_at'] else None
            })
        
        return jsonify({
            'success': True,
            'count': len(documents),
            'data': documents
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/document/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """获取文档详情"""
    if not neo4j_conn:
        return jsonify({'success': False, 'error': 'Neo4j未连接'}), 500
    
    try:
        cypher = """
        MATCH (d:Document {doc_id: $doc_id})
        RETURN d
        """
        results = neo4j_conn.run_read(cypher, {"doc_id": doc_id})
        
        if not results:
            return jsonify({'success': False, 'error': '文档不存在'}), 404
        
        record = results[0]['d']
        
        return jsonify({
            'success': True,
            'data': {
                'doc_id': record['doc_id'],
                'name': record['name'],
                'category': record['category'],
                'content': record.get('content', ''),
                'keywords': record.get('keywords', '').split(','),
                'updated_at': datetime.fromtimestamp(
                    record.get('updated_at', 0) / 1000
                ).strftime('%Y-%m-%d %H:%M') if record.get('updated_at') else None
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/document/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """删除文档"""
    if not neo4j_conn:
        return jsonify({'success': False, 'error': 'Neo4j未连接'}), 500
    
    try:
        cypher = """
        MATCH (d:Document {doc_id: $doc_id})
        DETACH DELETE d
        """
        neo4j_conn.run(cypher, {"doc_id": doc_id})
        
        return jsonify({
            'success': True,
            'message': '文档删除成功'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    neo4j_status = 'ok' if neo4j_conn else 'error'
    
    return jsonify({
        'status': 'ok',
        'service': 'document-knowledge-api',
        'neo4j': neo4j_status,
        'documents_count': len(vector_store.documents),
        'timestamp': datetime.now().isoformat()
    })


# ==================== 启动 ====================

if __name__ == '__main__':
    print("="*60)
    print("文档知识提取API服务")
    print("="*60)
    print("功能特点:")
    print("1. 支持PDF、Word、TXT文档上传")
    print("2. 自动提取关键词和摘要")
    print("3. 存储到Neo4j知识图谱")
    print("4. 向量相似度检索")
    print("="*60)
    print("端口: 5002")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5002, debug=False)
