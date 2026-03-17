"""
RAG知识库API服务
供后端部署使用
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import jieba
from collections import Counter
import re

app = Flask(__name__)
CORS(app, origins=['*'])

# 数据库配置 - 远程数据库
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root1234',
    'database': 'emotion_db',
    'charset': 'utf8mb4'
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

# ==================== RAG核心功能 ====================

# 同义词词典
SYNONYMS = {
    '焦虑': ['紧张', '不安', '担心', '压力大', '焦虑症'],
    '抑郁': ['低落', '沮丧', '忧郁', '绝望', '悲伤'],
    '失眠': ['睡眠不好', '难以入睡', '睡不着', '早醒'],
    '压力': ['紧张', '焦虑', '负担', '鸭梨'],
    '愤怒': ['生气', '发火', '暴躁', '不满'],
    '恐惧': ['害怕', '畏惧', '惊恐', '恐慌'],
    '孤独': ['寂寞', '独处', '无助', '孤单'],
    '迷茫': ['困惑', '彷徨', '无助', '不知所措'],
    '冥想': ['正念', '静心', '禅修', '放松'],
    '放松': ['解压', '舒缓', '减压', '休息'],
}

# 意图关键词
INTENT_KEYWORDS = {
    '缓解方法': ['怎么办', '如何缓解', '怎么缓解', '如何改善', '怎么调节', '怎么处理'],
    '原因分析': ['为什么', '原因', '为什么会', '怎么回事'],
    '了解': ['是什么', '什么是', '解释', '定义'],
    '预防': ['如何预防', '怎么预防', '避免', '防止'],
}

def expand_query(query):
    """扩展查询词"""
    words = jieba.lcut(query)
    expanded = set(words)
    for word in words:
        if word in SYNONYMS:
            expanded.update(SYNONYMS[word])
    return list(expanded)

def detect_intent(query):
    """检测意图"""
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in query:
                return intent
    return '咨询'

def calculate_similarity(query, title, content):
    """计算相似度"""
    query_words = set(expand_query(query))
    title_words = set(jieba.lcut(title))
    content_words = set(jieba.lcut(content[:500]))
    
    # 标题命中加分
    title_match = len(query_words & title_words)
    # 内容命中
    content_match = len(query_words & content_words)
    # 密度
    density = content_match / (len(content_words) + 1)
    
    score = title_match * 0.5 + content_match * 0.3 + density * 0.2
    return score

def generate_answer(query, matches):
    """生成回答"""
    if not matches:
        return "抱歉，我没有找到相关的知识。建议您换个问题或咨询专业心理医生。"
    
    top_match = matches[0]
    intent = detect_intent(query)
    
    # 温和的开头
    answers = {
        '缓解方法': f"关于「{query}」，我可以给您一些建议：\n\n",
        '原因分析': f"理解您的困惑，关于「{query}」的原因：\n\n",
        '了解': f"关于「{query}」，让我为您介绍：\n\n",
        '预防': f"对于「{query}」的预防，建议您：\n\n",
        '咨询': f"感谢您的提问，关于「{query}」：\n\n",
    }
    
    answer = answers.get(intent, f"关于「{query}」：\n\n")
    
    # 添加知识内容
    for i, m in enumerate(matches[:2]):
        answer += f"【{m['title']}】\n{m['content'][:200]}...\n\n"
    
    # 温暖结尾
    answer += "💡 小提示：如果您感到不适，建议及时寻求专业心理咨询师的帮助。您不是一个人，我们会陪伴您。"
    
    return answer

def search_knowledge(query, top_k=5):
    """搜索知识库"""
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT id, category, title, content, tags FROM knowledge_base WHERE is_active = 1")
    all_knowledge = cursor.fetchall()
    conn.close()
    
    if not all_knowledge:
        return []
    
    # 计算相似度
    results = []
    for item in all_knowledge:
        score = calculate_similarity(query, item['title'], item['content'])
        if score > 0:
            results.append({
                **item,
                'score': score
            })
    
    # 排序返回top_k
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]

# ==================== API接口 ====================

@app.route('/api/rag-knowledge/rag', methods=['POST'])
def rag_answer():
    """RAG问答接口"""
    data = request.get_json() or {}
    question = data.get('question', '')
    
    if not question:
        return jsonify({'success': False, 'error': '问题不能为空'}), 400
    
    # 搜索相关知识
    matches = search_knowledge(question)
    
    # 生成回答
    answer = generate_answer(question, matches)
    
    return jsonify({
        'success': True,
        'data': {
            'question': question,
            'answer': answer,
            'intent': detect_intent(question),
            'expanded_query': expand_query(question),
            'sources': [{'title': m['title'], 'score': round(m['score'], 4)} for m in matches[:3]]
        }
    })

@app.route('/api/rag-knowledge', methods=['GET'])
def search_knowledge_api():
    """搜索知识接口"""
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    sql = "SELECT * FROM knowledge_base WHERE is_active = 1"
    params = []
    
    if keyword:
        sql += " AND (title LIKE %s OR content LIKE %s OR tags LIKE %s)"
        kw = f'%{keyword}%'
        params.extend([kw, kw, kw])
    
    if category:
        sql += " AND category = %s"
        params.append(category)
    
    sql += " ORDER BY created_at DESC LIMIT 50"
    
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    
    return jsonify({'success': True, 'data': results})

@app.route('/api/rag-knowledge', methods=['POST'])
def create_knowledge():
    """添加知识"""
    data = request.get_json() or {}
    
    if not data.get('title') or not data.get('content'):
        return jsonify({'success': False, 'error': '标题和内容不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO knowledge_base (category, title, content, tags) VALUES (%s, %s, %s, %s)",
        (data.get('category', 'general'), data['title'], data['content'], data.get('tags', ''))
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '知识添加成功'})

@app.route('/api/rag-knowledge/<int:kid>', methods=['PUT'])
def update_knowledge(kid):
    """更新知识"""
    data = request.get_json() or {}
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE knowledge_base SET title = %s, content = %s, category = %s, tags = %s, updated_at = NOW() WHERE id = %s",
        (data.get('title'), data.get('content'), data.get('category'), data.get('tags'), kid)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/rag-knowledge/<int:kid>', methods=['DELETE'])
def delete_knowledge(kid):
    """删除知识"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE knowledge_base SET is_active = 0 WHERE id = %s", (kid,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/rag-knowledge/categories', methods=['GET'])
def get_categories():
    """获取知识分类"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM knowledge_base WHERE is_active = 1")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'data': categories})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("="*50)
    print("RAG知识库服务")
    print("端口: 5001")
    print("="*50)
    app.run(host='0.0.0.0', port=5001, debug=False)
