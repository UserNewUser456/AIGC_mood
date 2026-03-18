"""
智能心理知识库RAG服务
结合知识库检索 + AI大模型生成专业、温暖的回答
"""
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import pymysql
import jieba
import requests
import json
import re
from collections import Counter
from datetime import datetime
import os

app = Flask(__name__)
CORS(app, origins=['*'])

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root1234',
    'database': 'emotion_db',
    'charset': 'utf8mb4'
}

# 阿里云百炼API配置
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'sk-cd1941be1ff64ce58eddb6e7bb69de71')
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

def get_db():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

# ==================== 情绪检测与安抚 ====================

# 情绪关键词词典
EMOTION_KEYWORDS = {
    '焦虑': {
        'keywords': ['焦虑', '紧张', '不安', '担心', '压力大', '心慌', '坐立不安', '烦躁'],
        'comfort': [
            "我理解你现在的焦虑感，这种感觉确实让人不舒服。",
            "焦虑是一种正常的情绪反应，很多人都会经历。",
            "让我们一起来看看如何应对这种焦虑感。"
        ]
    },
    '抑郁': {
        'keywords': ['抑郁', '低落', '沮丧', '忧郁', '绝望', '悲伤', '难过', '空虚', '无助', '活着没意思'],
        'comfort': [
            "听到你有这样的感受，我真的很心疼。",
            "你愿意分享这些，已经是迈出了一大步。",
            "无论现在多么艰难，请记住你并不孤单。"
        ]
    },
    '愤怒': {
        'keywords': ['愤怒', '生气', '发火', '暴躁', '愤怒', '怨恨', '不满', '讨厌'],
        'comfort': [
            "我能感受到你现在的愤怒，这种情绪需要被理解和释放。",
            "愤怒背后往往藏着受伤，让我们一起看看是什么让你如此难受。",
            "你有权利感到愤怒，这是你的真实感受。"
        ]
    },
    '恐惧': {
        'keywords': ['恐惧', '害怕', '畏惧', '惊恐', '恐慌', '担心', '不敢'],
        'comfort': [
            "感到害怕是很正常的，这是身体在保护你。",
            "恐惧虽然强烈，但它不会永远持续。",
            "让我们一起找到让你感到安全的方法。"
        ]
    },
    '孤独': {
        'keywords': ['孤独', '寂寞', '独处', '没人理解', '孤单', '被抛弃'],
        'comfort': [
            "孤独的感觉确实很难受，我理解这种滋味。",
            "即使在人群中，我们也可能感到孤独，这是正常的。",
            "我在这里陪伴你，你不是一个人。"
        ]
    },
    '迷茫': {
        'keywords': ['迷茫', '困惑', '彷徨', '不知所措', '没有方向', '不知道怎么办'],
        'comfort': [
            "迷茫期是很多人都会经历的，这说明你在思考人生的意义。",
            "不用急着找到所有答案，给自己一些时间。",
            "迷茫也是成长的一部分，它会带你走向更清晰的未来。"
        ]
    }
}

# 严重风险词
RISK_KEYWORDS = ['自杀', '自残', '结束生命', '不想活', '死了算了', '活不下去', '解脱', '结束一切']

def detect_emotion(text):
    """
    检测用户情绪状态
    返回: {
        'primary_emotion': 主要情绪,
        'risk_level': 风险等级(low/medium/high/critical),
        'comfort_message': 安抚语句,
        'detected_keywords': 检测到的关键词
    }
    """
    text_lower = text.lower()
    detected_emotions = []
    detected_keywords = []
    
    # 检测严重风险
    for keyword in RISK_KEYWORDS:
        if keyword in text_lower:
            return {
                'primary_emotion': '危机',
                'risk_level': 'critical',
                'comfort_message': """我注意到你可能正在经历非常困难的时刻。\n\n""",
                'detected_keywords': [keyword],
                'is_crisis': True
            }
    
    # 检测各类情绪
    for emotion, data in EMOTION_KEYWORDS.items():
        for keyword in data['keywords']:
            if keyword in text:
                detected_emotions.append(emotion)
                detected_keywords.append(keyword)
                break
    
    # 确定主要情绪
    if detected_emotions:
        emotion_counts = Counter(detected_emotions)
        primary_emotion = emotion_counts.most_common(1)[0][0]
        
        # 随机选择一条安抚语
        import random
        comfort = random.choice(EMOTION_KEYWORDS[primary_emotion]['comfort'])
        
        # 判断风险等级
        if primary_emotion in ['抑郁'] and len(detected_keywords) > 2:
            risk_level = 'high'
        elif primary_emotion in ['焦虑', '愤怒']:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'primary_emotion': primary_emotion,
            'risk_level': risk_level,
            'comfort_message': comfort,
            'detected_keywords': list(set(detected_keywords)),
            'is_crisis': False
        }
    
    # 默认中性
    return {
        'primary_emotion': '中性',
        'risk_level': 'low',
        'comfort_message': "感谢你愿意和我分享。",
        'detected_keywords': [],
        'is_crisis': False
    }

