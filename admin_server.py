"""
管理员后台API服务
供后端部署使用
包含：管理员管理、商品管理、风险预警、知识库管理
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from datetime import datetime, timedelta
import secrets
import requests
import json
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
CORS(app, origins=['*'])

# 阿里云百炼API配置（用于解析文本）
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'sk-cd1941be1ff64ce58eddb6e7bb69de71')
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# Token存储 (生产环境建议使用Redis)
admin_tokens = {}

# 数据库配置 - 远程数据库
DB_CONFIG = {
    'host': 'localhost',  # 如果数据库在本地用localhost，在远程服务器用127.0.0.1
    'user': 'root',
    'password': 'root1234',
    'database': 'emotion_db',
    'charset': 'utf8mb4'
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

# ==================== 数据库初始化 ====================

def init_database():
    """初始化数据库表"""
    # 先连接不带数据库
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    cursor.execute("CREATE DATABASE IF NOT EXISTS emotion_db")
    cursor.execute("USE emotion_db")
    
    # 创建用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(64) UNIQUE,
            email VARCHAR(120),
            password_hash VARCHAR(128),
            user_type ENUM('anonymous', 'registered') DEFAULT 'anonymous',
            role VARCHAR(20) DEFAULT 'user',
            is_anonymous BOOLEAN DEFAULT TRUE,
            avatar_url VARCHAR(512),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # 创建商品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price FLOAT NOT NULL,
            original_price FLOAT,
            image_url VARCHAR(512),
            category VARCHAR(64),
            stock INT DEFAULT 100,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # 创建订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            order_no VARCHAR(64) UNIQUE,
            total_amount FLOAT,
            status ENUM('pending', 'paid', 'shipped', 'completed', 'cancelled') DEFAULT 'pending',
            payment_method VARCHAR(32),
            address TEXT,
            remark TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # 创建风险预警表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            conversation_id INT,
            risk_level ENUM('low', 'medium', 'high', 'critical'),
            risk_type VARCHAR(64),
            content TEXT,
            alert_sent BOOLEAN DEFAULT FALSE,
            handled BOOLEAN DEFAULT FALSE,
            handled_by VARCHAR(64),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建知识库表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(64),
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            tags VARCHAR(255),
            source VARCHAR(128),
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # 创建知识导入记录表（用于追踪从文本导入的知识）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_imports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            source VARCHAR(255),
            content_preview TEXT,
            entity_count INT DEFAULT 0,
            relation_count INT DEFAULT 0,
            imported_by VARCHAR(64),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("数据库表初始化完成!")

# ==================== 认证接口 ====================

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': '请输入用户名和密码'}), 400
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password_hash = %s AND role = 'admin'", (username, password))
    admin = cursor.fetchone()
    conn.close()
    
    if admin:
        token = secrets.token_urlsafe(32)
        admin_tokens[token] = {
            'username': username,
            'expire': datetime.now() + timedelta(days=7)
        }
        return jsonify({
            'success': True,
            'data': {'token': token, 'username': username}
        })
    return jsonify({'success': False, 'error': '用户名或密码错误'}), 401

def verify_token():
    """验证Token"""
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
        if token in admin_tokens:
            info = admin_tokens[token]
            if info['expire'] > datetime.now():
                return info
    return None

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
        admin_tokens.pop(token, None)
    return jsonify({'success': True})

@app.route('/api/admin/check', methods=['GET'])
def check_admin():
    info = verify_token()
    if info:
        return jsonify({'success': True, 'data': {'username': info['username']}})
    return jsonify({'success': False}), 401

# ==================== 统计接口 ====================

@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 今日新增用户
    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = %s", (today,))
    today_users = cursor.fetchone()[0] or 0
    
    # 总用户数
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0] or 0
    
    # 高危预警数
    cursor.execute("SELECT COUNT(*) FROM risk_alerts WHERE handled = 0 AND risk_level IN ('high', 'critical')")
    high_risk = cursor.fetchone()[0] or 0
    
    # 今日销售额
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) = %s", (today,))
    today_sales = cursor.fetchone()[0] or 0
    
    # 总销售额
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders")
    total_sales = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'today_users': today_users,
            'total_users': total_users,
            'high_risk_alerts': high_risk,
            'today_sales': round(today_sales, 2),
            'total_sales': round(total_sales, 2)
        }
    })

# ==================== 商品管理接口 ====================

@app.route('/api/admin/products', methods=['GET'])
def get_products():
    """获取商品列表"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC")
    products = cursor.fetchall()
    conn.close()
    
    return jsonify({'success': True, 'data': products})

