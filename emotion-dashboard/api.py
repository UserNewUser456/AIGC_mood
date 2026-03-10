"""
================================================================================
情绪愈疗平台 - Flask REST API 后端服务
================================================================================

文件名: api.py
功能: 提供RESTful API接口，包括用户管理、情绪记录、对话、知识库等
依赖: Flask, Flask-CORS, pymysql, python-dotenv

API接口列表:
    用户管理:   POST /api/users, GET /api/users/<username>
    情绪记录:   POST /api/emotion, GET /api/emotion/history, GET /api/emotion/stats
    对话管理:  POST /api/conversations, POST /api/conversations/<id>/messages
    周报:      GET /api/report/weekly
    知识库:    GET /api/knowledge
    资源推荐:   GET /api/resources
    风险预警:   GET /api/risk/alerts, PUT /api/risk/alerts/<id>

使用方法:
    python api.py

运行服务后，访问 http://localhost:5000 查看API文档
================================================================================
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

import pymysql
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# ================================================================================
# 第一部分：Flask应用配置
# ================================================================================

# ================================================================================
# 第一部分：Flask应用配置
# ================================================================================

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 创建Flask应用实例
# template_folder: HTML模板目录，默认 'templates'
# static_folder: 静态资源目录，默认 'static'
app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'), 
            static_folder=os.path.join(BASE_DIR, 'static'))

# 设置Secret Key，用于会话安全等
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'emotion-dashboard-secret-key')

# ================================================================================
# 第二部分：CORS跨域配置
# ================================================================================

# 启用CORS（跨域资源共享）
# 允许前端应用从不同域名访问API
CORS(app)

# ================================================================================
# 第三部分：数据库连接配置
# ================================================================================

# MySQL数据库连接配置
# 配置项说明:
#   - host: MySQL服务器地址，默认 localhost
#   - port: MySQL端口，默认 3306
#   - user: 数据库用户名，默认 root
#   - password: 数据库密码
#   - database: 数据库名称
#   - charset: 字符编码，使用 utf8mb4 支持emoji和中文
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),        # 数据库主机地址
    'port': int(os.getenv('DB_PORT', 3306)),         # 端口号
    'user': os.getenv('DB_USER', 'root'),            # 用户名
    'password': os.getenv('DB_PASSWORD', 'root1234'), # 密码
    'database': os.getenv('DB_NAME', 'emotion_db'),  # 数据库名
    'charset': 'utf8mb4'                             # 字符编码
}

# ================================================================================
# 第四部分：数据库操作工具函数
# ================================================================================

def get_db_connection():
    """
    获取MySQL数据库连接
    
    功能: 创建并返回一个数据库连接对象
    
    参数: 无
    
    返回值: pymysql数据库连接对象
    
    使用示例:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                result = cursor.fetchall()
        finally:
            conn.close()
    """
    return pymysql.connect(**DB_CONFIG)


def query_db(query, args=(), one=False):
    """
    执行SELECT查询并返回结果
    
    功能: 执行SQL查询语句并返回查询结果
    
    参数:
        query: SQL查询语句（使用%s作为占位符）
        args: 查询参数元组
        one: 是否只返回一条记录，默认False（返回所有记录）
    
    返回值:
        one=True: 返回单条记录（字典）或None
        one=False: 返回所有记录（字典列表）
    
    使用示例:
        # 查询单条
        user = query_db("SELECT * FROM users WHERE id = %s", (1,), one=True)
        
        # 查询多条
        users = query_db("SELECT * FROM users WHERE user_type = %s", ('anonymous',))
    """
    # 获取数据库连接
    conn = get_db_connection()
    try:
        # 使用DictCursor将结果转换为字典格式（可以通过列名访问）
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 执行SQL查询
            cursor.execute(query, args)
            # 根据one参数决定返回一条还是多条
            result = cursor.fetchone() if one else cursor.fetchall()
            return result
    finally:
        # 无论成功或失败都关闭连接，释放资源
        conn.close()


def execute_db(query, args=()):
    """
    执行INSERT/UPDATE/DELETE操作
    
    功能: 执行写操作SQL语句（插入、更新、删除）
    
    参数:
        query: SQL语句（使用%s作为占位符）
        args: 参数元组
    
    返回值:
        插入操作: 返回新插入记录的自增ID
        更新/删除操作: 返回受影响的行数
    
    使用示例:
        # 插入记录
        user_id = execute_db(
            "INSERT INTO users (username, user_type) VALUES (%s, %s)",
            ('test_user', 'anonymous')
        )
        
        # 更新记录
        execute_db(
            "UPDATE users SET username = %s WHERE id = %s",
            ('new_name', 1)
        )
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 执行SQL语句
            cursor.execute(query, args)
            # 提交事务，使更改生效
            conn.commit()
            # 返回最后插入的ID
            return cursor.lastrowid
    finally:
        conn.close()


