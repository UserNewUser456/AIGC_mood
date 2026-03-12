# 兼容性路由 - 适配前端API调用
# 前端期望的端点：/api/chat, /api/risk/assess
# Flask蓝图提供的端点：/api/conversations/send, /api/risk/check

from flask import Blueprint, request, jsonify
from extensions import db

# 创建兼容路由蓝图
compatibility_bp = Blueprint('compatibility', __name__)

@compatibility_bp.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_compatibility():
    """兼容前端的 /api/chat 端点"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # 转发到 conversation 蓝图的 send_message
        from routes.conversation import send_message
        return send_message()
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': None,
            'msg': f'聊天接口错误: {str(e)}'
        }), 500

@compatibility_bp.route('/api/risk/assess', methods=['POST', 'OPTIONS'])
def risk_assess_compatibility():
    """兼容前端的 /api/risk/assess 端点"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # 转发到 risk 蓝图的 check_risk
        from routes.risk import check_risk
        return check_risk()
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {'level': 'low', 'score': 0, 'message': '风险评估失败'},
            'msg': f'风险评估接口错误: {str(e)}'
        }), 500

@compatibility_bp.route('/api/emotion/analyze', methods=['POST', 'OPTIONS'])
def emotion_analyze_compatibility():
    """兼容前端的 /api/emotion/analyze 端点"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # 转发到 emotion 蓝图的 analyze
        from routes.emotion import analyze_emotion
        return analyze_emotion()
    except Exception as e:
        return jsonify({
            'code': 500,
            'data': {'label': '中性', 'emoji': '😐'},
            'msg': f'情绪分析接口错误: {str(e)}'
        }), 500
