"""
情绪识别模块 + 健康报告模块
后端工程师B - 任务1、2

功能：
1. 情绪识别API：文本情绪分析/实时情绪状态/情绪数据存储
2. 健康报告API：周报月报生成/情绪趋势分析/改善建议
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from datetime import datetime, timedelta
import statistics
import os
import json
import requests

emotion_bp = Blueprint('emotion_b', __name__)

# ==================== 情绪识别部分 ====================

# 百炼平台API配置
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# 情绪关键词映射
EMOTION_KEYWORDS = {
    '开心': ['开心', '快乐', '高兴', '幸福', '棒', '太好了', '喜悦', '欢乐', '愉快'],
    '悲伤': ['难过', '伤心', '悲伤', '忧郁', '哭', '痛苦', '沮丧', '失落', '郁闷'],
    '焦虑': ['紧张', '担心', '焦虑', '害怕', '不安', '恐慌', '压力', '烦恼'],
    '愤怒': ['生气', '愤怒', '恼火', '气愤', '发火', '暴躁', '不满', '厌烦'],
    '平静': ['平静', '安宁', '放松', '舒服', '还好', '宁静', '和谐', '轻松'],
    '恐惧': ['恐惧', '害怕', '恐慌', '畏惧']
}

# 情绪建议映射
EMOTION_ADVICE = {
    '开心': '继续保持好心情！可以记录下今天开心的事情。',
    '悲伤': '建议听听舒缓的音乐、和朋友聊聊天，或者做一些让自己开心的事。',
    '焦虑': '尝试深呼吸、冥想，或者写下你的担忧并逐一解决。',
    '愤怒': '深呼吸让自己冷静下来，暂时离开让你生气的场景。',
    '恐惧': '确认自己的安全，慢慢放松，必要时寻求帮助。',
    '平静': '保持良好的生活节奏，可以尝试学习新技能。'
}

# 情绪类别映射
EMOTION_CATEGORIES = {
    'joy': '开心', 'sadness': '悲伤', 'anxiety': '焦虑',
    'anger': '愤怒', 'fear': '恐惧', 'neutral': '平静'
}


def analyze_with_ai(text):
    """使用百炼平台进行AI情绪分析"""
    if not DASHSCOPE_API_KEY:
        return None
    
    prompt = f"""请分析以下文本的情绪，只返回JSON格式的结果。
情绪类别：joy(开心), sadness(悲伤), anxiety(焦虑), anger(愤怒), fear(恐惧), neutral(平静)
情绪强度（1-10）：1=非常微弱，10=非常强烈

文本：{text}

请按以下JSON格式返回：
{{"emotion": "情绪类别", "intensity": 强度数值, "reasoning": "分析理由"}}