# ==================== RAG检索功能 ====================

def expand_query(query):
    """扩展查询词，增加同义词"""
    # 心理领域同义词
    synonyms = {
        '焦虑': ['紧张', '不安', '担心', '心慌', '坐立不安'],
        '抑郁': ['低落', '沮丧', '忧郁', '情绪不好', '不开心'],
        '失眠': ['睡不着', '睡眠不好', '难以入睡', '早醒'],
        '压力': ['紧张', '焦虑', '负担', '不堪重负'],
        '情绪': ['心情', '感受', '情感', '心态'],
        '放松': ['减压', '舒缓', '休息', '平静', '镇静'],
    }
    
    words = list(jieba.cut(query))
    expanded = set(words)
    
    for word in words:
        if word in synonyms:
            expanded.update(synonyms[word])
    
    return list(expanded)

def search_knowledge(query, top_k=3):
    """
    从知识库中检索相关内容
    使用改进的相似度算法
    """
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 获取所有有效知识
        cursor.execute("""
            SELECT id, category, title, content, tags, source 
            FROM knowledge_base 
            WHERE is_active = 1
        """)
        all_knowledge = cursor.fetchall()
        
        if not all_knowledge:
            return []
        
        # 扩展查询词
        query_words = set(expand_query(query))
        
        # 计算相似度
        results = []
        for item in all_knowledge:
            # 分词
            title_words = set(jieba.cut(item['title']))
            content_words = set(jieba.cut(item['content'][:500]))
            tags_words = set(jieba.cut(item.get('tags', '')))
            
            # 计算各种匹配分数
            title_match = len(query_words & title_words) * 3.0  # 标题匹配权重高
            content_match = len(query_words & content_words) * 1.0
            tags_match = len(query_words & tags_words) * 2.0
            
            # 完全匹配加分
            if any(word in item['title'] for word in query_words):
                title_match += 2.0
            
            score = title_match + content_match + tags_match
            
            if score > 0:
                results.append({
                    **item,
                    'score': score,
                    'matched_words': list(query_words & (title_words | content_words | tags_words))
                })
        
        # 排序并返回top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
        
    finally:
        conn.close()

# ==================== AI大模型回答生成 ====================

def call_llm(messages, stream=False, temperature=0.7):
    """
    调用阿里云百炼大模型API
    """
    try:
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen-plus",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 800,
            "stream": stream
        }
        
        response = requests.post(
            DASHSCOPE_API_URL,
            headers=headers,
            json=data,
            timeout=30,
            stream=stream
        )
        
        if response.status_code == 200:
            if stream:
                return response
            else:
                result = response.json()
                return result['choices'][0]['message']['content']
        else:
            print(f"LLM API错误: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"调用LLM异常: {e}")
        return None

def generate_ai_response(question, context, emotion_info):
    """
    使用AI大模型生成专业、温暖的回答
    """
    # 构建系统提示
    system_prompt = """你是一位专业的心理咨询师，拥有丰富的心理学知识和咨询经验。

你的特点：
1. 专业：基于心理学理论和实证研究给出建议
2. 温暖：用关怀、理解的语言与用户交流
3. 安全：对于严重心理问题，建议寻求专业帮助
4. 实用：提供具体可行的方法和技巧

请根据提供的知识库内容，结合你的专业知识，给出专业、温暖、有帮助的回答。
回答结构：
1. 先表达理解和共情
2. 提供专业的心理学解释或建议
3. 给出具体可行的方法
4. 温暖的鼓励"""

    # 构建上下文
    context_text = ""
    if context:
        context_text = "\n\n相关心理学知识：\n"
        for i, item in enumerate(context, 1):
            context_text += f"{i}. 【{item['title']}】{item['content'][:300]}...\n"
    
    # 情绪安抚语
    comfort = emotion_info.get('comfort_message', '')
    
    # 危机情况特殊处理
    if emotion_info.get('is_crisis'):
        messages = [
            {"role": "system", "content": "你是一位危机干预专家。用户表达了自杀或自伤的想法，请立即提供危机干预信息，强烈建议寻求专业帮助。"},
            {"role": "user", "content": f"用户说：{question}\n\n请立即进行危机干预。"}
        ]
        
        ai_response = call_llm(messages)
        if ai_response:
            return ai_response + "\n\n🆘 **紧急求助资源**：\n- 全国24小时心理危机干预热线：400-161-9995\n- 北京心理危机研究与干预中心：010-82951332\n- 生命热线：400-821-1215"
        return "我注意到你可能正在经历非常艰难的时刻。请立即联系专业心理咨询师或拨打心理危机干预热线：400-161-9995。你的生命很珍贵，有人愿意帮助你。"
    
    # 正常情况
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"用户情绪状态：{emotion_info['primary_emotion']}\n用户问题：{question}\n{context_text}\n\n请给出专业、温暖的回答。先说一句共情的话，然后提供专业建议。"}
    ]
    
    ai_response = call_llm(messages)
    
    if ai_response:
        # 组合最终回答
        full_response = f"{comfort}\n\n{ai_response}"
        return full_response
    
    # AI调用失败，使用模板回答
    return generate_fallback_response(question, context, emotion_info)