# ================================================================================
# 第五部分：全局错误处理
# ================================================================================

@app.errorhandler(404)
def not_found(error):
    """
    404错误处理器
    
    功能: 处理资源不存在（接口不存在）的错误
    
    参数: error - 错误对象
    
    返回值: JSON格式的错误响应
    """
    return jsonify({"success": False, "message": "接口不存在"}), 404


@app.errorhandler(500)
def server_error(error):
    """
    500错误处理器
    
    功能: 处理服务器内部错误
    
    参数: error - 错误对象
    
    返回值: JSON格式的错误响应
    """
    return jsonify({"success": False, "message": "服务器内部错误"}), 500


# ================================================================================
# 第六部分：主页路由
# ================================================================================

@app.route('/')
def index():
    """
    主页路由
    
    功能: 返回仪表盘HTML页面
    
    返回值: 渲染后的HTML模板
    """
    return render_template('dashboard.html')


# ================================================================================
# 第七部分：用户管理API
# ================================================================================

@app.route('/api/users', methods=['POST'])
def create_user():
    """
    POST /api/users - 创建新用户
    
    功能: 创建一个新的用户记录
    
    请求体 (JSON):
        {
            "username": "用户名",           # 必填，用户名
            "user_type": "anonymous"       # 可选，默认为anonymous
        }
    
    成功响应 (201):
        {
            "success": true,
            "user_id": 1,
            "username": "test_user"
        }
    
    错误响应 (400):
        {
            "success": false,
            "message": "用户名不能为空"
        }
    """
    # 获取请求体中的JSON数据
    data = request.get_json()
    
    # 获取用户名，默认为None
    username = data.get('username')
    # 获取用户类型，默认为'anonymous'（匿名用户）
    user_type = data.get('user_type', 'anonymous')
    
    # 参数验证：用户名不能为空
    if not username:
        return jsonify({"success": False, "message": "用户名不能为空"}), 400
    
    try:
        # 执行插入操作
        user_id = execute_db(
            "INSERT INTO users (username, user_type) VALUES (%s, %s)",
            (username, user_type)
        )
        # 返回成功响应
        return jsonify({
            "success": True, 
            "user_id": user_id, 
            "username": username
        }), 201
    
    # 处理用户名重复错误
    except pymysql.IntegrityError:
        return jsonify({"success": False, "message": "用户名已存在"}), 400
    
    # 处理其他异常
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/users/<username>', methods=['GET'])
def get_user(username):
    """
    GET /api/users/<username> - 获取用户信息
    
    功能: 根据用户名查询用户详情
    
    URL参数:
        username - 用户名
    
    成功响应 (200):
        {
            "success": true,
            "data": {
                "id": 1,
                "username": "test_user",
                "user_type": "anonymous",
                "created_at": "2024-01-01T00:00:00"
            }
        }
    
    错误响应 (404):
        {
            "success": false,
            "message": "用户不存在"
        }
    """
    # 执行查询，one=True表示只返回一条记录
    user = query_db(
        "SELECT * FROM users WHERE username = %s", 
        (username,), 
        one=True
    )
    
    # 用户不存在
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404
    
    # 转换datetime对象为ISO格式字符串（便于JSON序列化）
    user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
    user['updated_at'] = user['updated_at'].isoformat() if user['updated_at'] else None
    
    # 返回用户数据
    return jsonify({"success": True, "data": user})


