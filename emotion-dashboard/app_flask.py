"""
情绪分析仪表盘 - Flask后端服务
独立Web应用API服务

功能：
- 情绪数据接收和存储
- 历史情绪数据查询
- 周报数据生成
- 支持iframe消息监听和数据接收
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# ==================== 应用配置 ====================
app = Flask(__name__, 
            template_folder='templates',  # HTML模板目录
            static_folder='static')       # 静态资源目录

# 启用CORS，允许跨域请求
CORS(app)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'emotion.db')

# ==================== 数据库操作 ====================

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使用RowFactory便于通过列名访问
    return conn

def init_db():
    """
    初始化数据库和表
    创建emotion_records表用于存储情绪记录
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 创建情绪记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                emotion TEXT NOT NULL,
                score REAL NOT NULL,
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 创建索引加速查询
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON emotion_records(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON emotion_records(created_at)')
        conn.commit()
        print(f"数据库初始化成功: {DB_PATH}")
    finally:
        conn.close()

# ==================== API接口 ====================

@app.route('/')
def index():
    """主页 - 返回仪表盘页面"""
    return render_template('dashboard.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    return send_from_directory(app.static_folder, filename)

# ==================== 情绪数据API ====================

@app.route('/api/emotion', methods=['POST'])
def receive_emotion():
    """
    POST /api/emotion - 接收情绪数据上报
    
    请求体格式:
    {
        "user_id": "用户ID",
        "emotion": "情绪类型",
        "score": 8.5,
        "text": "备注文字"
    }
    
    返回:
    {
        "success": true,
        "message": "情绪记录已保存",
        "id": 1
    }
    """
    try:
        data = request.get_json()
        
        # 参数验证
        if not data:
            return jsonify({"success": False, "message": "请求体不能为空"}), 400
        
        user_id = data.get('user_id')
        emotion = data.get('emotion')
        score = data.get('score')
        text = data.get('text', '')
        
        # 必填字段检查
        if not user_id:
            return jsonify({"success": False, "message": "user_id不能为空"}), 400
        if not emotion:
            return jsonify({"success": False, "message": "emotion不能为空"}), 400
        if score is None:
            return jsonify({"success": False, "message": "score不能为空"}), 400
        
        # 分数范围验证
        if not isinstance(score, (int, float)) or score < 0 or score > 10:
            return jsonify({"success": False, "message": "score必须在0-10之间"}), 400
        
        # 保存到数据库
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO emotion_records (user_id, emotion, score, text) VALUES (?, ?, ?, ?)',
                (user_id, emotion, score, text)
            )
            conn.commit()
            record_id = cursor.lastrowid
        finally:
            conn.close()
        
        return jsonify({
            "success": True,
            "message": "情绪记录已保存",
            "id": record_id,
            "data": {
                "user_id": user_id,
                "emotion": emotion,
                "score": score,
                "text": text
            }
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

@app.route('/api/emotion/history', methods=['GET'])
def get_emotion_history():
    """
    GET /api/emotion/history - 获取历史情绪数据
    
    查询参数:
    - user_id: 用户ID (必填)
    - days: 查询天数，默认7天
    
    返回:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "user_id": "user_xxx",
                "emotion": "开心",
                "score": 8.5,
                "text": "备注",
                "created_at": "2024-01-01 10:00:00"
            }
        ]
    }
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id')
        days = int(request.args.get('days', 7))
        
        # 参数验证
        if not user_id:
            return jsonify({"success": False, "message": "user_id不能为空"}), 400
        
        # 计算开始日期
        start_date = datetime.now() - timedelta(days=days)
        
        # 查询数据库
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, emotion, score, text, created_at 
                FROM emotion_records 
                WHERE user_id = ? AND created_at >= ?
                ORDER BY created_at ASC
            ''', (user_id, start_date))
            
            rows = cursor.fetchall()
            
            # 转换为字典列表
            data = []
            for row in rows:
                data.append({
                    "id": row['id'],
                    "user_id": row['user_id'],
                    "emotion": row['emotion'],
                    "score": row['score'],
                    "text": row['text'] if row['text'] else '',
                    "created_at": row['created_at']
                })
        finally:
            conn.close()
        
        return jsonify({
            "success": True,
            "data": data,
            "count": len(data),
            "days": days,
            "user_id": user_id
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

@app.route('/api/report/weekly', methods=['GET'])
def get_weekly_report():
    """
    GET /api/report/weekly - 生成周报数据
    
    查询参数:
    - user_id: 用户ID (必填)
    
    返回:
    {
        "success": true,
        "report": {
            "period": "2024-01-01 至 2024-01-07",
            "total_records": 21,
            "avg_score": 7.2,
            "dominant_emotion": "开心",
            "emotion_distribution": {
                "开心": 8,
                "平静": 5,
                "焦虑": 3
            },
            "trend": "上升趋势",
            "volatility": 1.5,
            "insights": "本周情绪整体良好..."
        }
    }
    """
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"success": False, "message": "user_id不能为空"}), 400
        
        # 计算周报时间范围（过去7天）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)  # 包含今天在内7天
        
        # 查询数据
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT emotion, score, created_at 
                FROM emotion_records 
                WHERE user_id = ? AND created_at >= ?
                ORDER BY created_at ASC
            ''', (user_id, start_date))
            
            rows = cursor.fetchall()
        finally:
            conn.close()
        
        # 数据分析
        if not rows:
            return jsonify({
                "success": True,
                "report": {
                    "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                    "total_records": 0,
                    "message": "本周暂无情绪记录"
                }
            })
        
        # 转换为列表便于分析
        records = [{'emotion': row['emotion'], 'score': row['score'], 'created_at': row['created_at']} for row in rows]
        
        # 计算统计数据
        scores = [r['score'] for r in records]
        emotions = [r['emotion'] for r in records]
        
        # 平均分
        avg_score = sum(scores) / len(scores)
        
        # 情绪分布统计
        emotion_counts = {}
        for e in emotions:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1
        
        # 主要情绪
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        
        # 情绪波动性（标准差）
        import statistics
        volatility = statistics.stdev(scores) if len(scores) > 1 else 0
        
        # 趋势分析（比较本周与上周）
        trend = "平稳"
        if len(scores) >= 3:
            first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            if second_half - first_half > 0.5:
                trend = "上升趋势"
            elif first_half - second_half > 0.5:
                trend = "下降趋势"
        
        # 生成洞察建议
        insights = []
        if avg_score >= 7:
            insights.append("本周情绪整体良好，保持积极心态！")
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
        
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500

# ==================== 便捷测试API ====================

@app.route('/api/demo/generate', methods=['POST'])
def generate_demo_data():
    """
    POST /api/demo/generate - 生成演示数据
    
    用于快速生成测试数据以便查看仪表盘效果
    """
    import random
    
    user_id = request.args.get('user_id', 'demo_user')
    
    emotions = [
        ('开心', 8.5), ('平静', 7.0), ('焦虑', 4.5), ('悲伤', 3.5),
        ('愤怒', 3.0), ('兴奋', 8.0), ('沮丧', 4.0), ('放松', 7.5)
    ]
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 生成过去7天的随机数据
        for day in range(7):
            # 每天生成2-4条记录
            for _ in range(random.randint(2, 4)):
                emotion, base_score = random.choice(emotions)
                # 添加随机波动
                score = min(10, max(0, base_score + random.uniform(-1, 1)))
                
                # 随机时间
                hours_ago = random.randint(0, day * 24)
                created_at = datetime.now() - timedelta(hours=hours_ago)
                
                cursor.execute(
                    'INSERT INTO emotion_records (user_id, emotion, score, text, created_at) VALUES (?, ?, ?, ?, ?)',
                    (user_id, emotion, round(score, 1), f'自动生成的演示数据', created_at)
                )
        
        conn.commit()
        count = cursor.lastrowid
    finally:
        conn.close()
    
    return jsonify({
        "success": True,
        "message": f"已为用户 {user_id} 生成演示数据",
        "records_count": 7 * 4  # 约14-28条
    })

# ==================== 启动应用 ====================

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 启动Flask开发服务器
    # host='0.0.0.0' 允许外部访问
    # port=5000       默认端口
    # debug=True      调试模式
    print("=" * 50)
    print("情绪分析仪表盘服务启动中...")
    print("访问地址: http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