def generate_fallback_response(question, context, emotion_info):
    """
    AI调用失败时的后备回答
    """
    comfort = emotion_info.get('comfort_message', '感谢你的分享。')
    
    response = comfort + "\n\n"
    
    if context:
        response += "根据心理学知识，我为你整理了一些信息：\n\n"
        for item in context[:2]:
            response += f"📖 **{item['title']}**\n{item['content'][:200]}...\n\n"
    else:
        response += "虽然我没有找到特定的知识，但请记住：\n"
        response += "1. 你的感受是真实的，值得被尊重\n"
        response += "2. 情绪会过去，困难也会过去\n"
        response += "3. 寻求支持是勇敢的表现\n\n"
    
    response += "💝 如果你感到困扰，建议寻求专业心理咨询师的帮助。"
    
    return response

def generate_stream_response(question, context, emotion_info):
    """
    流式生成回答
    """
    system_prompt = """你是一位专业的心理咨询师，回答要专业、温暖、有帮助。"""
    
    context_text = ""
    if context:
        context_text = "\n参考知识：" + " | ".join([item['title'] for item in context[:2]])
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"用户问题：{question}{context_text}\n请先共情，再给建议，控制在300字内。"}
    ]
    
    return call_llm(messages, stream=True)

# ==================== API接口 ====================

@app.route('/api/rag-knowledge/chat', methods=['POST'])
def chat():
    """
    智能对话接口
    结合情绪检测 + 知识检索 + AI生成回答
    """
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    user_id = data.get('user_id')
    stream = data.get('stream', False)
    
    if not question:
        return jsonify({'success': False, 'error': '问题不能为空'}), 400
    
    # 1. 检测情绪
    emotion_info = detect_emotion(question)
    
    # 2. 检索知识库
    knowledge_matches = search_knowledge(question, top_k=3)
    
    # 3. 生成回答
    if stream:
        # 流式响应
        def generate():
            # 先发送情绪信息
            yield f"data: {json.dumps({'emotion': emotion_info, 'type': 'emotion'})}\n\n"
            
            # 再流式发送AI回答
            ai_response = generate_stream_response(question, knowledge_matches, emotion_info)
            if ai_response:
                full_content = ""
                for chunk in ai_response.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        lines = chunk.split('\n')
                        for line in lines:
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str.strip() and data_str != '[DONE]':
                                    try:
                                        delta = json.loads(data_str)
                                        content = delta.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                        if content:
                                            full_content += content
                                            yield f"data: {json.dumps({'content': content, 'type': 'content'})}\n\n"
                                    except:
                                        pass
                
                # 保存对话记录（如果需要）
                yield f"data: {json.dumps({'done': True, 'full_content': full_content, 'type': 'done'})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream; charset=utf-8',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )
    else:
        # 普通响应
        answer = generate_ai_response(question, knowledge_matches, emotion_info)
        
        return jsonify({
            'success': True,
            'data': {
                'question': question,
                'answer': answer,
                'emotion': emotion_info['primary_emotion'],
                'risk_level': emotion_info['risk_level'],
                'sources': [
                    {
                        'id': m['id'],
                        'title': m['title'],
                        'category': m['category'],
                        'score': round(m['score'], 4)
                    } for m in knowledge_matches
                ]
            }
        })