# ================================================================================
# 第八部分：情绪记录API
# ================================================================================

@app.route('/api/emotion', methods=['POST'])
def receive_emotion():
    """
    POST /api/emotion - 接收情绪数据上报
    
    功能: 接收并保存用户的情绪记录
    
    请求体 (JSON):
        {
            "user_id": 1,        # 必填，用户ID
            "emotion": "开心",   # 必填，情绪类型
            "score": 8.5,        # 必填，情绪分数(0-10)
            "text": "备注"       # 可选，备注文字
        }
    
    成功响应 (201):
        {
            "success": true,
            "message": "情绪记录已保存",
            "id": 1
        }
    """
    # 获取请求JSON数据
    data = request.get_json()
    
    # 提取各字段
    user_id = data.get('user_id')       # 用户ID
    emotion = data.get('emotion')       # 情绪类型
    score = data.get('score')           # 情绪分数
    text = data.get('text', '')         # 备注（默认为空字符串）
    
    # 参数验证：必填字段不能为空
    if not all([user_id, emotion, score is not None]):
        return jsonify({"success": False, "message": "缺少必要参数"}), 400
    
    # 验证分数范围（0-10）
    if not (0 <= score <= 10):
        return jsonify({"success": False, "message": "分数必须在0-10之间"}), 400
    
    try:
        # 插入情绪记录到数据库
        record_id = execute_db(
            "INSERT INTO emotion_records (user_id, emotion, score, text) VALUES (%s, %s, %s, %s)",
            (user_id, emotion, score, text)
        )
        
        # 返回成功响应
        return jsonify({
            "success": True, 
            "message": "情绪记录已保存",
            "id": record_id
        }), 201
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/emotion/history', methods=['GET'])
def get_emotion_history():
    """
    GET /api/emotion/history - 获取历史情绪数据
    
    功能: 查询用户过去N天的情绪记录
    
    查询参数:
        user_id: 用户ID（必填）
        days: 查询天数，默认7天
    
    成功响应 (200):
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "user_id": 1,
                    "emotion": "开心",
                    "score": 8.5,
                    "text": "备注",
                    "created_at": "2024-01-01T10:00:00"
                }
            ],
            "count": 10,
            "days": 7
        }
    """
    # 获取查询参数
    user_id = request.args.get('user_id', type=int)    # 用户ID
    days = int(request.args.get('days', 7))            # 查询天数，默认7
    
    # 验证user_id
    if not user_id:
        return jsonify({"success": False, "message": "user_id不能为空"}), 400
    
    # 计算查询开始日期（当前时间减去指定天数）
    start_date = datetime.now() - timedelta(days=days)
    
    # 执行查询SQL
    # 按用户ID和创建时间查询，返回指定天数内的记录
    records = query_db("""
        SELECT id, user_id, emotion, score, text, created_at 
        FROM emotion_records 
        WHERE user_id = %s AND created_at >= %s
        ORDER BY created_at ASC
    """, (user_id, start_date))
    
    # 转换日期格式为ISO字符串（便于JSON序列化）
    for r in records:
        r['created_at'] = r['created_at'].isoformat() if r['created_at'] else None
    
    # 返回结果
    return jsonify({
        "success": True,
        "data": records,
        "count": len(records),
        "days": days
    })


