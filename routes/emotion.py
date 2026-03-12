"""
情绪记录路由
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import EmotionRecord, User, db
from datetime import datetime, timedelta
import statistics

emotion_bp = Blueprint('emotion', __name__)

@emotion_bp.route('', methods=['POST'])
def record_emotion():
    """记录情绪数据"""
    try:
        # 尝试获取JWT，如果不存在则使用user_id参数
        try:
            current_user_id = get_jwt_identity()
        except:
            data = request.get_json() or {}
            current_user_id = data.get('user_id', 1)
        data = request.get_json()
        
        # 验证必填字段
        emotion = data.get('emotion', '').strip()
        score = data.get('score')
        
        if not emotion:
            return jsonify({"success": False, "message": "情绪类型不能为空"}), 400
        
        if score is None:
            return jsonify({"success": False, "message": "情绪分数不能为空"}), 400
        
        # 验证分数范围
        if not (0 <= score <= 10):
            return jsonify({"success": False, "message": "情绪分数必须在0-10之间"}), 400
        
        # 创建情绪记录
        emotion_record = EmotionRecord(
            user_id=current_user_id,
            emotion=emotion,
            score=score,
            text=data.get('text', '')
        )
        
        db.session.add(emotion_record)
        db.session.commit()
        
        # 检测是否需要风险预警
        if score <= 3:  # 低分预警
            create_low_emotion_alert(current_user_id, emotion_record)
        
        return jsonify({
            "success": True,
            "message": "情绪记录保存成功",
            "record": emotion_record.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@emotion_bp.route('/history', methods=['GET'])
def get_emotion_history():
    """获取情绪历史记录"""
    try:
        # 尝试获取JWT，如果不存在则使用user_id参数
        try:
            current_user_id = get_jwt_identity()
        except:
            current_user_id = request.args.get('user_id', 1)
            if isinstance(current_user_id, str) and current_user_id.isdigit():
                current_user_id = int(current_user_id)
        
        # 获取查询参数
        days = int(request.args.get('days', 7))
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 计算开始日期
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 查询记录
        query = EmotionRecord.query.filter_by(user_id=current_user_id) \
            .filter(EmotionRecord.created_at >= start_date) \
            .order_by(EmotionRecord.created_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            "success": True,
            "records": [record.to_dict() for record in pagination.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "days": days
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@emotion_bp.route('/stats', methods=['GET'])
def get_emotion_stats():
    """获取情绪统计数据"""
    try:
        # 尝试获取JWT，如果不存在则使用user_id参数
        try:
            current_user_id = get_jwt_identity()
        except:
            current_user_id = request.args.get('user_id', 1)
            if isinstance(current_user_id, str) and current_user_id.isdigit():
                current_user_id = int(current_user_id)
        
        # 获取查询参数
        days = int(request.args.get('days', 7))
        
        # 计算开始日期
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 查询记录
        records = EmotionRecord.query.filter_by(user_id=current_user_id)\
            .filter(EmotionRecord.created_at >= start_date)\
            .order_by(EmotionRecord.created_at.asc())\
            .all()
        
        if not records:
            return jsonify({
                "success": True,
                "data": {
                    "total_records": 0,
                    "message": f"过去{days}天没有情绪记录"
                }
            })
        
        # 计算统计数据
        scores = [record.score for record in records]
        emotions = [record.emotion for record in records]
        
        # 基础统计
        total_records = len(records)
        avg_score = sum(scores) / total_records
        
        # 情绪分布
        emotion_distribution = {}
        for emotion in emotions:
            emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1
        
        # 主要情绪
        dominant_emotion = max(emotion_distribution, key=emotion_distribution.get)
        
        # 情绪波动性
        volatility = statistics.stdev(scores) if len(scores) > 1 else 0
        
        # 每日趋势
        daily_data = {}
        for record in records:
            date_str = record.created_at.strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {'scores': [], 'emotions': []}
            daily_data[date_str]['scores'].append(record.score)
            daily_data[date_str]['emotions'].append(record.emotion)
        
        # 格式化每日数据
        formatted_daily_data = []
        for date_str, data in sorted(daily_data.items()):
            daily_avg = sum(data['scores']) / len(data['scores'])
            dominant = max(set(data['emotions']), key=data['emotions'].count)
            
            formatted_daily_data.append({
                'date': date_str,
                'avg_score': round(daily_avg, 2),
                'record_count': len(data['scores']),
                'dominant_emotion': dominant
            })
        
        # 趋势分析
        trend = "平稳"
        if len(scores) >= 4:
            mid = len(scores) // 2
            first_half_avg = sum(scores[:mid]) / mid
            second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
            
            if second_half_avg - first_half_avg > 0.5:
                trend = "上升趋势"
            elif first_half_avg - second_half_avg > 0.5:
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
                "daily_data": formatted_daily_data,
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
@jwt_required()
def get_weekly_report():
    """获取周报数据"""
    try:
        current_user_id = get_jwt_identity()
        
        # 计算周报时间范围（过去7天）
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=6)  # 包含今天在内7天
        
        # 查询记录
        records = EmotionRecord.query.filter_by(user_id=current_user_id)\
            .filter(EmotionRecord.created_at >= start_date)\
            .order_by(EmotionRecord.created_at.asc())\
            .all()
        
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
        scores = [record.score for record in records]
        emotions = [record.emotion for record in records]
        
        # 基础统计
        total_records = len(records)
        avg_score = sum(scores) / total_records
        
        # 情绪分布
        emotion_distribution = {}
        for emotion in emotions:
            emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1
        
        # 主要情绪
        dominant_emotion = max(emotion_distribution, key=emotion_distribution.get)
        
        # 波动性
        volatility = statistics.stdev(scores) if len(scores) > 1 else 0
        
        # 趋势分析
        trend = "平稳"
        if len(scores) >= 4:
            mid = len(scores) // 2
            first_half_avg = sum(scores[:mid]) / mid
            second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
            
            if second_half_avg - first_half_avg > 0.5:
                trend = "上升趋势"
            elif first_half_avg - second_half_avg > 0.5:
                trend = "下降趋势"
        
        # 生成洞察建议
        insights = generate_insights(avg_score, volatility, emotion_distribution, total_records)
        
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

def generate_insights(avg_score, volatility, emotion_distribution, total_records):
    """生成洞察建议"""
    insights = []
    
    # 基于平均分的建议
    if avg_score >= 8:
        insights.append("本周情绪状态非常棒！继续保持积极心态，您的情绪管理能力很强。")
    elif avg_score >= 6:
        insights.append("本周情绪状态良好，整体保持稳定。可以尝试更多积极的活动来提升幸福感。")
    elif avg_score >= 4:
        insights.append("本周情绪有些波动，建议多关注自我照顾和放松。")
    else:
        insights.append("本周情绪偏低，建议寻求专业支持或与亲友多交流。")
    
    # 基于波动性的建议
    if volatility > 2:
        insights.append("情绪波动较大，建议记录情绪触发因素，有助于更好地了解自己。")
    elif volatility < 1:
        insights.append("情绪保持稳定，这表明您有很好的情绪调节能力。")
    
    # 基于情绪类型的建议
    if '焦虑' in emotion_distribution and emotion_distribution['焦虑'] > total_records * 0.3:
        insights.append("焦虑情绪出现较频繁，可以尝试深呼吸或冥想练习来缓解。")
    
    if '悲伤' in emotion_distribution and emotion_distribution['悲伤'] > total_records * 0.3:
        insights.append("悲伤情绪较多，建议多参与能带来快乐的活动，或与信任的人分享感受。")
    
    # 基于记录频率的建议
    if total_records < 3:
        insights.append("记录频率较低，建议每天记录1-2次情绪，有助于更好地了解情绪变化。")
    
    return " ".join(insights)

def create_low_emotion_alert(user_id, emotion_record):
    """创建低情绪预警"""
    from models import RiskAlert
    
    # 检查是否已有相似预警
    existing_alert = RiskAlert.query.filter_by(
        user_id=user_id,
        handled=False,
        risk_type='low_emotion'
    ).first()
    
    if not existing_alert:
        risk_alert = RiskAlert(
            user_id=user_id,
            risk_level='medium',
            risk_type='low_emotion',
            content=f"情绪分数较低：{emotion_record.score}，情绪类型：{emotion_record.emotion}"
        )
        
        db.session.add(risk_alert)
        # 注意：这里不立即提交，由调用方统一提交