@app.route('/api/admin/products', methods=['POST'])
def create_product():
    """发布商品"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    data = request.get_json() or {}
    
    if not data.get('name') or not data.get('price'):
        return jsonify({'success': False, 'error': '名称和价格不能为空'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO products (name, description, price, original_price, image_url, category, stock) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (data['name'], data.get('description', ''), float(data['price']), 
             float(data['original_price']) if data.get('original_price') else None, 
             data.get('image_url'), 
             data.get('category', 'product'), 
             int(data.get('stock', 100)))
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '商品发布成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """删除商品"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET is_active = 0 WHERE id = %s", (product_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ==================== 风险预警接口 ====================

@app.route('/api/admin/risks', methods=['GET'])
def get_risks():
    """获取风险预警列表"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT r.*, u.username 
        FROM risk_alerts r 
        LEFT JOIN users u ON r.user_id = u.id 
        ORDER BY r.created_at DESC LIMIT 50
    """)
    risks = cursor.fetchall()
    conn.close()
    
    return jsonify({'success': True, 'data': risks})

@app.route('/api/admin/risks/<int:risk_id>/handle', methods=['POST'])
def handle_risk(risk_id):
    """处理风险预警"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    data = request.get_json() or {}
    handler = data.get('handled_by', 'admin')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE risk_alerts SET handled = 1, handled_by = %s WHERE id = %s", (handler, risk_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ==================== 订单接口 ====================

@app.route('/api/admin/orders', methods=['GET'])
def get_orders():
    """获取订单列表"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT o.*, u.username 
        FROM orders o 
        LEFT JOIN users u ON o.user_id = u.id 
        ORDER BY o.created_at DESC LIMIT 100
    """)
    orders = cursor.fetchall()
    conn.close()
    
    return jsonify({'success': True, 'data': orders})

@app.route('/api/admin/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """更新订单状态"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    data = request.get_json() or {}
    status = data.get('status')
    
    if not status:
        return jsonify({'success': False, 'error': '状态不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = %s, updated_at = NOW() WHERE id = %s", (status, order_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ==================== 用户接口 ====================

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT id, username, email, user_type, role, created_at FROM users ORDER BY created_at DESC LIMIT 100")
    users = cursor.fetchall()
    conn.close()
    
    return jsonify({'success': True, 'data': users})

# ==================== 知识库管理（基于Neo4j）====================

# Neo4j配置
NEO4J_CONFIG = {
    'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    'username': os.getenv('NEO4J_USERNAME', 'neo4j'),
    'password': os.getenv('NEO4J_PASSWORD', 'root1234')
}

# 导入Neo4j驱动
try:
    from neo4j import GraphDatabase
    neo4j_available = True
except ImportError:
    neo4j_available = False
    print("[WARNING] Neo4j驱动未安装，知识库功能不可用")

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self._driver = None
        if not neo4j_available:
            return
        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            print(f"[OK] Neo4j连接成功")
        except Exception as e:
            print(f"[ERROR] Neo4j连接失败: {e}")
    
    def close(self):
        if self._driver:
            self._driver.close()
    
    def run(self, query, parameters=None):
        if not self._driver:
            raise Exception("Neo4j未连接")
        with self._driver.session() as session:
            return session.run(query, parameters)
    
    def run_read(self, query, parameters=None):
        if not self._driver:
            return []
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

def call_llm_for_extraction(text):
    """调用LLM从文本中提取知识图谱实体和关系"""
    try:
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""请从以下心理学文本中提取知识图谱的实体和关系。

文本内容：
{text[:2000]}

请按JSON格式输出：
{{
    "entities": [
        {{"type": "Emotion", "name": "情绪名称", "description": "描述"}},
        {{"type": "Symptom", "name": "症状名称", "description": "描述"}},
        {{"type": "Treatment", "name": "治疗方法", "description": "描述"}},
        {{"type": "Technique", "name": "技巧", "description": "描述"}},
        {{"type": "Cause", "name": "原因", "description": "描述"}}
    ],
    "relationships": [
        {{"from": "情绪名称", "to": "症状名称", "type": "LEADS_TO"}},
        {{"from": "情绪名称", "to": "治疗方法", "type": "RELIEVED_BY"}}
    ]
}}

注意：
1. type必须是：Emotion(情绪)、Symptom(症状)、Treatment(治疗)、Technique(技巧)、Cause(原因)
2. 关系类型必须是：LEADS_TO(导致)、RELIEVED_BY(缓解)、HAS_TECHNIQUE(有技巧)、CAUSED_BY(由...引起)
3. 只输出JSON，不要其他内容"""

        data = {
            "model": "qwen-plus",
            "messages": [
                {"role": "system", "content": "你是知识图谱抽取专家。只输出JSON格式。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        response = requests.post(DASHSCOPE_API_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"[ERROR] LLM提取失败: {e}")
        return None

def add_to_knowledge_graph(entities, relationships):
    """将实体和关系添加到Neo4j"""
    if not neo4j_conn:
        raise Exception("Neo4j未连接")
    
    try:
        # 创建实体
        for entity in entities:
            cypher = """
            MERGE (n:{type} {{name: $name}})
            ON CREATE SET n.description = $description, n.created_at = datetime()
            ON MATCH SET n.description = $description, n.updated_at = datetime()
            """.format(type=entity['type'])
            
            neo4j_conn.run(cypher, {
                'name': entity['name'],
                'description': entity.get('description', '')
            })
        
        # 创建关系
        for rel in relationships:
            cypher = """
            MATCH (a {{name: $from_name}}), (b {{name: $to_name}})
            MERGE (a)-[r:{rel_type}]->(b)
            ON CREATE SET r.created_at = datetime()
            """.format(rel_type=rel['type'])
            
            neo4j_conn.run(cypher, {
                'from_name': rel['from'],
                'to_name': rel['to']
            })
        
        return True
    except Exception as e:
        print(f"[ERROR] 添加到知识图谱失败: {e}")
        return False

@app.route('/api/admin/knowledge/import', methods=['POST'])
def import_knowledge():
    """从文本导入知识到知识图谱"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    if not neo4j_conn:
        return jsonify({'success': False, 'error': '知识库服务未启动'}), 500
    
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    title = data.get('title', '未命名').strip()
    source = data.get('source', '').strip()
    
    if not text:
        return jsonify({'success': False, 'error': '文本内容不能为空'}), 400
    
    try:
        # 1. 使用LLM提取实体和关系
        extracted = call_llm_for_extraction(text)
        
        if not extracted:
            return jsonify({'success': False, 'error': '文本解析失败'}), 500
        
        entities = extracted.get('entities', [])
        relationships = extracted.get('relationships', [])
        
        if not entities:
            return jsonify({'success': False, 'error': '未提取到有效知识'}), 400
        
        # 2. 添加到Neo4j
        success = add_to_knowledge_graph(entities, relationships)
        
        if not success:
            return jsonify({'success': False, 'error': '添加到知识图谱失败'}), 500
        
        # 3. 记录到MySQL（便于管理）
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO knowledge_imports (title, source, content_preview, 
                                         entity_count, relation_count, imported_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (title, source, text[:200], len(entities), len(relationships), 
              verify_token()['username']))
        conn.commit()
        import_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'成功导入知识，提取了{len(entities)}个实体和{len(relationships)}个关系',
            'data': {
                'import_id': import_id,
                'entities': entities,
                'relationships': relationships
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/knowledge/imports', methods=['GET'])
def get_knowledge_imports():
    """获取知识导入记录"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT SQL_CALC_FOUND_ROWS *, 
               DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') as import_time
        FROM knowledge_imports 
        ORDER BY created_at DESC 
        LIMIT %s OFFSET %s
    """, (per_page, (page - 1) * per_page))
    
    imports = cursor.fetchall()
    
    cursor.execute("SELECT FOUND_ROWS() as total")
    total = cursor.fetchone()['total']
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'list': imports,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    })

