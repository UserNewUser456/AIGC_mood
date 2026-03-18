"""
基于Neo4j知识图谱的智能心理知识库RAG服务
结合知识图谱推理 + AI大模型生成专业、温暖的回答
"""
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import requests
import json
import os
from collections import Counter
from datetime import datetime
import re

# Neo4j图数据库
try:
    from neo4j import GraphDatabase
    neo4j_available = True
except ImportError:
    neo4j_available = False
    print("[WARNING] Neo4j驱动未安装")

app = Flask(__name__)
CORS(app, origins=['*'])

# ==================== 配置 ====================

# Neo4j数据库配置
NEO4J_CONFIG = {
    'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    'username': os.getenv('NEO4J_USERNAME', 'neo4j'),
    'password': os.getenv('NEO4J_PASSWORD', 'root1234')  # 修改为实际密码
}

# 阿里云百炼API配置
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'sk-cd1941be1ff64ce58eddb6e7bb69de71')
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# ==================== Neo4j连接管理 ====================

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

# 初始化Neo4j连接
neo4j_conn = None
neo4j_connected = False
if neo4j_available:
    try:
        neo4j_conn = Neo4jConnection(
            NEO4J_CONFIG['uri'],
            NEO4J_CONFIG['username'],
            NEO4J_CONFIG['password']
        )
        # 测试连接
        if neo4j_conn._driver:
            neo4j_conn.run_read("RETURN 1")
            neo4j_connected = True
            print("[OK] Neo4j连接成功")
    except Exception as e:
        print(f"[WARNING] Neo4j连接失败: {e}")
        print("[INFO] 服务将以有限功能模式运行")
        neo4j_conn = None
        neo4j_connected = False

# ==================== 情绪检测与安抚 ====================