只返回JSON，不要其他内容。"""

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
        }
        
        data = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {"role": "system", "content": "你是一个情绪分析专家，请用JSON格式返回结果。"},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "temperature": 0.3,
                "max_tokens": 500,
                "result_format": "message"
            }
        }
        
        response = requests.post(DASHSCOPE_API_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'output' in result and 'text' in result['output']:
                import re
                content = result['output']['text']
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        
        return None
    except Exception as e:
        print(f"AI分析失败: {e}")
        return None


# ==================== 情绪识别API ====================

@emotion_bp.route('/analyze', methods=['POST'])
def analyze_emotion():
    """
    POST /api/b-emotion/analyze - 文本情绪分析
    请求: {"text": "用户文本", "user_id": 1}
    返回: 情绪类型、置信度、建议
    """
    try:
        data = request.get_json() or {}
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"success": False, "message": "请输入文本"}), 400
        
        user_id = data.get('user_id')
        use_ai = data.get('use_ai', False)
        
        # 优先使用AI分析
        ai_result = None
        if use_ai and DASHSCOPE_API_KEY:
            try:
                ai_result = analyze_with_ai(text)
            except:
                pass
        
        if ai_result and ai_result.get('emotion'):
            detected_emotion = ai_result['emotion']
            intensity = ai_result.get('intensity', 5)
            confidence = 0.95
            reasoning = ai_result.get('reasoning', '')
        else:
            # 降级到关键词分析
            detected_emotion = 'neutral'
            max_match = 0
            
            keyword_map = {
                '开心': 'joy', '快乐': 'joy', '高兴': 'joy',
                '悲伤': 'sadness', '难过': 'sadness', '伤心': 'sadness',
                '焦虑': 'anxiety', '紧张': 'anxiety', '担心': 'anxiety',
                '愤怒': 'anger', '生气': 'anger',
                '恐惧': 'fear', '害怕': 'fear'
            }
            
            for emotion, keywords in EMOTION_KEYWORDS.items():
                match_count = sum(1 for kw in keywords if kw in text)
                if match_count > max_match:
                    max_match = match_count
                    detected_emotion = keyword_map.get(emotion, 'neutral')
            
            intensity = min(10, max_match * 2 + 3) if max_match > 0 else 5
            confidence = min(0.95, 0.5 + max_match * 0.15) if max_match > 0 else 0.5
            reasoning = '基于文本内容分析'
        
        emotion_cn = EMOTION_CATEGORIES.get(detected_emotion, '平静')
        advice = EMOTION_ADVICE.get(emotion_cn, '保持良好心态')
        
        result = {
            "text": text[:100],
            "emotion": detected_emotion,
            "emotion_cn": emotion_cn,
            "intensity": intensity,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "advice": advice,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return jsonify({"success": True, "data": result})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@emotion_bp.route('/record', methods=['POST'])
def record_emotion():
    """
    POST /api/b-emotion/record - 记录情绪数据
    请求: {"user_id": 1, "emotion": "开心", "score": 8.5, "text": "备注"}
    """
    try:
        data = request.get_json() or {}
        
        user_id = data.get('user_id', 1)
        emotion = data.get('emotion', '').strip()
        score = data.get('score')
        
        if not emotion:
            return jsonify({"success": False, "message": "情绪类型不能为空"}), 400
        
        if score is None:
            return jsonify({"success": False, "message": "情绪分数不能为空"}), 400
        
        if not (0 <= score <= 10):
            return jsonify({"success": False, "message": "分数必须在0-10之间"}), 400
        
        # 导入模型（避免循环导入）
        from models import EmotionRecord
        
        emotion_record = EmotionRecord(
            user_id=user_id,
            emotion=emotion,
            score=score,
            text=data.get('text', '')
        )
        
        db.session.add(emotion_record)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "情绪记录保存成功",
            "data": {
                "id": emotion_record.id,
                "emotion": emotion,
                "score": score,
                "created_at": emotion_record.created_at.isoformat() if emotion_record.created_at else None
            }
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@emotion_bp.route('/history', methods=['GET'])
def get_emotion_history():
    """
    GET /api/b-emotion/history - 获取情绪历史
    参数: user_id, days(默认7), page, per_page
    """
    try:
        user_id = request.args.get('user_id', 1, type=int)
        days = int(request.args.get('days', 7))
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        from models import EmotionRecord
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = EmotionRecord.query.filter_by(user_id=user_id) \
            .filter(EmotionRecord.created_at >= start_date) \
            .order_by(EmotionRecord.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "success": True,
            "data": {
                "records": [r.to_dict() for r in pagination.items],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total,
                    "pages": pagination.pages
                }
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== 健康报告API ====================

@emotion_bp.route('/stats', methods=['GET'])
def get_emotion_stats():
    """
    GET /api/b-emotion/stats - 获取情绪统计数据
    参数: user_id, days
    """
    try:
        user_id = request.args.get('user_id', 1, type=int)
        days = int(request.args.get('days', 7))
        
        from models import EmotionRecord
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        records = EmotionRecord.query.filter_by(user_id=user_id)\
            .filter(EmotionRecord.created_at >= start_date)\
            .order_by(EmotionRecord.created_at.asc()).all()
        
        if not records:
            return jsonify({
                "success": True,
                "data": {
                    "total_records": 0,
                    "message": f"过去{days}天没有情绪记录"
                }
            })
        
        scores = [r.score for r in records]
        emotions = [r.emotion for r in records]
        
        total_records = len(records)
        avg_score = sum(scores) / total_records
        
        # 情绪分布
        emotion_distribution = {}
        for e in emotions:
            emotion_distribution[e] = emotion_distribution.get(e, 0) + 1
        
        dominant_emotion = max(emotion_distribution, key=emotion_distribution.get)
        volatility = statistics.stdev(scores) if len(scores) > 1 else 0
        
        # 每日趋势
        daily_data = {}
        for r in records:
            date_str = r.created_at.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {'scores': [], 'emotions': []}
            daily_data[date_str]['scores'].append(r.score)
            daily_data[date_str]['emotions'].append(r.emotion)
        
        formatted_daily = []
        for date_str, data in sorted(daily_data.items()):
            daily_avg = sum(data['scores']) / len(data['scores'])
            dominant = max(set(data['emotions']), key=data['emotions'].count)
            formatted_daily.append({
                'date': date_str,
                'avg_score': round(daily_avg, 2),
                'record_count': len(data['scores']),
                'dominant_emotion': dominant
            })
        
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
        
        return jsonify({
            "success": True,
            "data": {
                "total_records": total_records,
                "avg_score": round(avg_score, 2),
                "dominant_emotion": dominant_emotion,
                "emotion_distribution": emotion_distribution,
                "volatility": round(volatility, 2),
                "trend": trend,
                "daily_data": formatted_daily,
                "period": {
                    "days": days,
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": datetime.utcnow().strftime('%Y-%m-%d')
                }
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@emotion_bp.route('/weekly-report', methods=['GET'])
def get_weekly_report():
    """
    GET /api/b-emotion/weekly-report - 获取周报
    参数: user_id
    """
    try:
        user_id = request.args.get('user_id', 1, type=int)
        
        from models import EmotionRecord
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=6)
        
        records = EmotionRecord.query.filter_by(user_id=user_id)\
            .filter(EmotionRecord.created_at >= start_date)\
            .order_by(EmotionRecord.created_at.asc()).all()
        
        if not records:
            return jsonify({
                "success": True,
                "report": {
                    "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                    "total_records": 0,
                    "message": "本周暂无情绪记录"
                }
            })
        
        scores = [r.score for r in records]
        emotions = [r.emotion for r in records]
        
        total_records = len(records)
        avg_score = sum(scores) / total_records
        
        # 情绪分布
        emotion_distribution = {}
        for e in emotions:
            emotion_distribution[e] = emotion_distribution.get(e, 0) + 1
        
        dominant_emotion = max(emotion_distribution, key=emotion_distribution.get)
        volatility = statistics.stdev(scores) if len(scores) > 1 else 0
        
        # 趋势
        trend = "平稳"
        if len(scores) >= 4:
            mid = len(scores) // 2
            first_half = sum(scores[:mid]) / mid
            second_half = sum(scores[mid:]) / (len(scores) - mid)
            
            if second_half - first_half > 0.5:
                trend = "上升趋势"
            elif first_half - second_half > 0.5:
                trend = "下降趋势"
        
        # 生成洞察建议
        insights = _generate_insights(avg_score, volatility, emotion_distribution, total_records)
        
        return jsonify({
            "success": True,
            "report": {
                "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                "total_records": total_records,
                "avg_score": round(avg_score, 2),
                "dominant_emotion": dominant_emotion,
                "emotion_distribution": emotion_distribution,
                "trend": trend,
                "volatility": round(volatility, 2),
                "insights": insights
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def _generate_insights(avg_score, volatility, emotion_distribution, total_records):
    """生成洞察建议"""
    insights = []
    
    if avg_score >= 8:
        insights.append("本周情绪状态非常棒！继续保持积极心态。")
    elif avg_score >= 6:
        insights.append("本周情绪状态良好，整体保持稳定。")
    elif avg_score >= 4:
        insights.append("本周情绪有些波动，建议多关注自我照顾。")
    else:
        insights.append("本周情绪偏低，建议寻求专业支持或与亲友交流。")
    
    if volatility > 2:
        insights.append("情绪波动较大，建议记录情绪触发因素。")
    elif volatility < 1:
        insights.append("情绪保持稳定，表明您有很好的情绪调节能力。")
    
    if '焦虑' in emotion_distribution and emotion_distribution['焦虑'] > total_records * 0.3:
        insights.append("焦虑情绪出现较频繁，可以尝试深呼吸或冥想练习。")
    
    if '悲伤' in emotion_distribution and emotion_distribution['悲伤'] > total_records * 0.3:
        insights.append("悲伤情绪较多，建议多参与能带来快乐的活动。")
    
    if total_records < 3:
        insights.append("记录频率较低，建议每天记录1-2次情绪。")
    
    return " ".join(insights)


# 注册路由示例（在app.py中）
"""
from my_emotion_api import emotion_bp
app.register_blueprint(emotion_bp, url_prefix='/api/b-emotion')
"""