@app.route('/api/emotion/stats', methods=['GET'])
def get_emotion_stats():
    """
    GET /api/emotion/stats - 获取情绪统计数据
    
    功能: 计算用户情绪数据的统计信息，包括平均分、情绪分布、每日趋势等
    
    查询参数:
        user_id: 用户ID（必填）
        days: 查询天数，默认7天
    
    成功响应 (200):
        {
            "success": true,
            "data": {
                "total_records": 20,
                "avg_score": 7.2,
                "dominant_emotion": "开心",
                "emotion_distribution": {"开心": 8, "焦虑": 4},
                "daily_data": [
                    {"date": "2024-01-07", "avg_score": 7.5, "count": 3, "dominant_emotion": "开心"}
                ]
            }
        }
    """
    # 获取查询参数
    user_id = request.args.get('user_id', type=int)
    days = int(request.args.get('days', 7))
    
    # 参数验证
    if not user_id:
        return jsonify({"success": False, "message": "user_id不能为空"}), 400
    
    # 计算查询开始日期
    start_date = datetime.now() - timedelta(days=days)
    
    # 查询指定时间范围内的情绪记录
    records = query_db("""
        SELECT emotion, score, created_at 
        FROM emotion_records 
        WHERE user_id = %s AND created_at >= %s
        ORDER BY created_at ASC
    """, (user_id, start_date))
    
    # 如果没有记录，返回空统计
    if not records:
        return jsonify({
            "success": True,
            "data": {
                "total_records": 0,
                "avg_score": 0,
                "dominant_emotion": None,
                "emotion_distribution": {}
            }
        })
    
    # ========== 数据统计分析 ==========
    
    # 1. 计算平均情绪分数
    # 使用列表推导式提取所有分数，然后计算平均值
    scores = [r['score'] for r in records]
    avg_score = sum(scores) / len(scores)
    
    # 2. 统计情绪分布（每种情绪出现的次数）
    # 遍历记录，统计每种情绪出现的次数
    emotion_counts = {}
    for r in records:
        emotion_counts[r['emotion']] = emotion_counts.get(r['emotion'], 0) + 1
    
    # 3. 找出主要情绪（出现次数最多的）
    # 使用max函数根据字典的值找出最大的键
    dominant_emotion = max(emotion_counts, key=emotion_counts.get)
    
    # 4. 按日期统计每日数据
    # 创建日期到数据的映射字典
    daily_stats = {}
    for r in records:
        # 格式化日期为 YYYY-MM-DD
        date = r['created_at'].strftime('%Y-%m-%d')
        if date not in daily_stats:
            daily_stats[date] = {'scores': [], 'emotions': []}
        daily_stats[date]['scores'].append(r['score'])
        daily_stats[date]['emotions'].append(r['emotion'])
    
    # 构建每日统计数据列表
    daily_data = []
    for date, data in sorted(daily_stats.items()):
        daily_data.append({
            'date': date,
            'avg_score': round(sum(data['scores']) / len(data['scores']), 2),
            'count': len(data['scores']),
            'dominant_emotion': max(set(data['emotions']), key=data['emotions'].count)
        })
    
    # 返回统计结果
    return jsonify({
        "success": True,
        "data": {
            "total_records": len(records),
            "avg_score": round(avg_score, 2),
            "dominant_emotion": dominant_emotion,
            "emotion_distribution": emotion_counts,
            "daily_data": daily_data
        }
    })


# ================================================================================
# 第九部分：对话管理API
# ================================================================================

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """
    POST /api/conversations - 创建新对话会话
    
    功能: 创建一个新的AI对话会话
    
    请求体 (JSON):
        {
            "user_id": 1,              # 必填，用户ID
            "doctor_type": "gentle"    # 可选，医生类型，默认gentle
        }
    
    成功响应 (201):
        {
            "success": true,
            "conversation_id": 1
        }
    """
    # 获取请求数据
    data = request.get_json()
    user_id = data.get('user_id')
    doctor_type = data.get('doctor_type', 'gentle')
    
    # 验证user_id
    if not user_id:
        return jsonify({"success": False, "message": "user_id不能为空"}), 400
    
    # 创建新对话会话
    conv_id = execute_db(
        "INSERT INTO conversations (user_id, doctor_type) VALUES (%s, %s)",
        (user_id, doctor_type)
    )
    
    return jsonify({"success": True, "conversation_id": conv_id}), 201