@app.route('/api/admin/knowledge/graph', methods=['GET'])
def get_knowledge_graph():
    """获取知识图谱数据（用于可视化）"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    if not neo4j_conn:
        return jsonify({'success': False, 'error': '知识库服务未启动'}), 500
    
    emotion = request.args.get('emotion', '')
    
    try:
        if emotion:
            # 获取特定情绪的知识图谱
            cypher = """
            MATCH path = (e:Emotion {name: $emotion})-[r*1..2]->(related)
            RETURN [node in nodes(path) | {
                id: id(node),
                name: node.name,
                type: labels(node)[0],
                description: node.description
            }] as nodes,
            [rel in relationships(path) | {
                source: id(startNode(rel)),
                target: id(endNode(rel)),
                type: type(rel)
            }] as relationships
            LIMIT 50
            """
            results = neo4j_conn.run_read(cypher, {'emotion': emotion})
        else:
            # 获取全部（限制数量）
            cypher = """
            MATCH (n)-[r]->(m)
            RETURN {
                id: id(n),
                name: n.name,
                type: labels(n)[0],
                description: n.description
            } as source,
            {
                id: id(m),
                name: m.name,
                type: labels(m)[0],
                description: m.description
            } as target,
            type(r) as relationship
            LIMIT 100
            """
            results = neo4j_conn.run_read(cypher)
        
        # 格式化数据
        nodes = {}
        links = []
        
        for record in results:
            if emotion:
                # 处理路径格式
                path_nodes = record['nodes']
                path_rels = record['relationships']
                for node in path_nodes:
                    if node['id'] not in nodes:
                        nodes[node['id']] = node
                for rel in path_rels:
                    links.append(rel)
            else:
                # 处理关系格式
                source = record['source']
                target = record['target']
                nodes[source['id']] = source
                nodes[target['id']] = target
                links.append({
                    'source': source['id'],
                    'target': target['id'],
                    'type': record['relationship']
                })
        
        return jsonify({
            'success': True,
            'data': {
                'nodes': list(nodes.values()),
                'links': links
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/knowledge/nodes', methods=['GET'])
def get_knowledge_nodes():
    """获取知识图谱节点列表"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    if not neo4j_conn:
        return jsonify({'success': False, 'error': '知识库服务未启动'}), 500
    
    node_type = request.args.get('type', '')
    keyword = request.args.get('keyword', '')
    
    try:
        if node_type:
            cypher = f"MATCH (n:{node_type}) WHERE n.name CONTAINS $keyword RETURN n.name as name, n.description as description LIMIT 100"
        else:
            cypher = "MATCH (n) WHERE n.name CONTAINS $keyword RETURN labels(n)[0] as type, n.name as name, n.description as description LIMIT 100"
        
        results = neo4j_conn.run_read(cypher, {'keyword': keyword})
        
        nodes = []
        for record in results:
            nodes.append({
                'type': record.get('type', node_type),
                'name': record['name'],
                'description': record['description']
            })
        
        return jsonify({'success': True, 'data': nodes})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/knowledge/node', methods=['POST'])
