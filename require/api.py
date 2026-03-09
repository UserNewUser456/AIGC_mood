"""
Flask REST API 后端服务
提供情绪记录、对话、知识库等API接口
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

import pymysql
from flask import Flask, request, jsonify, render_template
from flask_cORS import CORS

# ==================== 应用配置 ====================
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'emotion-dashboard-secret-key')

# 启用CORS
CORS(app)

# ==================== 数据库配置 ====================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'emotion_db'),
    'charset': 'utf8mb4'
}


# ==================== 数据库操作工具 ====================

def get_db_connection():
    """获取MySQL数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def query_db(query, args=(), one=False):
    """执行查询并返回结果"""
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, args)
            result = cursor.fetchone() if one else cursor.fetchall()
            return result
    finally:
        conn.close()


def execute_db(query, args=()):
    """执行插入/更新/删除操作"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "接口不存在"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False, "message": "服务器内部错误"}), 500


# ==================== 主页 ====================

@app.route('/')
def index():
    """仪表盘主页"""
    return render_template('dashboard.html')


# ==================== 用户管理API ====================

@app.route('/api/users', methods=['POST'])
def create_user():
    """
    POST /api/users - 创建用户

    请求体: {"username": "用户名", "user_type": "anonymous|registered"}
    """
    data = request.get_json()
    username = data.get('username')
    user_type = data.get('user_type', 'anonymous')

    if not username:
        return jsonify({"success": False, "message": "用户名不能为空"}), 400

    try:
        user_id = execute_db(
            "INSERT INTO users (username, user_type) VALUES (%s, %s)",
            (username, user_type)
        )
        return jsonify({"success": True, "user_id": user_id, "username": username}), 201
    except pymysql.IntegrityError:
        return jsonify({"success": False, "message": "用户名已存在"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/users/<username>', methods=['GET'])
def get_user(username):
    """GET /api/users/<username> - 获取用户信息"""
    user = query_db("SELECT * FROM users WHERE username = %s", (username,), one=True)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
    user['updated_at'] = user['updated_at'].isoformat() if user['updated_at'] else None
    return jsonify({"success": True, "data": user})


# ==================== 情绪记录API ====================

@app.route('/api/emotion', methods=['POST'])
def receive_emotion():
    """
    POST /api/emotion - 接收情绪数据上报

    请求体:
    {
        "user_id": 1,
        "emotion": "开心",
        "score": 8.5,
        "text": "备注"
    }
    """
    data = request.get_json()

    user_id = data.get('user_id')
    emotion = data.get('emotion')
    score = data.get('score')
    text = data.get('text', '')

    # 参数验证
    if not all([user_id, emotion, score is not None]):
        return jsonify({"success": False, "message": "缺少必要参数"}), 400

    if not (0 <= score <= 10):
        return jsonify({"success": False, "message": "分数必须在0-10之间"}), 400

    try:
        record_id = execute_db(
            "INSERT INTO emotion_records (user_id, emotion, score, text) VALUES (%s, %s, %s, %s)",
            (user_id, emotion, score, text)
        )
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

    参数: user_id, days (默认7)
    """
    user_id = request.args.get('user_id', type=int)
    days = int(request.args.get('days', 7))

    if not user_id:
        return jsonify({"success": False, "message": "user_id不能为空"}), 400

    start_date = datetime.now() - timedelta(days=days)

    records = query_db("""
        SELECT id, user_id, emotion, score, text, created_at 
        FROM emotion_records 
        WHERE user_id = %s AND created_at >= %s
        ORDER BY created_at ASC
    """, (user_id, start_date))

    # 转换日期格式
    for r in records:
        r['created_at'] = r['created_at'].isoformat() if r['created_at'] else None

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

    参数: user_id, days
    """
    user_id = request.args.get('user_id', type=int)
    days = int(request.args.get('days', 7))

    if not user_id:
        return jsonify({"success": False, "message": "user_id不能为空"}), 400

    start_date = datetime.now() - timedelta(days=days)

    # 获取记录
    records = query_db("""
        SELECT emotion, score, created_at 
        FROM emotion_records 
        WHERE user_id = %s AND created_at >= %s
        ORDER BY created_at ASC
    """, (user_id, start_date))

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

    # 计算统计数据
    scores = [r['score'] for r in records]
    avg_score = sum(scores) / len(scores)

    # 情绪分布
    emotion_counts = {}
    for r in records:
        emotion_counts[r['emotion']] = emotion_counts.get(r['emotion'], 0) + 1

    dominant_emotion = max(emotion_counts, key=emotion_counts.get)

    # 按日期统计
    daily_stats = {}
    for r in records:
        date = r['created_at'].strftime('%Y-%m-%d')
        if date not in daily_stats:
            daily_stats[date] = {'scores': [], 'emotions': []}
        daily_stats[date]['scores'].append(r['score'])
        daily_stats[date]['emotions'].append(r['emotion'])

    daily_data = []
    for date, data in sorted(daily_stats.items()):
        daily_data.append({
            'date': date,
            'avg_score': round(sum(data['scores']) / len(data['scores']), 2),
            'count': len(data['scores']),
            'dominant_emotion': max(set(data['emotions']), key=data['emotions'].count)
        })

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


# ==================== 对话API ====================

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """
    POST /api/conversations - 创建新对话
    """
    data = request.get_json()
    user_id = data.get('user_id')
    doctor_type = data.get('doctor_type', 'gentle')

    if not user_id:
        return jsonify({"success": False, "message": "user_id不能为空"}), 400

    conv_id = execute_db(
        "INSERT INTO conversations (user_id, doctor_type) VALUES (%s, %s)",
        (user_id, doctor_type)
    )
    return jsonify({"success": True, "conversation_id": conv_id}), 201


@app.route('/api/conversations/<int:conv_id>/messages', methods=['POST'])
def send_message(conv_id):
    """
    POST /api/conversations/<id>/messages - 发送消息

    请求体: {"role": "user|assistant", "content": "消息内容"}
    """
    data = request.get_json()
    role = data.get('role')
    content = data.get('content')

    if not role or not content:
        return jsonify({"success": False, "message": "消息内容不能为空"}), 400

    # 检查对话是否存在
    conv = query_db("SELECT * FROM conversations WHERE id = %s", (conv_id,), one=True)
    if not conv:
        return jsonify({"success": False, "message": "对话不存在"}), 404

    # 保存用户消息
    msg_id = execute_db(
        "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
        (conv_id, role, content)
    )

    # 更新对话时间
    execute_db("UPDATE conversations SET updated_at = NOW() WHERE id = %s", (conv_id,))

    return jsonify({
        "success": True,
        "message_id": msg_id,
        "content": content
    })


@app.route('/api/conversations/<int:conv_id>/messages', methods=['GET'])
def get_messages(conv_id):
    """
    GET /api/conversations/<id>/messages - 获取对话消息
    """
    messages = query_db(
        "SELECT * FROM messages WHERE conversation_id = %s ORDER BY created_at ASC",
        (conv_id,)
    )

    for m in messages:
        m['created_at'] = m['created_at'].isoformat() if m['created_at'] else None

    return jsonify({
        "success": True,
        "data": messages
    })


# ==================== 周报API ====================

@app.route('/api/report/weekly', methods=['GET'])
def get_weekly_report():
    """
    GET /api/report/weekly - 获取周报数据

    参数: user_id
    """
    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({"success": False, "message": "user_id不能为空"}), 400

    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)

    records = query_db("""
        SELECT emotion, score, created_at 
        FROM emotion_records 
        WHERE user_id = %s AND created_at >= %s
        ORDER BY created_at ASC
    """, (user_id, start_date))

    if not records:
        return jsonify({
            "success": True,
            "report": {
                "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                "total_records": 0,
                "message": "本周暂无情绪记录"
            }
        })

    # 数据分析
    import statistics

    scores = [r['score'] for r in records]
    emotions = [r['emotion'] for r in records]

    avg_score = sum(scores) / len(scores)
    volatility = statistics.stdev(scores) if len(scores) > 1 else 0

    # 情绪分布
    emotion_counts = {}
    for e in emotions:
        emotion_counts[e] = emotion_counts.get(e, 0) + 1

    dominant_emotion = max(emotion_counts, key=emotion_counts.get)

    # 趋势分析
    trend = "平稳"
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (len(scores) - mid)
        if second_half - first_half > 0.5:
            trend = "上升趋势"
        elif first_half - second_half > 0.5:
            trend = "下降趋势"

    # 生成建议
    insights = []
    if avg_score >= 7:
        insights.append("本周情绪整体良好，继续保持积极心态！")
    elif avg_score >= 5:
        insights.append("本周情绪一般，建议适当放松和调节。")
    else:
        insights.append("本周情绪偏低，建议多与朋友交流或寻求专业帮助。")

    if volatility > 2:
        insights.append("情绪波动较大，建议记录触发因素以更好地了解自己。")

    if emotion_counts.get('焦虑', 0) > len(emotions) * 0.3:
        insights.append("焦虑情绪出现较频繁，可以尝试深呼吸或冥想放松。")

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


# ==================== 知识库API ====================

@app.route('/api/knowledge', methods=['GET'])
def search_knowledge():
    """
    GET /api/knowledge - 搜索心理知识

    参数: keyword, category
    """
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')

    query = "SELECT * FROM knowledge_base WHERE 1=1"
    params = []

    if keyword:
        query += " AND (title LIKE %s OR content LIKE %s OR tags LIKE %s)"
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

    if category:
        query += " AND category = %s"
        params.append(category)

    query += " ORDER BY created_at DESC LIMIT 20"

    results = query_db(query, tuple(params))

    for r in results:
        r['created_at'] = r['created_at'].isoformat() if r['created_at'] else None
        r['updated_at'] = r['updated_at'].isoformat() if r['updated_at'] else None

    return jsonify({"success": True, "data": results, "count": len(results)})


# ==================== 资源推荐API ====================

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """
    GET /api/resources - 获取资源推荐

    参数: type, emotion
    """
    res_type = request.args.get('type')
    emotion = request.args.get('emotion')

    query = "SELECT * FROM resources WHERE 1=1"
    params = []

    if res_type:
        query += " AND type = %s"
        params.append(res_type)

    if emotion:
        query += " AND applicable_emotions LIKE %s"
        params.append(f'%{emotion}%')

    query += " ORDER BY created_at DESC"

    results = query_db(query, tuple(params))

    for r in results:
        r['created_at'] = r['created_at'].isoformat() if r['created_at'] else None

    return jsonify({"success": True, "data": results, "count": len(results)})


# ==================== 风险预警API ====================

@app.route('/api/risk/alerts', methods=['GET'])
def get_risk_alerts():
    """
    GET /api/risk/alerts - 获取风险预警列表

    参数: user_id (可选), handled (0/1)
    """
    user_id = request.args.get('user_id', type=int)
    handled = request.args.get('handled')

    query = "SELECT * FROM risk_alerts WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)

    if handled is not None:
        query += " AND handled = %s"
        params.append(int(handled))

    query += " ORDER BY created_at DESC LIMIT 50"

    alerts = query_db(query, tuple(params))

    for a in alerts:
        a['created_at'] = a['created_at'].isoformat() if a['created_at'] else None

    return jsonify({"success": True, "data": alerts})


@app.route('/api/risk/alerts/<int:alert_id>', methods=['PUT'])
def handle_risk_alert(alert_id):
    """
    PUT /api/risk/alerts/<id> - 处理风险预警
    """
    data = request.get_json()
    handled = data.get('handled', 1)

    execute_db("UPDATE risk_alerts SET handled = %s WHERE id = %s", (handled, alert_id))

    return jsonify({"success": True, "message": "预警已处理"})


# ==================== 启动应用 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("情绪愈疗平台API服务启动中...")
    print("访问地址: http://localhost:5000")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)