@app.route('/api/rag-knowledge', methods=['GET'])
def search_knowledge_api():
    """搜索知识接口"""
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 构建查询
        sql = "SELECT * FROM knowledge_base WHERE is_active = 1"
        count_sql = "SELECT COUNT(*) as total FROM knowledge_base WHERE is_active = 1"
        params = []
        
        if keyword:
            sql += " AND (title LIKE %s OR content LIKE %s OR tags LIKE %s)"
            count_sql += " AND (title LIKE %s OR content LIKE %s OR tags LIKE %s)"
            kw = f'%{keyword}%'
            params.extend([kw, kw, kw])
        
        if category:
            sql += " AND category = %s"
            count_sql += " AND category = %s"
            params.append(category)
        
        # 获取总数
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 获取分页数据
        sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': {
                'list': results,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    finally:
        conn.close()

@app.route('/api/rag-knowledge/<int:kid>', methods=['GET'])
def get_knowledge_detail(kid):
    """获取知识详情"""
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute(
            "SELECT * FROM knowledge_base WHERE id = %s AND is_active = 1",
            (kid,)
        )
        result = cursor.fetchone()
        
        if result:
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': False, 'error': '知识不存在'}), 404
            
    finally:
        conn.close()

@app.route('/api/rag-knowledge', methods=['POST'])
def create_knowledge():
    """添加知识"""
    data = request.get_json() or {}
    
    if not data.get('title') or not data.get('content'):
        return jsonify({'success': False, 'error': '标题和内容不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO knowledge_base 
               (category, title, content, tags, source, is_active, created_at, updated_at) 
               VALUES (%s, %s, %s, %s, %s, 1, NOW(), NOW())""",
            (
                data.get('category', 'general'),
                data['title'],
                data['content'],
                data.get('tags', ''),
                data.get('source', '')
            )
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': '知识添加成功',
            'id': cursor.lastrowid
        })
        
    finally:
        conn.close()

@app.route('/api/rag-knowledge/<int:kid>', methods=['PUT'])
def update_knowledge(kid):
    """更新知识"""
    data = request.get_json() or {}
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """UPDATE knowledge_base 
               SET title = %s, content = %s, category = %s, tags = %s, source = %s, updated_at = NOW() 
               WHERE id = %s""",
            (
                data.get('title'),
                data.get('content'),
                data.get('category'),
                data.get('tags'),
                data.get('source'),
                kid
            )
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': '知识更新成功'})
        
    finally:
        conn.close()

@app.route('/api/rag-knowledge/<int:kid>', methods=['DELETE'])
def delete_knowledge(kid):
    """删除知识（软删除）"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE knowledge_base SET is_active = 0, updated_at = NOW() WHERE id = %s",
            (kid,)
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': '知识删除成功'})
        
    finally:
        conn.close()

@app.route('/api/rag-knowledge/categories', methods=['GET'])
def get_categories():
    """获取知识分类列表"""
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM knowledge_base 
            WHERE is_active = 1 
            GROUP BY category
        """)
        categories = cursor.fetchall()
        
        return jsonify({'success': True, 'data': categories})
        
    finally:
        conn.close()

@app.route('/api/rag-knowledge/batch', methods=['POST'])
def batch_import():
    """批量导入知识"""
    data = request.get_json() or {}
    items = data.get('items', [])
    
    if not items:
        return jsonify({'success': False, 'error': '没有要导入的数据'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        success_count = 0
        for item in items:
            if item.get('title') and item.get('content'):
                cursor.execute(
                    """INSERT INTO knowledge_base 
                       (category, title, content, tags, source, is_active, created_at) 
                       VALUES (%s, %s, %s, %s, %s, 1, NOW())""",
                    (
                        item.get('category', 'general'),
                        item['title'],
                        item['content'],
                        item.get('tags', ''),
                        item.get('source', 'batch_import')
                    )
                )
                success_count += 1
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功导入 {success_count} 条知识',
            'total': len(items),
            'success_count': success_count
        })
        
    finally:
        conn.close()

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'rag-knowledge-api',
        'timestamp': datetime.now().isoformat()
    })

# ==================== 初始化 ====================

def init_database():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 创建知识库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(50) DEFAULT 'general',
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                tags VARCHAR(500),
                source VARCHAR(100),
                is_active TINYINT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_category (category),
                INDEX idx_active (is_active),
                FULLTEXT INDEX idx_content (title, content)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        conn.commit()
        print("[OK] 知识库表初始化完成")
        
    except Exception as e:
        print(f"[WARNING] 初始化失败: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    print("="*60)
    print("智能心理知识库RAG服务")
    print("="*60)
    print("功能特点：")
    print("1. 情绪检测与安抚")
    print("2. 知识库智能检索")
    print("3. AI大模型生成专业回答")
    print("4. 危机干预预警")
    print("="*60)
    print("端口: 5001")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