@app.route('/api/conversations/<int:conv_id>/messages', methods=['POST'])
def send_message(conv_id):
    """
    POST /api/conversations/<id>/messages - 发送消息
    
    功能: 在指定会话中发送消息（用户消息或AI回复）
    
    URL参数:
        conv_id: 会话ID
    
    请求体 (JSON):
        {
            "role": "user",           # 必填，消息角色：user(用户) 或 assistant(AI)
            "content": "消息内容"       # 必填，消息正文
        }
    
    成功响应 (201):
        {
            "success": true,
            "message_id": 1,
            "content": "消息内容"
        }
    """
    # 获取请求数据
    data = request.get_json()
    role = data.get('role')           # 消息角色
    content = data.get('content')      # 消息内容
    
    # 参数验证
    if not role or not content:
        return jsonify({"success": False, "message": "消息内容不能为空"}), 400
    
    # 检查会话是否存在
    conv = query_db(
        "SELECT * FROM conversations WHERE id = %s", 
        (conv_id,), 
        one=True
    )
    if not conv:
        return jsonify({"success": False, "message": "对话不存在"}), 404
    
    # 保存消息到数据库
    msg_id = execute_db(
        "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
        (conv_id, role, content)
    )
    
    # 更新会话的最后活动时间
    execute_db(
        "UPDATE conversations SET updated_at = NOW() WHERE id = %s", 
        (conv_id,)
    )
    
    return jsonify({
        "success": True,
        "message_id": msg_id,
        "content": content
    })


@app.route('/api/conversations/<int:conv_id>/messages', methods=['GET'])
def get_messages(conv_id):
    """
    GET /api/conversations/<id>/messages - 获取会话消息
    
    功能: 获取指定会话的所有消息记录
    
    URL参数:
        conv_id: 会话ID
    
    成功响应 (200):
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "conversation_id": 1,
                    "role": "user",
                    "content": "你好",
                    "created_at": "2024-01-01T10:00:00"
                }
            ]
        }
    """
    # 查询会话消息
    messages = query_db(
        "SELECT * FROM messages WHERE conversation_id = %s ORDER BY created_at ASC",
        (conv_id,)
    )
    
    # 转换日期格式
    for m in messages:
        m['created_at'] = m['created_at'].isoformat() if m['created_at'] else None
    
    return jsonify({
        "success": True,
        "data": messages
    })


# ================================================================================
# 第十部分：周报API
# ================================================================================