def create_knowledge_node():
    """手动创建知识节点"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    if not neo4j_conn:
        return jsonify({'success': False, 'error': '知识库服务未启动'}), 500
    
    data = request.get_json() or {}
    node_type = data.get('type', '').strip()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not node_type or not name:
        return jsonify({'success': False, 'error': '类型和名称不能为空'}), 400
    
    try:
        cypher = f"""
        CREATE (n:{node_type} {{name: $name, description: $description, created_at: datetime()}})
        RETURN id(n) as id
        """
        result = neo4j_conn.run_read(cypher, {'name': name, 'description': description})
        
        return jsonify({
            'success': True,
            'message': '节点创建成功',
            'data': {'id': result[0]['id'] if result else None}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/knowledge/relationship', methods=['POST'])
def create_knowledge_relationship():
    """手动创建知识关系"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    if not neo4j_conn:
        return jsonify({'success': False, 'error': '知识库服务未启动'}), 500
    
    data = request.get_json() or {}
    from_name = data.get('from', '').strip()
    to_name = data.get('to', '').strip()
    rel_type = data.get('type', '').strip()
    
    if not from_name or not to_name or not rel_type:
        return jsonify({'success': False, 'error': '参数不完整'}), 400
    
    try:
        cypher = f"""
        MATCH (a {{name: $from_name}}), (b {{name: $to_name}})
        CREATE (a)-[r:{rel_type}]->(b)
        RETURN id(r) as id
        """
        result = neo4j_conn.run_read(cypher, {'from_name': from_name, 'to_name': to_name})
        
        return jsonify({
            'success': True,
            'message': '关系创建成功',
            'data': {'id': result[0]['id'] if result else None}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/knowledge/node/<name>', methods=['DELETE'])
def delete_knowledge_node(name):
    """删除知识节点及其关系"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    if not neo4j_conn:
        return jsonify({'success': False, 'error': '知识库服务未启动'}), 500
    
    try:
        cypher = """
        MATCH (n {name: $name})
        OPTIONAL MATCH (n)-[r]-()
        DELETE r, n
        """
        neo4j_conn.run(cypher, {'name': name})
        
        return jsonify({'success': True, 'message': '节点删除成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/knowledge/stats', methods=['GET'])
def get_knowledge_stats():
    """获取知识图谱统计"""
    if not verify_token():
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    if not neo4j_conn:
        return jsonify({'success': False, 'error': '知识库服务未启动'}), 500
    
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
        
        # 导入记录数
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_imports")
        stats['import_count'] = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 健康检查 ====================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'time': datetime.now().isoformat(),
        'neo4j': 'connected' if neo4j_conn else 'not_available'
    })

if __name__ == '__main__':
    # 初始化数据库
    try:
        init_database()
    except Exception as e:
        print(f"数据库初始化: {e}")
    
    # 启动命令: python admin_server.py
    # 端口: 5000
    print("="*50)
    print("管理员后台服务")
    print("端口: 5005")
    print("="*50)
    app.run(host='0.0.0.0', port=5005, debug=False)