# 情绪关键词词典
EMOTION_KEYWORDS = {
    '焦虑': {
        'keywords': ['焦虑', '紧张', '不安', '担心', '压力大', '心慌', '坐立不安', '烦躁'],
        'comfort': [
            "我理解你现在的焦虑感，这种感觉确实让人不舒服。",
            "焦虑是一种正常的情绪反应，让我们一起来面对它。",
            "别担心，我们会找到缓解焦虑的方法。"
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
        'keywords': ['愤怒', '生气', '发火', '暴躁', '怨恨', '不满', '讨厌'],
        'comfort': [
            "我能感受到你现在的愤怒，这种情绪需要被理解。",
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
    '失眠': {
        'keywords': ['失眠', '睡不着', '睡眠不好', '难以入睡', '早醒', '睡眠质量差'],
        'comfort': [
            "失眠确实会让人很难受，影响白天的状态。",
            "睡眠问题很常见，我们一起来改善它。",
            "有很多方法可以帮助你获得更好的睡眠。"
        ]
    }
}

# 严重风险词
RISK_KEYWORDS = ['自杀', '自残', '结束生命', '不想活', '死了算了', '活不下去', '解脱', '结束一切']

def detect_emotion(text):
    """
    检测用户情绪状态
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
                'comfort_message': "我注意到你可能正在经历非常困难的时刻。",
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
    
    return {
        'primary_emotion': '中性',
        'risk_level': 'low',
        'comfort_message': "感谢你愿意和我分享。",
        'detected_keywords': [],
        'is_crisis': False
    }

# ==================== 知识图谱检索 ====================

def search_knowledge_graph(emotion, query, top_k=3):
    """
    从知识图谱中检索相关知识
    使用Neo4j Cypher查询
    """
    # 扩展查询词
    query_words = query.lower().split()
    
    # Cypher查询：根据情绪类型和相关关键词检索
    cypher_query = """
    // 根据情绪类型查找相关知识
    MATCH (e:Emotion {name: $emotion})
    OPTIONAL MATCH (e)-[:LEADS_TO]->(s:Symptom)
    OPTIONAL MATCH (e)-[:RELIEVED_BY]->(t:Treatment)
    OPTIONAL MATCH (e)-[:HAS_TECHNIQUE]->(tech:Technique)
    
    // 根据关键词查找
    WITH e, s, t, tech
    OPTIONAL MATCH (n)
    WHERE (n:Symptom OR n:Treatment OR n:Technique OR n:Cause)
      AND ANY(word IN $query_words WHERE toLower(n.name) CONTAINS word OR toLower(n.description) CONTAINS word)
    
    // 收集结果
    WITH COLLECT(DISTINCT {
        type: CASE 
            WHEN n IS NOT NULL THEN labels(n)[0]
            WHEN s IS NOT NULL THEN 'Symptom'
            WHEN t IS NOT NULL THEN 'Treatment'
            WHEN tech IS NOT NULL THEN 'Technique'
            ELSE 'Emotion'
        END,
        name: COALESCE(n.name, s.name, t.name, tech.name, e.name),
        description: COALESCE(n.description, s.description, t.description, tech.description, e.description),
        match_type: CASE 
            WHEN n IS NOT NULL THEN 'keyword_match'
            ELSE 'emotion_related'
        END
    }) as results
    
    // 展开并去重
    UNWIND results as result
    WITH DISTINCT result
    WHERE result.name IS NOT NULL
    
    // 返回前N个结果
    RETURN result.type as type, 
           result.name as name, 
           result.description as description,
           result.match_type as match_type
    LIMIT $limit
    """
    
    try:
        results = neo4j_conn.run_read(cypher_query, {
            'emotion': emotion,
            'query_words': query_words,
            'limit': top_k * 2
        })
        
        # 格式化结果
        knowledge_items = []
        for record in results:
            knowledge_items.append({
                'type': record['type'],
                'name': record['name'],
                'description': record['description'] or '',
                'match_type': record['match_type']
            })
        
        return knowledge_items
        
    except Exception as e:
        print(f"[ERROR] 知识图谱查询失败: {e}")
        return []

def get_related_knowledge_path(emotion):
    """
    获取知识图谱中的相关路径
    例如：焦虑 -> 症状 -> 治疗方法
    """
    cypher_query = """
    MATCH path = (e:Emotion {name: $emotion})-[:LEADS_TO|HAS_SYMPTOM|RELIEVED_BY*1..3]->(related)
    RETURN [node in nodes(path) | {
        name: node.name,
        type: labels(node)[0],
        description: node.description
    }] as path_nodes,
    [rel in relationships(path) | type(rel)] as path_rels
    LIMIT 5
    """
    
    try:
        results = neo4j_conn.run_read(cypher_query, {'emotion': emotion})
        paths = []
        for record in results:
            paths.append({
                'nodes': record['path_nodes'],
                'relationships': record['path_rels']
            })
        return paths
    except Exception as e:
        print(f"[ERROR] 路径查询失败: {e}")
        return []

# ==================== AI大模型回答生成 ====================

def call_llm(messages, stream=False, temperature=0.7):
    """调用阿里云百炼大模型API"""
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
            print(f"[ERROR] LLM API错误: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 调用LLM异常: {e}")
        return None

def generate_ai_response(question, knowledge_items, emotion_info):
    """使用AI大模型生成专业、温暖的回答"""
    
    has_knowledge = knowledge_items and len(knowledge_items) > 0
    primary_emotion = emotion_info.get('primary_emotion', '中性')
    
    # 根据是否有知识图谱内容选择不同的系统提示
    if has_knowledge:
        # 有专业知识，使用专业模式
        system_prompt = """你是一位温暖专业的心理咨询师。

任务：根据知识图谱内容，用自己的话回答用户问题。
重要：
1. 必须将知识图谱内容用自己的话复述，不能直接复制
2. 回答要自然、流畅，像和人聊天
3. 先共情，再给建议，最后鼓励
4. 控制在200字左右"""
        
        knowledge_context = "\n\n知识图谱信息：\n"
        for item in knowledge_items[:3]:
            knowledge_context += f"- {item.get('name', '')}: {item.get('description', '')[:80]}\n"
    else:
        # 没有专业知识，使用闲聊模式
        system_prompt = """你是一位温暖友好的心理咨询师助手。

任务：和用户进行自然、温暖的日常对话。
重要：
1. 像朋友聊天一样，自然回应
2. 不要重复同样的开场白
3. 适当关心用户的感受
4. 如果用户表达负面情绪，给予理解和支持
5. 控制在150字左右"""
        
        knowledge_context = ""
    
    # 共情语随机变化（避免重复）
    comfort_options = [
        "谢谢你的分享，",
        "我听到你了，",
        "感谢你愿意告诉我这些，",
        "很高兴你能和我聊聊，",
    ]
    import random
    comfort_prefix = random.choice(comfort_options) if primary_emotion != '中性' else ""
    comfort = emotion_info.get('comfort_message', '')
    
    # 危机情况特殊处理
    if emotion_info.get('is_crisis'):
        messages = [
            {"role": "system", "content": "你是一位危机干预专家。用户表达了自杀或自伤的想法，请立即提供危机干预信息。"},
            {"role": "user", "content": f"用户说：{question}\n\n请立即进行危机干预，强调寻求专业帮助的重要性。"}
        ]
        
        ai_response = call_llm(messages)
        if ai_response:
            return ai_response + "\n\n🆘 **紧急求助资源**：\n- 全国24小时心理危机干预热线：400-161-9995\n- 北京心理危机研究与干预中心：010-82951332\n- 生命热线：400-821-1215"
        return "我注意到你可能正在经历非常艰难的时刻。请立即联系专业心理咨询师或拨打心理危机干预热线：400-161-9995。你的生命很珍贵，有人愿意帮助你。"
    
    # 正常情况 - 根据是否有知识调整提示
    if has_knowledge:
        user_content = f"用户问题：{question}\n{knowledge_context}\n\n请结合以上知识，用自己的话回答。先共情，再给建议。控制在200字左右。"
    else:
        user_content = f"用户说：{question}\n\n请进行温暖友好的对话回应。控制在150字左右。"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    ai_response = call_llm(messages)
    
    if ai_response:
        full_response = f"{comfort}\n\n{ai_response}"
        return full_response
    
    # 后备回答
    return generate_fallback_response(question, knowledge_items, emotion_info)

def generate_fallback_response(question, knowledge_items, emotion_info):
    """AI调用失败时的后备回答"""
    comfort = emotion_info.get('comfort_message', '感谢你的分享。')
    
    response = comfort + "\n\n"
    
    if knowledge_items:
        response += "根据心理学知识，我为你整理了一些信息：\n\n"
        for item in knowledge_items[:2]:
            response += f"📖 **{item['name']}** ({item['type']})\n{item['description'][:150]}...\n\n"
    else:
        response += "虽然我没有找到特定的知识，但请记住：\n"
        response += "1. 你的感受是真实的，值得被尊重\n"
        response += "2. 情绪会过去，困难也会过去\n"
        response += "3. 寻求支持是勇敢的表现\n\n"
    
    response += "💝 如果你感到困扰，建议寻求专业心理咨询师的帮助。"
    
    return response

# ==================== API接口 ====================

@app.route('/api/rag-knowledge/chat', methods=['POST'])
def chat():
    """
    智能对话接口
    结合情绪检测 + 知识图谱检索 + AI生成回答
    """
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    user_id = data.get('user_id')
    stream = data.get('stream', False)
    
    if not question:
        return jsonify({'success': False, 'error': '问题不能为空'}), 400
    
    # 1. 检测情绪
    emotion_info = detect_emotion(question)
    primary_emotion = emotion_info['primary_emotion']
    
    # 2. 从知识图谱检索
    knowledge_items = search_knowledge_graph(primary_emotion, question, top_k=3)
    
    # 3. 获取相关路径
    knowledge_paths = []
    if primary_emotion != '中性':
        knowledge_paths = get_related_knowledge_path(primary_emotion)
    
    # 4. 生成回答
    if stream:
        # 流式响应
        def generate():
            yield f"data: {json.dumps({'emotion': emotion_info, 'type': 'emotion'})}\n\n"
            
            ai_response = generate_ai_response(question, knowledge_items, emotion_info)
            if ai_response:
                # 模拟流式输出
                for char in ai_response:
                    yield f"data: {json.dumps({'content': char, 'type': 'content'})}\n\n"
            
            yield f"data: {json.dumps({'done': True, 'knowledge_count': len(knowledge_items), 'type': 'done'})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream; charset=utf-8',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )
    else:
        # 普通响应
        answer = generate_ai_response(question, knowledge_items, emotion_info)
        
        return jsonify({
            'success': True,
            'data': {
                'question': question,
                'answer': answer,
                'emotion': primary_emotion,
                'risk_level': emotion_info['risk_level'],
                'knowledge_items': knowledge_items,
                'knowledge_paths': knowledge_paths
            }
        })

@app.route('/api/rag-knowledge/emotion/<emotion_name>', methods=['GET'])
def get_emotion_knowledge(emotion_name):
    """获取特定情绪的知识图谱"""
    try:
        # 查询情绪节点及其关系
        cypher_query = """
        MATCH (e:Emotion {name: $emotion})
        OPTIONAL MATCH (e)-[:LEADS_TO]->(s:Symptom)
        OPTIONAL MATCH (e)-[:CAUSED_BY]->(c:Cause)
        OPTIONAL MATCH (e)-[:RELIEVED_BY]->(t:Treatment)
        OPTIONAL MATCH (e)-[:HAS_TECHNIQUE]->(tech:Technique)
        
        RETURN e.name as emotion,
               e.description as description,
               COLLECT(DISTINCT {type: 'symptom', name: s.name, description: s.description}) as symptoms,
               COLLECT(DISTINCT {type: 'cause', name: c.name, description: c.description}) as causes,
               COLLECT(DISTINCT {type: 'treatment', name: t.name, description: t.description}) as treatments,
               COLLECT(DISTINCT {type: 'technique', name: tech.name, description: tech.description}) as techniques
        """
        
        results = neo4j_conn.run_read(cypher_query, {'emotion': emotion_name})
        
        if results:
            record = results[0]
            return jsonify({
                'success': True,
                'data': {
                    'emotion': record['emotion'],
                    'description': record['description'],
                    'symptoms': [s for s in record['symptoms'] if s['name']],
                    'causes': [c for c in record['causes'] if c['name']],
                    'treatments': [t for t in record['treatments'] if t['name']],
                    'techniques': [t for t in record['techniques'] if t['name']]
                }
            })
        else:
            return jsonify({'success': False, 'error': '未找到该情绪的知识'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rag-knowledge/search', methods=['GET'])
def search_knowledge():
    """搜索知识图谱"""
    keyword = request.args.get('keyword', '')
    
    if not keyword:
        return jsonify({'success': False, 'error': '关键词不能为空'}), 400
    
    try:
        cypher_query = """
        MATCH (n)
        WHERE (n:Emotion OR n:Symptom OR n:Treatment OR n:Technique OR n:Cause)
          AND (toLower(n.name) CONTAINS $keyword OR toLower(n.description) CONTAINS $keyword)
        RETURN labels(n)[0] as type, n.name as name, n.description as description
        LIMIT 20
        """
        
        results = neo4j_conn.run_read(cypher_query, {'keyword': keyword.lower()})
        
        items = []
        for record in results:
            items.append({
                'type': record['type'],
                'name': record['name'],
                'description': record['description']
            })
        
        return jsonify({'success': True, 'data': items})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rag-knowledge/emotions', methods=['GET'])
def get_all_emotions():
    """获取所有情绪类型"""
    try:
        cypher_query = """
        MATCH (e:Emotion)
        RETURN e.name as name, e.description as description
        ORDER BY e.name
        """
        
        results = neo4j_conn.run_read(cypher_query)
        
        emotions = []
        for record in results:
            emotions.append({
                'name': record['name'],
                'description': record['description']
            })
        
        return jsonify({'success': True, 'data': emotions})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rag-knowledge/graph-stats', methods=['GET'])
def get_graph_stats():
    """获取知识图谱统计信息"""
    try:
        stats = {}
        
        # 各类节点数量
        node_types = ['Emotion', 'Symptom', 'Treatment', 'Technique', 'Cause']
        for node_type in node_types:
            cypher = f"MATCH (n:{node_type}) RETURN count(n) as count"
            results = neo4j_conn.run_read(cypher)
            stats[node_type.lower() + '_count'] = results[0]['count'] if results else 0
        
        # 关系数量
        rel_cypher = "MATCH ()-[r]->() RETURN count(r) as count"
        rel_results = neo4j_conn.run_read(rel_cypher)
        stats['relationship_count'] = rel_results[0]['count'] if rel_results else 0
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    neo4j_status = 'ok'
    try:
        neo4j_conn.run_read("MATCH (n) RETURN count(n) LIMIT 1")
    except:
        neo4j_status = 'error'
    
    return jsonify({
        'status': 'ok',
        'service': 'rag-knowledge-graph-api',
        'neo4j': neo4j_status,
        'timestamp': datetime.now().isoformat()
    })

# ==================== 初始化 ====================

def init_knowledge_graph():
    """初始化知识图谱数据"""
    print("[INFO] 初始化知识图谱...")
    
    # 检查是否已有数据
    try:
        results = neo4j_conn.run_read("MATCH (n) RETURN count(n) as count")
        if results and results[0]['count'] > 0:
            print(f"[OK] 知识图谱已有 {results[0]['count']} 个节点")
            return
    except:
        pass
    
    # 创建初始数据
    cypher = """
    // 创建情绪节点
    CREATE (e1:Emotion {name: '焦虑', description: '一种紧张、不安的情绪状态，常伴有担心和恐惧'})
    CREATE (e2:Emotion {name: '抑郁', description: '情绪低落、兴趣减退、精力不足的状态'})
    CREATE (e3:Emotion {name: '愤怒', description: '因不满或受挫而产生的强烈情绪反应'})
    CREATE (e4:Emotion {name: '恐惧', description: '对威胁或危险的本能情绪反应'})
    CREATE (e5:Emotion {name: '孤独', description: '感到缺乏社交联系或被理解的情感体验'})
    CREATE (e6:Emotion {name: '失眠', description: '难以入睡或保持睡眠状态的问题'})
    
    // 创建症状节点
    CREATE (s1:Symptom {name: '心慌', description: '心跳加快或不规则的感觉'})
    CREATE (s2:Symptom {name: '肌肉紧张', description: '身体肌肉持续紧绷的状态'})
    CREATE (s3:Symptom {name: '注意力难集中', description: '难以将注意力集中在特定任务上'})
    CREATE (s4:Symptom {name: '睡眠障碍', description: '入睡困难、早醒或睡眠质量差'})
    
    // 创建治疗方法节点
    CREATE (t1:Treatment {name: '认知行为疗法', description: '通过改变思维和行为模式来改善情绪的心理治疗方法'})
    CREATE (t2:Treatment {name: '正念冥想', description: '通过专注当下、接纳体验来减轻压力的方法'})
    CREATE (t3:Treatment {name: '运动疗法', description: '通过规律运动来改善心理和生理状态'})
    CREATE (t4:Treatment {name: '深呼吸练习', description: '通过调节呼吸来缓解紧张情绪的技术'})
    
    // 创建技巧节点
    CREATE (tech1:Technique {name: '4-7-8呼吸法', description: '吸气4秒、屏息7秒、呼气8秒的呼吸技巧'})
    CREATE (tech2:Technique {name: '渐进式肌肉放松', description: '逐步紧张和放松各肌肉群的方法'})
    CREATE (tech3:Technique {name: '思维记录表', description: '记录和挑战负面想法的工具'})
    
    // 创建关系
    CREATE (e1)-[:LEADS_TO]->(s1)
    CREATE (e1)-[:LEADS_TO]->(s2)
    CREATE (e1)-[:LEADS_TO]->(s3)
    CREATE (e2)-[:LEADS_TO]->(s4)
    CREATE (e6)-[:HAS_SYMPTOM]->(s4)
    
    CREATE (e1)-[:RELIEVED_BY]->(t1)
    CREATE (e1)-[:RELIEVED_BY]->(t2)
    CREATE (e1)-[:RELIEVED_BY]->(t4)
    CREATE (e2)-[:RELIEVED_BY]->(t1)
    CREATE (e2)-[:RELIEVED_BY]->(t3)
    CREATE (e6)-[:RELIEVED_BY]->(t2)
    
    CREATE (t2)-[:HAS_TECHNIQUE]->(tech1)
    CREATE (t4)-[:HAS_TECHNIQUE]->(tech1)
    CREATE (t1)-[:HAS_TECHNIQUE]->(tech3)
    """
    
    try:
        neo4j_conn.run(cypher)
        print("[OK] 知识图谱初始化完成")
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")

if __name__ == '__main__':
    print("="*60)
    print("基于Neo4j知识图谱的智能心理知识库RAG服务")
    print("="*60)
    
    # 初始化知识图谱
    init_knowledge_graph()
    
    print("="*60)
    print("功能特点：")
    print("1. 情绪检测与安抚")
    print("2. Neo4j知识图谱检索")
    print("3. AI大模型生成专业回答")
    print("4. 危机干预预警")
    print("="*60)
    print("端口: 5001")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