@app.route('/api/report/weekly', methods=['GET'])
def get_weekly_report():
    """
    GET /api/report/weekly - 获取周报数据
    
    功能: 生成用户过去一周的情绪分析报告，包括统计分析和建议
    
    查询参数:
        user_id: 用户ID（必填）
    
    成功响应 (200):
        {
            "success": true,
            "report": {
                "period": "2024-01-01 至 2024-01-07",
                "total_records": 20,
                "avg_score": 7.2,
                "dominant_emotion": "开心",
                "emotion_distribution": {"开心": 10, "焦虑": 5},
                "trend": "上升趋势",
                "volatility": 1.5,
                "insights": "本周情绪整体良好..."
            }
        }
    """
    # 获取查询参数
    user_id = request.args.get('user_id', type=int)
    
    # 验证user_id
    if not user_id:
        return jsonify({"success": False, "message": "user_id不能为空"}), 400
    
    # 计算周报时间范围（过去7天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)  # 包含今天在内7天
    
    # 查询过去7天的情绪记录
    records = query_db("""
        SELECT emotion, score, created_at 
        FROM emotion_records 
        WHERE user_id = %s AND created_at >= %s
        ORDER BY created_at ASC
    """, (user_id, start_date))
    
    # 无记录时返回提示信息
    if not records:
        return jsonify({
            "success": True,
            "report": {
                "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                "total_records": 0,
                "message": "本周暂无情绪记录"
            }
        })
    
    # ========== 数据分析 ==========
    
    # 导入统计模块，用于计算标准差
    import statistics
    
    # 提取分数和情绪列表
    scores = [r['score'] for r in records]
    emotions = [r['emotion'] for r in records]
    
    # 计算平均分
    avg_score = sum(scores) / len(scores)
    
    # 计算情绪波动性（标准差）
    # 标准差越大表示情绪波动越大
    volatility = statistics.stdev(scores) if len(scores) > 1 else 0
    
    # 统计情绪分布
    emotion_counts = {}
    for e in emotions:
        emotion_counts[e] = emotion_counts.get(e, 0) + 1
    
    # 主要情绪
    dominant_emotion = max(emotion_counts, key=emotion_counts.get)
    
    # ========== 趋势分析 ==========
    # 比较前半周和后半周的平均分
    trend = "平稳"  # 默认平稳
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (len(scores) - mid)
        if second_half - first_half > 0.5:
            trend = "上升趋势"
        elif first_half - second_half > 0.5:
            trend = "下降趋势"
    
    # ========== 生成建议 ==========
    # 根据分析结果生成个性化的心理健康建议
    insights = []
    
    # 根据平均分给出建议
    if avg_score >= 7:
        insights.append("本周情绪整体良好，继续保持积极心态！")
    elif avg_score >= 5:
        insights.append("本周情绪一般，建议适当放松和调节。")
    else:
        insights.append("本周情绪偏低，建议多与朋友交流或寻求专业帮助。")
    
    # 根据波动性给出建议
    if volatility > 2:
        insights.append("情绪波动较大，建议记录触发因素以更好地了解自己。")
    
    # 根据焦虑比例给出建议
    if emotion_counts.get('焦虑', 0) > len(emotions) * 0.3:
        insights.append("焦虑情绪出现较频繁，可以尝试深呼吸或冥想放松。")
    
    # 返回周报数据
    return jsonify({
        "success": True,
        "report": {
            "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
            "total_records": len(records),
            "avg_score": round(avg_score, 2),
            "dominant_emotion": dominant_emotion,
            "emotion_distribution": emotion_counts,
            "trend": trend,
            "volatility": round(volatility, 2),
            "insights": " ".join(insights)
        }
    })


# ================================================================================
# 第十一部分：知识库API
# ================================================================================

@app.route('/api/knowledge', methods=['GET'])
def search_knowledge():
    """
    GET /api/knowledge - 搜索心理知识
    
    功能: 从知识库中搜索心理健康知识文章
    
    查询参数:
        keyword: 搜索关键词（可选）
        category: 知识分类（可选）
    
    成功响应 (200):
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "category": "情绪管理",
                    "title": "深呼吸放松法",
                    "content": "...",
                    "tags": "深呼吸,放松"
                }
            ],
            "count": 5
        }
    """
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')
    
    # 构建动态SQL查询
    # 1=1 是一个恒真条件，便于后面添加AND条件
    query = "SELECT * FROM knowledge_base WHERE 1=1"
    params = []
    
    # 添加关键词搜索条件（模糊匹配）
    if keyword:
        # 使用LIKE进行模糊匹配，%表示任意字符
        query += " AND (title LIKE %s OR content LIKE %s OR tags LIKE %s)"
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    
    # 添加分类筛选条件
    if category:
        query += " AND category = %s"
        params.append(category)
    
    # 排序并限制返回数量（最新20条）
    query += " ORDER BY created_at DESC LIMIT 20"
    
    # 执行查询
    results = query_db(query, tuple(params))
    
    # 转换日期格式
    for r in results:
        r['created_at'] = r['created_at'].isoformat() if r['created_at'] else None
        r['updated_at'] = r['updated_at'].isoformat() if r['updated_at'] else None
    
    return jsonify({"success": True, "data": results, "count": len(results)})


