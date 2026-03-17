"""
管理员后台API服务
供后端部署使用
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
CORS(app, origins=['*'])

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

# ==================== 健康检查 ====================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

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
    print("端口: 5000")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=False)