# ================================================================================
# 第十二部分：资源推荐API
# ================================================================================

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """
    GET /api/resources - 获取资源推荐
    
    功能: 获取心理健康资源推荐，可按类型和适用情绪筛选
    
    查询参数:
        type: 资源类型（可选）：meditation, article, music, product, consultation
        emotion: 适用情绪（可选）
    
    成功响应 (200):
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "type": "meditation",
                    "title": "5分钟正念冥想",
                    "description": "适合初学者",
                    "url": "https://...",
                    "applicable_emotions": "焦虑,压力"
                }
            ],
            "count": 5
        }
    """
    # 获取查询参数
    res_type = request.args.get('type')
    emotion = request.args.get('emotion')
    
    # 构建动态SQL
    query = "SELECT * FROM resources WHERE 1=1"
    params = []
    
    # 按资源类型筛选
    if res_type:
        query += " AND type = %s"
        params.append(res_type)
    
    # 按适用情绪筛选（模糊匹配）
    if emotion:
        query += " AND applicable_emotions LIKE %s"
        params.append(f'%{emotion}%')
    
    # 排序
    query += " ORDER BY created_at DESC"
    
    # 执行查询
    results = query_db(query, tuple(params))
    
    # 转换日期格式
    for r in results:
        r['created_at'] = r['created_at'].isoformat() if r['created_at'] else None
    
    return jsonify({"success": True, "data": results, "count": len(results)})


# ================================================================================
# 第十三部分：风险预警API
# ================================================================================

@app.route('/api/risk/alerts', methods=['GET'])
def get_risk_alerts():
    """
    GET /api/risk/alerts - 获取风险预警列表
    
    功能: 获取系统中的心理风险预警记录
    
    查询参数:
        user_id: 用户ID（可选）
        handled: 处理状态（可选）：0-未处理，1-已处理
    
    成功响应 (200):
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "user_id": 1,
                    "risk_level": "high",
                    "risk_type": "depression",
                    "content": "...",
                    "handled": 0,
                    "created_at": "2024-01-01T10:00:00"
                }
            ]
        }
    """
    # 获取查询参数
    user_id = request.args.get('user_id', type=int)
    handled = request.args.get('handled')
    
    # 构建动态SQL
    query = "SELECT * FROM risk_alerts WHERE 1=1"
    params = []
    
    # 按用户筛选
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    
    # 按处理状态筛选
    if handled is not None:
        query += " AND handled = %s"
        params.append(int(handled))
    
    # 排序并限制数量（最新50条）
    query += " ORDER BY created_at DESC LIMIT 50"
    
    # 执行查询
    alerts = query_db(query, tuple(params))
    
    # 转换日期格式
    for a in alerts:
        a['created_at'] = a['created_at'].isoformat() if a['created_at'] else None
    
    return jsonify({"success": True, "data": alerts})


@app.route('/api/risk/alerts/<int:alert_id>', methods=['PUT'])
def handle_risk_alert(alert_id):
    """
    PUT /api/risk/alerts/<id> - 处理风险预警
    
    功能: 更新预警的处理状态
    
    URL参数:
        alert_id: 预警ID
    
    请求体 (JSON):
        {
            "handled": 1    # 1-已处理，0-未处理
        }
    
    成功响应 (200):
        {
            "success": true,
            "message": "预警已处理"
        }
    """
    # 获取请求数据
    data = request.get_json()
    handled = data.get('handled', 1)
    
    # 更新预警状态
    execute_db(
        "UPDATE risk_alerts SET handled = %s WHERE id = %s", 
        (handled, alert_id)
    )
    
    return jsonify({"success": True, "message": "预警已处理"})


# ================================================================================
# 第十四部分：启动应用
# ================================================================================

if __name__ == '__main__':
    # 打印启动信息
    print("=" * 50)
    print("情绪愈疗平台API服务启动中...")
    print("访问地址: http://localhost:5000")
    print("=" * 50)
    
    # 启动Flask开发服务器
    # host='0.0.0.0': 允许外部设备访问
    # port=5000: 监听端口号
    # debug=True: 开启调试模式（修改代码后自动重载）
    app.run(host='0.0.0.0', port=5000, debug=True)
